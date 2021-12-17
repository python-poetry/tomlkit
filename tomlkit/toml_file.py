from .api import loads
from .toml_document import TOMLDocument


class TOMLFile:
    """
    Represents a TOML file.
    """

    def __init__(self, path: str) -> None:
        self._path = path

    def read(self) -> TOMLDocument:
        with open(self._path, encoding="utf-8", newline="") as f:
            return loads(f.read())

    def write(self, data: TOMLDocument) -> None:
        with open(self._path, "w", encoding="utf-8", newline="") as f:
            f.write(data.as_string())
