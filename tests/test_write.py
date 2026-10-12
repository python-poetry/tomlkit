import sys

from typing import Any

import pytest

from tomlkit import dumps
from tomlkit import loads
from tomlkit import string


def test_write_backslash() -> None:
    d = {"foo": "\\e\u25e6\r"}

    expected = """foo = "\\\\e\u25e6\\r"
"""

    assert expected == dumps(d)
    result: Any = loads(dumps(d))["foo"]
    assert result == "\\e\u25e6\r"


def test_write_escape_char_as_unicode_escape() -> None:
    # ``\e`` is TOML 1.1 only, so ESC must be written as ``\u001b``.
    d = {"a\x1bk": "a\x1bb", "m": string("x\x1by\n", multiline=True)}
    expected = '"a\\u001bk" = "a\\u001bb"\nm = """x\\u001by\n"""\n'

    assert expected == dumps(d)
    assert loads(dumps(d)) == d


@pytest.mark.skipif(sys.version_info < (3, 11), reason="tomllib requires 3.11+")
def test_write_escape_char_readable_by_tomllib() -> None:
    import tomllib

    d = {"a\x1bk": "a\x1bb", "m": string("x\x1by\n", multiline=True)}

    assert tomllib.loads(dumps(d)) == d


def test_parse_escape_char_shorthand() -> None:
    doc = loads('a = "\\e"\nb = """\\e"""\n')

    assert doc["a"] == "\x1b"
    assert doc["b"] == "\x1b"


def test_escape_special_characters_in_key() -> None:
    d = {"foo\nbar": "baz"}
    expected = '"foo\\nbar" = "baz"\n'
    assert expected == dumps(d)
    result: Any = loads(dumps(d))["foo\nbar"]
    assert result == "baz"


def test_write_inline_table_in_nested_arrays() -> None:
    d = {"foo": [[{"a": 1}]]}
    expected = "foo = [[{a = 1}]]\n"
    assert expected == dumps(d)
    result: Any = loads(dumps(d))["foo"]
    assert result == [[{"a": 1}]]


def test_serialize_aot_with_nested_tables() -> None:
    doc = {"a": [{"b": {"c": 1}}]}
    expected = """\
[[a]]
[a.b]
c = 1
"""
    assert dumps(doc) == expected
    assert loads(expected) == doc
