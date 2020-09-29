import io
import os

from .api import loads
from .toml_document import TOMLDocument


class TOMLFile(object):
    """
    Represents a TOML file.
    """

    def __init__(self, path):  # type: (str) -> None
        self._path = path
        self._line_ending = os.linesep

    def read(self):  # type: () -> TOMLDocument
        with io.open(self._path, "r", encoding="utf-8", newline=None) as f:
            content = f.read()
            if not isinstance(f.newlines, tuple):
                # mixed line endings
                self._line_ending = f.newlines
            return loads(content)

    def write(self, data):  # type: (TOMLDocument) -> None
        with io.open(self._path, "w", encoding="utf-8", newline=self._line_ending) as f:
            f.write(data.as_string())
