import os

from collections.abc import Callable

import pytest


@pytest.fixture
def example() -> Callable[[str], str]:
    def _example(name: str) -> str:
        with open(
            os.path.join(os.path.dirname(__file__), "examples", name + ".toml"),
            encoding="utf-8",
        ) as f:
            return f.read()

    return _example


@pytest.fixture
def json_example() -> Callable[[str], str]:
    def _example(name: str) -> str:
        with open(
            os.path.join(os.path.dirname(__file__), "examples", "json", name + ".json"),
            encoding="utf-8",
        ) as f:
            return f.read()

    return _example


@pytest.fixture
def invalid_example() -> Callable[[str], str]:
    def _example(name: str) -> str:
        with open(
            os.path.join(
                os.path.dirname(__file__), "examples", "invalid", name + ".toml"
            ),
            encoding="utf-8",
        ) as f:
            return f.read()

    return _example
