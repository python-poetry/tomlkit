from datetime import date
from datetime import datetime as dt
from datetime import time
from datetime import timedelta as td
from datetime import timezone as tz
from enum import Enum
from typing import Union

import pytest

import tomlkit

from tomlkit._utils import _utc
from tomlkit._utils import escape_string
from tomlkit._utils import parse_rfc3339


@pytest.mark.parametrize(
    "string, expected",
    [
        ("1979-05-27T07:32:00", dt(1979, 5, 27, 7, 32, 0)),
        ("1979-05-27T07:32:00Z", dt(1979, 5, 27, 7, 32, 0, tzinfo=_utc)),
        (
            "1979-05-27T07:32:00-07:00",
            dt(1979, 5, 27, 7, 32, 0, tzinfo=tz(td(seconds=-7 * 3600), "-07:00")),
        ),
        (
            "1979-05-27T00:32:00.999999-07:00",
            dt(
                1979,
                5,
                27,
                0,
                32,
                0,
                999999,
                tzinfo=tz(td(seconds=-7 * 3600), "-07:00"),
            ),
        ),
        (
            "1979-05-27T07:32:00+05:30",
            dt(
                1979,
                5,
                27,
                7,
                32,
                0,
                tzinfo=tz(td(seconds=5 * 3600 + 30 * 60), "+05:30"),
            ),
        ),
    ],
)
def test_parse_rfc3339_datetime(string: str, expected: Union[dt, date, time]) -> None:
    assert parse_rfc3339(string) == expected


@pytest.mark.parametrize("string, expected", [("1979-05-27", date(1979, 5, 27))])
def test_parse_rfc3339_date(string: str, expected: Union[dt, date, time]) -> None:
    assert parse_rfc3339(string) == expected


@pytest.mark.parametrize(
    "string, expected",
    [("12:34:56", time(12, 34, 56)), ("12:34:56.123456", time(12, 34, 56, 123456))],
)
def test_parse_rfc3339_time(string: str, expected: Union[dt, date, time]) -> None:
    assert parse_rfc3339(string) == expected


class _Color(str, Enum):
    RED = "red"


class _Quoted(str):
    def __str__(self) -> str:
        return f'"{super().__str__()}"'


def test_escape_string_returns_plain_str() -> None:
    result = escape_string("hello")

    assert result == "hello"
    assert type(result) is str


def test_escape_string_str_subclass_stays_plain_str() -> None:
    """Issue #725: a ``str`` subclass must keep its characters, not its ``__str__``."""
    result = escape_string(_Quoted("plain"))

    assert result == "plain"
    assert type(result) is str


def test_escape_string_str_subclass_with_sequences_stays_plain_str() -> None:
    """Issue #725: the escaping branch must not leak the subclass either."""
    result = escape_string(_Quoted("a\nb"))

    assert result == "a\\nb"
    assert type(result) is str


def test_dumps_str_enum_writes_value() -> None:
    """Issue #725: ``dumps`` wrote ``"Color.RED"`` instead of ``"red"``."""
    document = tomlkit.document()
    document["color"] = _Color.RED

    assert tomlkit.dumps(document) == 'color = "red"\n'


def test_dumps_str_subclass_with_custom_str_round_trips() -> None:
    """Issue #725: the emitted document could not be re-parsed."""
    document = tomlkit.document()
    document["k"] = _Quoted("shown")

    dumped = tomlkit.dumps(document)

    assert dumped == 'k = "shown"\n'
    assert tomlkit.parse(dumped)["k"] == "shown"
