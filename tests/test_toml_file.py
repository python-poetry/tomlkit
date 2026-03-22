import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from tomlkit.toml_document import TOMLDocument
from tomlkit.toml_file import TOMLFile


def test_toml_file(example: Callable[[str], str]) -> None:
    original_content = example("example")

    toml_file = os.path.join(os.path.dirname(__file__), "examples", "example.toml")
    toml = TOMLFile(toml_file)

    content = toml.read()
    assert isinstance(content, TOMLDocument)
    assert content["owner"]["organization"] == "GitHub"  # type: ignore[comparison-overlap]

    toml.write(content)

    try:
        with open(toml_file, encoding="utf-8") as f:
            assert original_content == f.read()
    finally:
        with open(toml_file, "w", encoding="utf-8", newline="") as f:
            assert f.write(original_content)


def test_keep_old_eol(tmp_path: Path) -> None:
    toml_path = tmp_path / "pyproject.toml"
    with open(toml_path, "wb+") as fh:
        fh.write(b"a = 1\r\nb = 2\r\n")

    toml_f = TOMLFile(toml_path)
    content = toml_f.read()
    content["b"] = 3
    toml_f.write(content)

    with open(toml_path, "rb") as fh:
        assert fh.read() == b"a = 1\r\nb = 3\r\n"


def test_keep_old_eol_2(tmp_path: Path) -> None:
    toml_path = tmp_path / "pyproject.toml"
    with open(toml_path, "wb+") as fh:
        fh.write(b"a = 1\nb = 2\n")

    toml_f = TOMLFile(toml_path)
    content = toml_f.read()
    content["b"] = 3
    toml_f.write(content)

    with open(toml_path, "rb") as fh:
        assert fh.read() == b"a = 1\nb = 3\n"


def test_mixed_eol(tmp_path: Path) -> None:
    toml_path = tmp_path / "pyproject.toml"
    with open(toml_path, "wb+") as fh:
        fh.write(b"a = 1\r\nrb = 2\n")

    toml_f = TOMLFile(toml_path)
    toml_f.write(toml_f.read())

    with open(toml_path, "rb") as fh:
        assert fh.read() == b"a = 1\r\nrb = 2\n"


def test_consistent_eol(tmp_path: Path) -> None:
    toml_path = tmp_path / "pyproject.toml"
    with open(toml_path, "wb+") as fh:
        fh.write(b"a = 1\r\nb = 2\r\n")

    toml_f = TOMLFile(toml_path)
    content = toml_f.read()
    content["c"] = 3
    toml_f.write(content)

    with open(toml_path, "rb") as fh:
        assert fh.read() == b"a = 1\r\nb = 2\r\nc = 3\r\n"


def test_consistent_eol_2(tmp_path: Path) -> None:
    toml_path = tmp_path / "pyproject.toml"
    with open(toml_path, "wb+") as fh:
        fh.write(b"a = 1\nb = 2\n")

    toml_f = TOMLFile(toml_path)
    content = toml_f.read()
    content["c"] = 3
    content["c"].trivia.trail = "\r\n"
    toml_f.write(content)

    with open(toml_path, "rb") as fh:
        assert fh.read() == b"a = 1\nb = 2\nc = 3\n"


def test_default_eol_is_os_linesep(tmp_path: Path) -> None:
    toml_path = tmp_path / "pyproject.toml"
    toml_f = TOMLFile(toml_path)
    content = TOMLDocument()
    content.append("a", 1)  # type: ignore[arg-type]
    content["a"].trivia.trail = "\n"
    content.append("b", 2)  # type: ignore[arg-type]
    content["b"].trivia.trail = "\r\n"
    toml_f.write(content)
    linesep = os.linesep.encode()
    with open(toml_path, "rb") as fh:
        assert fh.read() == b"a = 1" + linesep + b"b = 2" + linesep


def test_readwrite_eol_windows(tmp_path: Path) -> None:
    toml_path = tmp_path / "pyproject.toml"
    doc = TOMLDocument()
    doc.add("a", 1)  # type: ignore[arg-type]
    toml_f = TOMLFile(toml_path)
    toml_f.write(doc)
    readback = toml_f.read()
    assert doc.as_string() == readback.as_string()
