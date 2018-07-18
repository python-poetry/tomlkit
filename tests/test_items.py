import math
import pytest

from tomlkit import parse
from tomlkit.exceptions import NonExistentKey
from tomlkit.items import InlineTable
from tomlkit.items import Integer
from tomlkit.items import Key
from tomlkit.items import KeyType
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
    assert "" == table.as_string()

    table.append(Key("foo"), String(StringType.SLB, "bar", "bar", Trivia(trail="\n")))

    assert 'foo = "bar"\n' == table.as_string()

    table.append(
        Key("baz"),
        Integer(34, Trivia(comment_ws="   ", comment="# Integer", trail=""), "34"),
    )

    assert 'foo = "bar"\nbaz = 34   # Integer' == table.as_string()

    table.remove(Key("baz"))

    assert 'foo = "bar"\n' == table.as_string()

    table.remove(Key("foo"))

    assert "" == table.as_string()

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

    assert doc["sf1"] == float("inf")
    assert doc["sf2"] == float("inf")
    assert doc["sf3"] == float("-inf")

    assert math.isnan(doc["sf4"])
    assert math.isnan(doc["sf5"])
    assert math.isnan(doc["sf6"])


def test_hex_octal_and_bin_integers_are_supported(example):
    content = example("0.5.0")
    doc = parse(content)

    assert doc["hex1"] == 3735928559
    assert doc["hex2"] == 3735928559
    assert doc["hex3"] == 3735928559

    assert doc["oct1"] == 342391
    assert doc["oct2"] == 493

    assert doc["bin1"] == 214


def test_key_automatically_sets_proper_string_type_if_not_bare():
    key = Key("foo.bar")

    assert key.t == KeyType.Basic
