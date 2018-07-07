import pytest

from tomllib.exceptions import NonExistentKey
from tomllib.items import InlineTable
from tomllib.items import Integer
from tomllib.items import Key
from tomllib.items import String
from tomllib.items import StringType
from tomllib.items import Table
from tomllib.items import Trivia
from tomllib.parser import Parser


def test_items_can_be_appended_to_and_removed_from_a_table():
    string = """[table]
"""

    parser = Parser(string)
    _, table = parser._parse_table()

    assert isinstance(table, Table)
    assert "\n" == table.as_string()

    table.append(Key("foo"), String(StringType.SLB, "bar", "bar", Trivia(trail="\n")))

    assert '\nfoo = "bar"\n' == table.as_string()

    table.append(
        Key("baz"),
        Integer(34, Trivia(comment_ws="   ", comment="# Integer", trail=""), "34"),
    )

    assert '\nfoo = "bar"\nbaz = 34   # Integer' == table.as_string()

    table.remove(Key("baz"))

    assert '\nfoo = "bar"\n' == table.as_string()

    table.remove(Key("foo"))

    assert "\n" == table.as_string()

    with pytest.raises(NonExistentKey):
        table.remove(Key("foo"))


def test_items_can_be_appended_to_and_removed_from_an_inline_table():
    string = """table = {}
"""

    parser = Parser(string)
    _, table = parser._parse_item()

    assert isinstance(table, InlineTable)
    assert "{}" == table.as_string()

    table.append(Key("foo"), String(StringType.SLB, "bar", "bar", Trivia(trail="")))

    assert '{foo = "bar"}' == table.as_string()

    table.append(Key("baz"), Integer(34, Trivia(trail=""), "34"))

    assert '{foo = "bar", baz = 34}' == table.as_string()

    table.remove(Key("baz"))

    assert '{foo = "bar"}' == table.as_string()

    table.remove(Key("foo"))

    assert "{}" == table.as_string()

    with pytest.raises(NonExistentKey):
        table.remove(Key("foo"))
