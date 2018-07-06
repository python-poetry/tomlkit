from typing import Any
from typing import Dict

from ._compat import Path
from .api import dumps
from .api import loads
from .toml_document import TOMLDocument


class TOMLFile(object):
    """
    Represents a TOML file.
    """

    def __init__(self, path):  # type: (Path) -> None
        self._path = path

    def read(self):  # type: () -> TOMLDocument
        with self._path.open(encoding="utf-8") as f:
            return loads(f.read())

    def write(self, data):  # type: (TOMLDocument) -> None
        data = self.dumps(data, sort=sort)

        with self._path.open("w", encoding="utf-8") as f:
            f.write(data.as_string())
