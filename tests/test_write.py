from typing import Any

from tomlkit import dumps
from tomlkit import loads


def test_write_backslash() -> None:
    d = {"foo": "\\e\u25e6\r"}

    expected = """foo = "\\\\e\u25e6\\r"
"""

    assert expected == dumps(d)
    result: Any = loads(dumps(d))["foo"]
    assert result == "\\e\u25e6\r"


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
