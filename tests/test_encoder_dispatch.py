import functools

from collections.abc import Iterator
from typing import Any

import pytest

from tomlkit import api
from tomlkit.exceptions import ConvertError
from tomlkit.items import CUSTOM_ENCODERS
from tomlkit.items import Item


@pytest.fixture(autouse=True)
def restore_encoders() -> Iterator[None]:
    original = CUSTOM_ENCODERS[:]
    CUSTOM_ENCODERS.clear()
    yield
    CUSTOM_ENCODERS[:] = original


@pytest.mark.parametrize("parameter", ["_parent", "_sort_keys"])
@pytest.mark.parametrize("required", [False, True])
def test_individual_keyword_context(parameter: str, required: bool) -> None:
    captured: dict[str, Any] = {}
    namespace: dict[str, Any] = {"api": api, "captured": captured}
    default = "" if required else "=None"
    exec(
        f"def encode(value, *, {parameter}{default}):\n"
        f'    captured["value"] = {parameter}\n'
        f'    return api.string("converted")\n',
        namespace,
    )
    parent = api.table()
    api.register_encoder(namespace["encode"])
    assert (
        api.item(object(), _parent=parent, _sort_keys=True).as_string() == '"converted"'
    )
    assert captured["value"] is (parent if parameter == "_parent" else True)


@pytest.mark.parametrize("name", ["_parent", "_sort_keys"])
@pytest.mark.parametrize("syntax", ["", ", /"])
def test_primary_value_name_not_reused_as_context(name: str, syntax: str) -> None:
    namespace: dict[str, Any] = {"api": api}
    exec(
        f'def encode({name}{syntax}):\n    return api.string("converted")\n', namespace
    )
    api.register_encoder(namespace["encode"])
    assert (
        api.item(object(), _parent=api.table(), _sort_keys=True).as_string()
        == '"converted"'
    )


def test_bound_method_with_context_subset() -> None:
    class Encoder:
        def __init__(self) -> None:
            self.captured: bool | None = None

        def encode(self, value: Any, *, _sort_keys: bool = False) -> Item:
            self.captured = _sort_keys
            return api.string("converted")

    encoder = Encoder()
    api.register_encoder(encoder.encode)
    assert api.item(object(), _sort_keys=True).as_string() == '"converted"'
    assert encoder.captured is True


def test_partial_encoder_with_context_subset() -> None:
    captured: dict[str, Any] = {}

    def encode(prefix: str, value: Any, *, _parent: Item | None = None) -> Item:
        captured["parent"] = _parent
        return api.string(prefix)

    parent = api.table()
    api.register_encoder(functools.partial(encode, "converted"))
    assert api.item(object(), _parent=parent).as_string() == '"converted"'
    assert captured["parent"] is parent


def test_kwargs_and_legacy_chain() -> None:
    calls: list[Any] = []

    def legacy(value: Any) -> Item:
        calls.append("legacy")
        raise ConvertError("not supported")

    def encode(value: Any, **kwargs: Any) -> Item:
        calls.append(kwargs)
        return api.string("converted")

    api.register_encoder(legacy)
    api.register_encoder(encode)
    parent = api.table()
    assert (
        api.item(object(), _parent=parent, _sort_keys=True).as_string() == '"converted"'
    )
    assert calls == ["legacy", {"_parent": parent, "_sort_keys": True}]


def test_internal_typeerror_propagates_once() -> None:
    calls: list[Any] = []
    error = TypeError("encoder sentinel")

    def encode(value: Any, *, _parent: Item | None = None) -> Item:
        calls.append(value)
        raise error

    api.register_encoder(encode)
    with pytest.raises(TypeError) as caught:
        api.item(object())
    assert caught.value is error
    assert len(calls) == 1


def test_invalid_encoder_return_is_not_accepted() -> None:
    def invalid(value: Any) -> Any:
        return None

    api.register_encoder(invalid)
    with pytest.raises(ConvertError, match="expected to return"):
        api.item(object())


@pytest.mark.parametrize("syntax", ["_parent, /", "*_parent"])
def test_primary_nonkeyword_name_still_allows_context_in_kwargs(syntax: str) -> None:
    captured: dict[str, Any] = {}
    namespace: dict[str, Any] = {"api": api, "captured": captured}
    exec(
        f"def encode({syntax}, **kwargs):\n"
        f"    captured.update(kwargs)\n"
        f'    return api.string("converted")\n',
        namespace,
    )
    parent = api.table()
    api.register_encoder(namespace["encode"])
    assert (
        api.item(object(), _parent=parent, _sort_keys=True).as_string() == '"converted"'
    )
    assert captured == {"_parent": parent, "_sort_keys": True}


def test_bound_primary_keyword_name_does_not_receive_context_twice() -> None:
    captured: dict[str, Any] = {}

    def encode(_parent: Any, **kwargs: Any) -> Item:
        captured.update(kwargs)
        return api.string("converted")

    api.register_encoder(encode)
    assert (
        api.item(object(), _parent=api.table(), _sort_keys=True).as_string()
        == '"converted"'
    )
    assert captured == {"_sort_keys": True}
