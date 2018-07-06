from typing import Dict

from .parser import Parser
from .toml_document import TOMLDocument as _TOMLDocument


def loads(string):  # type: (str) -> _TOMLDocument
    return parse(string)


def dumps(data):  # type: (_TOMLDocument) -> str
    return data.as_string()


def parse(string):  # type: (str) -> _TOMLDocument
    return Parser(string).parse()
