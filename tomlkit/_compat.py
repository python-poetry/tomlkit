from __future__ import annotations

import sys

from typing import Any


PY38 = sys.version_info >= (3, 8)


def decode(string: Any, encodings: list[str] | None = None):
    if not isinstance(string, bytes):
        return string

    encodings = encodings or ["utf-8", "latin1", "ascii"]

    for encoding in encodings:
        try:
            return string.decode(encoding)
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass

    return string.decode(encodings[0], errors="ignore")
