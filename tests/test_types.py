import tomlkit

from tomlkit.items import Array
from tomlkit.items import Table


def test_custom_list_add_returns_combined_items() -> None:
    arr = tomlkit.array()
    arr.extend([1, 2, 3])

    result = arr + [4, 5]  # noqa: RUF005 (exercising __add__ itself)

    assert result == [1, 2, 3, 4, 5]


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
