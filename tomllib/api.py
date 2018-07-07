import datetime as _datetime

from typing import Dict
from typing import Tuple

from ._utils import parse_rfc3339
from .container import Container
from .items import AoT
from .items import Array
from .items import Bool
from .items import Comment
from .items import Date
from .items import DateTime
from .items import Float
from .items import InlineTable
from .items import Integer
from .items import Key
from .items import KeyType
from .items import String
from .items import StringType
from .items import Table
from .items import Time
from .items import Trivia
from .items import Whitespace
from .parser import Parser
from .toml_document import TOMLDocument as _TOMLDocument


def loads(string):  # type: (str) -> _TOMLDocument
    """
    Parses a string into a TOMLDocument.

    Alias for parse().
    """
    return parse(string)


def dumps(data):  # type: (_TOMLDocument) -> str
    """
    Dumps a TOMLDocument into a string.
    """
    return data.as_string()


def parse(string):  # type: (str) -> _TOMLDocument
    """
    Parses a string into a TOMLDocument.
    """
    return Parser(string).parse()


# Items
def integer(raw):  # type: (str) -> Integer
    return Integer(int(raw), Trivia(), raw)


def float_(raw):  # type: (str) -> Float
    return Float(float(raw), Trivia(), raw)


def boolean(raw):  # type: (str) -> Bool
    return Bool(raw == "true", Trivia)


def date(raw):  # type: (str) -> Date
    value = parse_rfc3339(raw)
    if not isinstance(value, _datetime.date):
        raise ValueError("date() only accepts date strings.")

    return Date(value, Trivia(), raw)


def time(raw):  # type: (str) -> Time
    value = parse_rfc3339(raw)
    if not isinstance(value, _datetime.time):
        raise ValueError("time() only accepts time strings.")

    return Time(value, Trivia(), raw)


def datetime(raw):  # type: (str) -> DateTime
    value = parse_rfc3339(raw)
    if not isinstance(value, _datetime.datetime):
        raise ValueError("datetime() only accepts datetime strings.")

    return DateTime(value, Trivia(), raw)


def array(raw=None):  # type: (str) -> Array
    if raw is None:
        raw = "[]"

    return Array(value(raw), Trivia())


def table():  # type: () -> Table
    return Table(Container(), Trivia(), False)


def inline_table():  # type: () -> InlineTable
    return InlineTable(Container(), Trivia())


def aot():  # type: () -> AoT
    return AoT([])


def key(k):  # type: (str) -> Key
    return Key(key)


def value(raw):  # type: (str) -> Item
    return Parser(raw)._parse_value()


def key_value(src):  # type: (str) -> Tuple[Key, Item]
    return Parser(src)._parse_key_value()
