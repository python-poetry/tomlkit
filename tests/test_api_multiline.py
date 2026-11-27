import io

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from typing import Any

import pytest

from tomlkit import array
from tomlkit import dump
from tomlkit import dumps
from tomlkit import item
from tomlkit import parse
from tomlkit.items import Array
from tomlkit.items import Trivia
from tomlkit.toml_document import TOMLDocument


def test_dumps_multiline_mapping_and_dump_stream() -> None:
    data = {"z": (1, 2), "a": []}
    expected = "a = []\nz = [\n    1,\n    2,\n]\n"
    assert dumps(data, True, multiline=True) == expected
    stream = io.StringIO()
    dump(data, stream, sort_keys=True, multiline=True)
    assert stream.getvalue() == expected
    assert data == {"z": (1, 2), "a": []}


@pytest.mark.parametrize(
    "source, expected",
    [
        ("a = [1, 2]\n", "a = [\n    1,\n    2,\n]\n"),
        ("[t]\na = [1, 2]\n", "[t]\na = [\n    1,\n    2,\n]\n"),
        ("a.b = [1, 2]\n", "a.b = [\n    1,\n    2,\n]\n"),
        (
            "[[t]]\na = [1, 2]\n[[t]]\na = [3]\n",
            "[[t]]\na = [\n    1,\n    2,\n]\n[[t]]\na = [\n    3,\n]\n",
        ),
        ("a = {b = [1, 2]}\n", "a = {b = [\n    1,\n    2,\n]}\n"),
        ("a = {b.c = [1, 2]}\n", "a = {b.c = [\n    1,\n    2,\n]}\n"),
        (
            "a = [[1, 2], [3]]\n",
            "a = [\n    [\n    1,\n    2,\n],\n    [\n    3,\n],\n]\n",
        ),
        (
            "a = [{b = [1, 2]}]\n",
            "a = [\n    {b = [\n    1,\n    2,\n]},\n]\n",
        ),
        (
            "[a.b]\nx = [1, 2]\n[z]\nx = [3]\n[a.c]\nx = [4]\n",
            "[a.b]\nx = [\n    1,\n    2,\n]\n[z]\nx = [\n    3,\n]\n[a.c]\nx = [\n    4,\n]\n",
        ),
    ],
)
def test_dumps_multiline_preserves_document(source: str, expected: str) -> None:
    doc = parse(source)
    assert dumps(doc, multiline=True) == expected
    assert parse(expected) == doc
    assert dumps(doc) == source
    assert dumps(doc, multiline=False) == source


def test_dumps_multiline_preserves_comments_and_manual_formatting() -> None:
    source = "a = [\n # before\n 1, # one\n # between\n 2 # two\n] # array\n"
    doc = parse(source)
    original_array = doc["a"]
    result = dumps(doc, multiline=True)
    assert parse(result) == doc
    for comment in ["# before", "# one", "# between", "# two", "# array"]:
        assert result.count(comment) == 1
    assert doc["a"] is original_array
    assert original_array._multiline is False
    assert dumps(doc) == source

    explicit = array("[1, 2]").multiline(True)
    assert dumps({"a": explicit}, multiline=False) == "a = [\n    1,\n    2,\n]\n"
    assert explicit._multiline is True


@pytest.mark.parametrize("multiline", [False, True])
def test_dumps_multiline_keeps_custom_renderer_signature(multiline: bool) -> None:
    class CustomArray(Array):
        def as_string(self) -> str:
            return "[42]"

    class CustomDocument(TOMLDocument):
        def as_string(self) -> str:
            return "custom = [42]\n"

    custom = CustomArray([], Trivia())
    assert dumps({"a": custom}, multiline=multiline) == "a = [42]\n"
    assert dumps(CustomDocument(), multiline=multiline) == "custom = [42]\n"

    class Wrapper:
        def as_string(self) -> str:
            return "wrapped = [42]\n"

    assert dumps(Wrapper(), multiline=multiline) == "wrapped = [42]\n"  # type: ignore[arg-type]


def test_nested_dumps_has_its_own_formatting_option() -> None:
    inner_results = []

    class ReentrantArray(Array):
        def as_string(self) -> str:
            inner_results.append(dumps({"inner": [7, 8]}))
            return "[42]"

    result = dumps(
        {"custom": ReentrantArray([], Trivia()), "ordinary": [1, 2]}, multiline=True
    )
    assert inner_results == ["inner = [7, 8]\n"]
    assert result == "custom = [42]\nordinary = [\n    1,\n    2,\n]\n"


def test_failed_multiline_dump_does_not_change_the_input() -> None:
    class FailingArray(Array):
        def as_string(self) -> str:
            raise RuntimeError("render failed")

    shared = array("[1, 2]")
    with pytest.raises(RuntimeError, match="render failed"):
        dumps({"a": shared, "b": FailingArray([], Trivia())}, multiline=True)
    assert shared._multiline is False
    assert shared.as_string() == "[1, 2]"
    assert dumps({"a": shared}) == "a = [1, 2]\n"


def test_concurrent_dumps_can_format_the_same_array_differently() -> None:
    barrier = Barrier(2)

    class SynchronizedArray(Array):
        def as_string(self) -> str:
            barrier.wait(timeout=10)
            return "[]"

    shared = array("[1, 2]")
    data = {"sync": SynchronizedArray([], Trivia()), "a": shared}
    with ThreadPoolExecutor(max_workers=2) as executor:
        normal = executor.submit(dumps, data)
        multiline = executor.submit(dumps, data, multiline=True)
        assert normal.result() == "sync = []\na = [1, 2]\n"
        assert multiline.result() == "sync = []\na = [\n    1,\n    2,\n]\n"
    assert shared.as_string() == "[1, 2]"


def test_multiline_renders_table_and_inline_table_roots() -> None:
    table = item({"a": [1, 2]})
    inline = parse("a = {b = [1, 2]}\n")["a"]
    assert dumps(table, multiline=True) == "a = [\n    1,\n    2,\n]\n"
    assert dumps(inline, multiline=True) == "{b = [\n    1,\n    2,\n]}"
    assert dumps(table) == "a = [1, 2]\n"
    assert dumps(inline) == "{b = [1, 2]}"


def test_multiline_retains_custom_encoder_arrays() -> None:
    from tomlkit import register_encoder
    from tomlkit import unregister_encoder
    from tomlkit.exceptions import ConvertError

    class Value:
        pass

    shared = array("[1, 2]")

    def encoder(value: Any) -> Array:
        if isinstance(value, Value):
            return shared
        raise ConvertError

    register_encoder(encoder)
    try:
        assert dumps({"a": Value()}, multiline=True) == "a = [\n    1,\n    2,\n]\n"
        assert shared.as_string() == "[1, 2]"
    finally:
        unregister_encoder(encoder)
