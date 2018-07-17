import math
import pytest

from tomlkit import parse
from tomlkit.exceptions import NonExistentKey
from tomlkit.items import InlineTable
from tomlkit.items import Integer
from tomlkit.items import Key
from tomlkit.items import String
from tomlkit.items import StringType
from tomlkit.items import Table
from tomlkit.items import Trivia
from tomlkit.parser import Parser


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


def test_inf_and_nan_are_supported(example):
    content = example("0.5.0")
    doc = parse(content)

    assert doc["plus-infinity"] == float("inf")
    assert doc["minus-infinity"] == float("-inf")
    assert doc["infinity"] == float("inf")
    assert math.isnan(doc["not-a-number"])
