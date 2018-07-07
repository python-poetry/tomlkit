import pytest

import tomllib

from tomllib import dumps
from tomllib import loads
from tomllib import parse
from tomllib.exceptions import InvalidNumberOrDateError
from tomllib.exceptions import MixedArrayTypesError
from tomllib.exceptions import UnexpectedCharError
from tomllib.items import AoT
from tomllib.items import Array
from tomllib.items import Bool
from tomllib.items import Date
from tomllib.items import DateTime
from tomllib.items import Float
from tomllib.items import InlineTable
from tomllib.items import Integer
from tomllib.items import Key
from tomllib.items import Table
from tomllib.items import Time
from tomllib.toml_document import TOMLDocument


@pytest.mark.parametrize("example_name", ["example", "fruit", "hard"])
def test_parse_can_parse_valid_toml_files(example, example_name):
    assert isinstance(parse(example(example_name)), TOMLDocument)
    assert isinstance(loads(example(example_name)), TOMLDocument)


@pytest.mark.parametrize(
    "example_name,error",
    [
        ("section_with_trailing_characters", UnexpectedCharError),
        ("key_value_with_trailing_chars", UnexpectedCharError),
        ("array_with_invalid_chars", UnexpectedCharError),
        ("mixed_array_types", MixedArrayTypesError),
        ("invalid_number", InvalidNumberOrDateError),
    ],
)
def test_parse_raises_errors_for_invalid_toml_files(
    invalid_example, error, example_name
):
    with pytest.raises(error):
        parse(invalid_example(example_name))


@pytest.mark.parametrize("example_name", ["example", "fruit", "hard"])
def test_original_string_and_dumped_string_are_equal(example, example_name):
    content = example(example_name)
    parsed = parse(content)

    assert content == dumps(parsed)


def test_integer():
    i = tomllib.integer("34")

    assert isinstance(i, Integer)


def test_float():
    i = tomllib.float_("34.56")

    assert isinstance(i, Float)


def test_boolean():
    i = tomllib.boolean("true")

    assert isinstance(i, Bool)


def test_date():
    dt = tomllib.date("1979-05-13")

    assert isinstance(dt, Date)

    with pytest.raises(ValueError):
        tomllib.date("12:34:56")


def test_time():
    dt = tomllib.time("12:34:56")

    assert isinstance(dt, Time)

    with pytest.raises(ValueError):
        tomllib.time("1979-05-13")


def test_datetime():
    dt = tomllib.datetime("1979-05-13T12:34:56")

    assert isinstance(dt, DateTime)

    with pytest.raises(ValueError):
        tomllib.time("1979-05-13")


def test_array():
    a = tomllib.array()

    assert isinstance(a, Array)

    a = tomllib.array("[1,2, 3]")

    assert isinstance(a, Array)


def test_table():
    t = tomllib.table()

    assert isinstance(t, Table)


def test_inline_table():
    t = tomllib.inline_table()

    assert isinstance(t, InlineTable)


def test_aot():
    t = tomllib.aot()

    assert isinstance(t, AoT)


def test_key():
    k = tomllib.key("foo")

    assert isinstance(k, Key)


def test_key_value():
    k, i = tomllib.key_value("foo = 12")

    assert isinstance(k, Key)
    assert isinstance(i, Integer)
