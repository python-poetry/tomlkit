from typing import Any

import pytest

from tomlkit import key
from tomlkit import parse
from tomlkit.items import SingleKey


class StringKey(str):
    pass


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
