from __future__ import annotations

import sys

from datetime import date
from datetime import datetime
from datetime import time
from typing import Any

import pytest

from tomlkit import dumps
from tomlkit import parse
from tomlkit.items import Date
from tomlkit.items import DateTime
from tomlkit.items import Time


def assert_temporal_round_trip(value: date | time, expected: date | time) -> None:
    rendered = dumps({"value": value})
    if sys.version_info >= (3, 11):
        import tomllib

        assert tomllib.loads(rendered) == {"value": expected}
    assert parse(rendered).unwrap() == {"value": expected}


@pytest.mark.parametrize(
    "method, args",
    [
        ("fromisoformat", ("2026-11-09",)),
        ("fromordinal", (date(2026, 11, 9).toordinal(),)),
        ("fromtimestamp", (1720000000,)),
        ("fromisocalendar", (2026, 46, 1)),
    ],
)
def test_date_factories_serialize(method: str, args: tuple[Any, ...]) -> None:
    value = getattr(Date, method)(*args)
    expected = getattr(date, method)(*args)

    assert isinstance(value, Date)
    assert_temporal_round_trip(value, expected)


def test_date_today_serializes() -> None:
    before = date.today()
    value = Date.today()
    after = date.today()

    assert isinstance(value, Date)
    assert value.unwrap() in (before, after)
    assert_temporal_round_trip(value, value.unwrap())


@pytest.mark.parametrize(
    "text",
    [
        "00:00:00",
        "12:34",
        "12:34:56",
        "12:34:56.123456",
        "12:34:56.000001",
        "12:34:56+02:00",
    ],
)
def test_time_fromisoformat_serializes(text: str) -> None:
    value = Time.fromisoformat(text)
    expected = time.fromisoformat(text)

    assert isinstance(value, Time)
    assert value.tzinfo == expected.tzinfo
    assert_temporal_round_trip(value, expected.replace(tzinfo=None))


@pytest.mark.parametrize(
    "source",
    [
        "value = 2026-11-09 # date\n",
        "value = 12:34:56.120000 # time\n",
        "value = 12:34:56.000000 # whole second\n",
    ],
)
def test_parsed_temporal_items_keep_original_format(source: str) -> None:
    assert dumps(parse(source)) == source


def test_datetime_factory_serialization_is_unchanged() -> None:
    text = "2026-11-09T12:34:56.123456"
    value = DateTime.fromisoformat(text)

    assert isinstance(value, DateTime)
    assert_temporal_round_trip(value, datetime.fromisoformat(text))
