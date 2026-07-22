from typing import Any

import tomlkit

from tomlkit._types import wrap_method
from tomlkit.items import Array
from tomlkit.items import Table


def test_custom_list_add_returns_plain_list_with_combined_items() -> None:
    arr = tomlkit.array()
    arr.extend([1, 2, 3])

    result = arr + [4, 5]  # noqa: RUF005 (exercising __add__ itself)

    assert result == [1, 2, 3, 4, 5]
    assert not isinstance(result, Array)


def test_custom_list_iadd_mutates_in_place_and_keeps_wrapper_type() -> None:
    arr = tomlkit.array()
    arr.extend([1, 2])
    original_id = id(arr)

    arr += [9]

    assert arr == [1, 2, 9]
    assert isinstance(arr, Array)
    assert id(arr) == original_id


def test_custom_dict_or_returns_new_table_with_merged_items() -> None:
    table = tomlkit.table()
    table["a"] = 1
    table["b"] = 2

    result = table | {"c": 3}

    assert dict(result) == {"a": 1, "b": 2, "c": 3}
    assert isinstance(result, Table)
    assert result is not table


def test_custom_dict_ior_mutates_in_place() -> None:
    table = tomlkit.table()
    table["x"] = 1
    original_id = id(table)

    table |= {"y": 2}

    assert dict(table) == {"x": 1, "y": 2}
    assert id(table) == original_id


class _Wrapped:
    def __init__(self, value: int) -> None:
        self.value = value

    def _new(self, value: int) -> "_Wrapped":
        return _Wrapped(value)


def test_wrap_method_wraps_result_via_new() -> None:
    def raw_add(self: _Wrapped, other: int) -> int:
        return self.value + other

    wrapped_add = wrap_method(raw_add)
    wrapped = _Wrapped(5)

    result = wrapped_add(wrapped, 3)

    assert isinstance(result, _Wrapped)
    assert result.value == 8


def test_wrap_method_passes_through_not_implemented() -> None:
    def raw_not_implemented(self: _Wrapped, other: int) -> Any:
        return NotImplemented

    wrapped_method = wrap_method(raw_not_implemented)
    wrapped = _Wrapped(5)

    assert wrapped_method(wrapped, 3) is NotImplemented
