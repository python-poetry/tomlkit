import io
import os

from tomlkit.toml_document import TOMLDocument
from tomlkit.toml_file import TOMLFile


def test_toml_file(example):
    original_content = example("example")

    toml_file = os.path.join(os.path.dirname(__file__), "examples", "example.toml")
    toml = TOMLFile(toml_file)

    content = toml.read()
    assert isinstance(content, TOMLDocument)
    assert content["owner"]["organization"] == "GitHub"

    toml.write(content)

    try:
        with io.open(toml_file, encoding="utf-8") as f:
            assert original_content == f.read()
    finally:
        with io.open(toml_file, "w", encoding="utf-8") as f:
            assert f.write(original_content)


def test_keep_old_eol(tmpdir):
    toml_path = str(tmpdir / "pyproject.toml")
    with io.open(toml_path, "wb+") as f:
        f.write(b"a = 1\r\nb = 2\r\n")

    f = TOMLFile(toml_path)
    content = f.read()
    assert f._line_ending == "\r\n"
    content["b"] = 3
    f.write(content)

    with io.open(toml_path, "rb") as f:
        assert f.read() == b"a = 1\r\nb = 3\r\n"


def test_mixed_eol(tmpdir):
    toml_path = str(tmpdir / "pyproject.toml")
    with io.open(toml_path, "wb+") as f:
        f.write(b"a = 1\rb = 2\r\nc = 3\n")

    f = TOMLFile(toml_path)
    f.write(f.read())

    with io.open(toml_path, "rb") as f:
        assert f.read() == "a = 1{0}b = 2{0}c = 3{0}".format(os.linesep).encode()
