import copy
import pickle

from collections.abc import Callable
from typing import Any

import pytest

from tomlkit import key
from tomlkit import parse
from tomlkit.items import Item
from tomlkit.items import Key
from tomlkit.items import SingleKey
from tomlkit.toml_document import TOMLDocument


class StringKey(str):
    pass


class KeyOperandOnly(SingleKey):
    __hash__ = SingleKey.__hash__

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Key):
            raise TypeError("Key operand required")
        return super().__eq__(other)


def pickle_copy(doc: TOMLDocument) -> TOMLDocument:
    return pickle.loads(pickle.dumps(doc))  # type: ignore[no-any-return]


@pytest.mark.parametrize("clone", [lambda x: x, copy.copy, copy.deepcopy, pickle_copy])
@pytest.mark.parametrize("lookup", ["custom", "ordinary"])
def test_custom_key_comparisons_preserved(
    clone: Callable[[TOMLDocument], TOMLDocument], lookup: str
) -> None:
    doc = parse("")
    doc.append(KeyOperandOnly("custom"), 1)
    doc.append("ordinary", 2)
    doc = clone(doc)
    assert "custom" in doc
    assert doc["custom"] == 1
    assert doc["ordinary"] == 2
    # Upstream's assignment scan compares every stored key to the original
    # query, including unrelated custom keys, before replacing anything.
    with pytest.raises(TypeError, match="Key operand required"):
        doc[lookup] = 3
    doc[key(lookup)] = 4
    assert doc[lookup] == 4


@pytest.mark.parametrize("method", ["insert", "replace"])
def test_custom_key_tracking_after_insert_or_replace(method: str) -> None:
    doc = parse("first = 1\nlast = 2\n")
    custom = KeyOperandOnly("custom")
    if method == "insert":
        doc._insert_at(0, custom, 3)
    else:
        value = doc.item("first")
        assert isinstance(value, Item)
        doc._replace("first", custom, value)
    assert "custom" in doc
    assert doc["custom"] in (1, 3)
    with pytest.raises(TypeError, match="Key operand required"):
        doc["custom"] = 4


@pytest.mark.parametrize("missing", ["", "a b", 'a"b', "雪", "a.b", "\0"])
def test_lookup_missing_key_preserves_quoted_error(missing: str) -> None:
    doc = parse("present = 1\n")
    with pytest.raises(KeyError) as bare_error:
        doc[missing]
    with pytest.raises(KeyError) as key_error:
        doc[key(missing)]
    assert type(bare_error.value) is type(key_error.value)
    assert str(bare_error.value) == str(key_error.value)
    assert missing not in doc


@pytest.mark.parametrize("lookup", ["a key", StringKey("a key"), key("a key")])
def test_repeated_updates_preserve_canonical_key_and_body_order(lookup: Any) -> None:
    doc = parse("first = 0\n  'a key'  = 'old' # keep\nlast = 2\n")
    original_key = doc.body[1][0]
    for value in ("one", "two", "three"):
        doc[lookup] = value
        assert list(doc) == ["first", "a key", "last"]
        assert doc.unwrap() == {"first": 0, "a key": value, "last": 2}
        if isinstance(lookup, str):
            assert doc.body[1][0] is original_key
            assert doc.as_string() == (
                f"first = 0\n  'a key'  = '{value}' # keep\nlast = 2\n"
            )


def test_update_after_deleted_slots_and_out_of_order_fragments() -> None:
    doc = parse("[a.x]\nx = 1\n[b]\nb = 2\n[a.y]\ny = 3\n")
    del doc["b"]
    doc["a"] = {"replacement": 4}
    assert list(doc) == ["a"]
    assert doc.unwrap() == {"a": {"replacement": 4}}
    assert parse(doc.as_string()).unwrap() == doc.unwrap()
    doc["a"] = 5
    assert doc.unwrap() == {"a": 5}
    assert parse(doc.as_string()).unwrap() == doc.unwrap()


def test_existing_key_update_does_not_compare_unrelated_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    doc = parse("".join(f"dependency_{i} = 1\n" for i in range(100)))
    comparisons = []
    original = SingleKey.__eq__

    def compare(self: SingleKey, other: Any) -> bool:
        comparisons.append(self.key)
        return original(self, other)

    monkeypatch.setattr(SingleKey, "__eq__", compare)
    doc["dependency_99"] = 2
    assert set(comparisons) == {"dependency_99"}
    assert doc["dependency_99"] == 2
