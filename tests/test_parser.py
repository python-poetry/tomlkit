import pytest

from tomlkit.exceptions import EmptyTableNameError
from tomlkit.exceptions import InternalParserError
from tomlkit.exceptions import InvalidUnicodeValueError
from tomlkit.exceptions import ParseError
from tomlkit.exceptions import UnexpectedCharError
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
