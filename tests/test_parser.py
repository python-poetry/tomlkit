import sys

import pytest

from tomlkit.exceptions import EmptyTableNameError
from tomlkit.exceptions import InternalParserError
from tomlkit.exceptions import InvalidNumberError
from tomlkit.exceptions import InvalidUnicodeValueError
from tomlkit.exceptions import ParseError
from tomlkit.exceptions import UnexpectedCharError
from tomlkit.items import Integer
from tomlkit.items import StringType
from tomlkit.parser import Parser


def test_parser_should_raise_an_internal_error_if_parsing_wrong_type_of_string() -> (
    None
):
    parser = Parser('"foo"')

    with pytest.raises(InternalParserError) as e:
        parser._parse_string(StringType.SLL)

    assert e.value.line == 1
    assert e.value.col == 0


def test_parser_should_raise_an_error_for_empty_tables() -> None:
    content = """
[one]
[]
"""

    parser = Parser(content)

    with pytest.raises(EmptyTableNameError) as e:
        parser.parse()

    assert e.value.line == 3
    assert e.value.col == 1


def test_parser_should_raise_an_error_if_equal_not_found() -> None:
    content = """[foo]
a {c = 1, d = 2}
"""
    parser = Parser(content)
    with pytest.raises(UnexpectedCharError):
        parser.parse()


def test_array_close_after_value_round_trips() -> None:
    # The parser skips the value attempt when it is sitting on the closing
    # "]" (a value-less position: an empty or trailing-comma array). This is a
    # pure optimisation -- valid arrays going through that branch must still
    # round-trip byte-for-byte.
    for content in (
        "a = []",
        "a = [ ]",
        "a = [1]",
        "a = [1,]",
        "a = [1, 2]",
        "a = [1, 2, ]",
        "a = [\n  1,\n  2,\n]",
        "a = [[1], [2]]",
        "a = [{b = 1}]",
    ):
        assert Parser(content).parse().as_string() == content


def test_malformed_array_still_raises() -> None:
    # ...and malformed arrays must still raise: the skip applies only to "]",
    # never to a real value start (which must still be parsed) nor to "," (so a
    # leading/double comma keeps erroring).
    for content in ("a = [, 1]", "a = [1 2]", "a = [1, , 2]", "a = [@]"):
        with pytest.raises(UnexpectedCharError):
            Parser(content).parse()


def test_array_with_malformed_element_raises() -> None:
    # An element that starts to parse like a value but then hits an
    # unexpected char (e.g. an inline table missing its "=" or "}") must
    # surface the error instead of being swallowed and silently dropped,
    # which left the array truncated to whatever parsed before it.
    for content in (
        "a = [{1]",
        "a = [{a]",
        "a = [1, {2]",
        "a = [{a = 1}, {2]",
        "a = [[1, {x]]",
        "a = [{a.b]",
    ):
        with pytest.raises(UnexpectedCharError):
            Parser(content).parse()


def test_parse_multiline_string_ignore_the_first_newline() -> None:
    content = 'a = """\nfoo\n"""'
    parser = Parser(content)
    assert parser.parse() == {"a": "foo\n"}

    content = 'a = """\r\nfoo\n"""'
    parser = Parser(content)
    assert parser.parse() == {"a": "foo\n"}


def test_parse_multiline_basic_string_with_crlf() -> None:
    content = 'a = """foo\r\nbar"""'
    parser = Parser(content)
    assert parser.parse() == {"a": "foo\r\nbar"}


def test_parse_multiline_literal_string_with_crlf() -> None:
    content = "a = '''foo\r\nbar'''"
    parser = Parser(content)
    assert parser.parse() == {"a": "foo\r\nbar"}


def test_multiline_string_body_round_trips() -> None:
    # The multiline body is consumed by a bulk scan that stops at the
    # delimiter / escape / CR / invalid control char, leaving raw LF and tab
    # inside the run. Bodies spanning many lines must round-trip byte-for-byte,
    # incl. mixed LF/CRLF, tabs and a lone (non-closing) quote inside.
    for delim in ('"""', "'''"):
        for body in (
            "line1\nline2\nline3\n",
            "with\ttabs\tand\nnewlines\n",
            "crlf\r\nand\r\nlf\nmixed",
            f"a lone {delim[0]} quote inside",
            f"two {delim[0] * 2} quotes inside",
            "trailing spaces   \n   leading",
        ):
            content = f"a = {delim}{body}{delim}"
            assert Parser(content).parse().as_string() == content


def test_multiline_string_still_rejects_control_chars() -> None:
    # The bulk scan must stop at a bare CR and at other control chars so the
    # per-char branches still reject them (raw LF and tab stay allowed).
    for bad in ("\r", "\x00", "\x0c", "\x1f", "\x7f"):
        content = f'a = """ok{bad}bad"""'
        with pytest.raises(ParseError):
            Parser(content).parse()


@pytest.mark.parametrize(
    "content",
    [
        r'a = "\uD800"',
        r'a = "\uDFFF"',
        r'a = "\U0000D800"',
        r'a = "\U0000DFFF"',
        r'a = "\U0000DC00"',
    ],
)
def test_parser_rejects_surrogate_unicode_escapes(content: str) -> None:
    parser = Parser(content)
    with pytest.raises(InvalidUnicodeValueError):
        parser.parse()


@pytest.mark.parametrize(
    "content",
    [
        r'a = "\u12_3"',
        r'a = "\u 123"',
        r'a = "\u+123"',
        r'a = "\u1_23"',
        r'a = "\U0010_FFFF"',
        r'a = "\U0000_0041"',
    ],
)
def test_parser_rejects_non_hex_unicode_escapes(content: str) -> None:
    parser = Parser(content)
    with pytest.raises(InvalidUnicodeValueError):
        parser.parse()


@pytest.mark.parametrize(
    "content",
    [
        "a\tb = 1",
        "[a\tb]",
        "x.y\tz = 1",
    ],
)
def test_parser_rejects_tab_in_bare_key(content: str) -> None:
    parser = Parser(content)
    with pytest.raises(ParseError):
        parser.parse()


@pytest.mark.parametrize(
    "content",
    [
        "[a.b]\n[a]\n[a.b]",
        "[a.b]\nx = 1\n[a]\n[a.b]\ny = 2",
        "[a.b.c]\n[a]\n[a.b.c]",
        "[a.b]\n[a.c]\n[a]\n[a.b]",
    ],
)
def test_parser_rejects_table_redefined_after_parent(content: str) -> None:
    parser = Parser(content)
    with pytest.raises(ParseError):
        parser.parse()


@pytest.mark.parametrize(
    "content",
    [
        "[[a]b",
        "[[a]",
        "[[a]x\ny = 1",
        "[[a.b]x",
    ],
)
def test_parser_rejects_aot_header_missing_second_bracket(content: str) -> None:
    parser = Parser(content)
    with pytest.raises(ParseError):
        parser.parse()


@pytest.mark.skipif(
    not hasattr(sys, "get_int_max_str_digits"),
    reason="requires the int-from-string digit limit (3.9.14+/3.10.7+/3.11+)",
)
def test_parser_rejects_overlong_decimal_integer() -> None:
    # A decimal integer with more digits than Python's int-from-string limit
    # raises ValueError in int(); it must be reported as an invalid number, not
    # silently fall through to float() and become inf.
    parser = Parser("a = " + "9" * 4301)
    with pytest.raises(InvalidNumberError):
        parser.parse()

    # the value just under the limit is still a normal integer
    value = Parser("a = " + "9" * 4300).parse()["a"]
    assert isinstance(value, Integer)
