from __future__ import annotations

from typing import Any

import pytest

import tomlkit

from tomlkit.items import Null


@pytest.mark.parametrize(
    "source",
    ["[]", "[ ]", "[\n]", "[# note\n]", "[1]", "[1,2,]", "[1, # note\n2]"],
)
def test_appends_keep_values_formatting_and_indexes_in_sync(source: str) -> None:
    array = tomlkit.parse("x=" + source)["x"]
    expected = list(array)
    array.extend(value for value in ["new", 4, True])
    expected.extend(["new", 4, True])

    assert array == expected
    assert tomlkit.parse("x=" + array.as_string())["x"] == expected
    array[-1] = "changed"
    expected[-1] = "changed"
    assert tomlkit.parse("x=" + array.as_string())["x"] == expected
    assert array.pop() == expected.pop()
    array.insert(0, "first")
    expected.insert(0, "first")
    assert tomlkit.parse("x=" + array.as_string())["x"] == expected


def test_tail_append_avoids_reindexing(monkeypatch: pytest.MonkeyPatch) -> None:
    array = tomlkit.array()

    def unexpected_reindex() -> None:
        raise AssertionError("tail appends should keep existing indexes")

    monkeypatch.setattr(array, "_reindex", unexpected_reindex)
    array.extend(range(100))

    assert array == list(range(100))
    assert array._index_map == dict(enumerate(range(100)))


@pytest.mark.parametrize("kind", ["null", "whitespace", "comment"])
def test_special_items_keep_the_original_index_rebuild(kind: str) -> None:
    array = tomlkit.array()
    value: Any = {
        "null": Null(),
        "whitespace": tomlkit.ws(" "),
        "comment": tomlkit.comment("note"),
    }[kind]
    array.append(value)
    array.append("after")

    expected = dict(
        enumerate(
            index
            for index, group in enumerate(array._value)
            if group.value is not None and not isinstance(group.value, Null)
        )
    )
    assert array._index_map == expected


def test_extend_self_and_append_after_deletion() -> None:
    array = tomlkit.item([1, 2])
    array.extend(array)
    assert array.as_string() == "[1, 2, 1, 2]"
    del array[1:3]
    array.append(3)
    assert array == [1, 2, 3]
    assert array.as_string() == "[1, 2, 3]"
