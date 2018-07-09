from typing import Any
from typing import Dict

from .api import dumps
from .api import loads
from .toml_document import TOMLDocument


class TOMLFile(object):
    """
    Represents a TOML file.
    """

    def __init__(self, path):  # type: (str) -> None
        self._path = path

    def read(self):  # type: () -> TOMLDocument
        with open(self._path, encoding="utf-8") as f:
            return loads(f.read())

    def write(self, data):  # type: (TOMLDocument) -> None
        data = self.dumps(data, sort=sort)

        with open(self._path, "w", encoding="utf-8") as f:
            f.write(data.as_string())
