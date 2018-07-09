import datetime as _datetime

from typing import Any
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


def document():  # type: () -> _TOMLDocument
    """
    Returns a new TOMLDocument instance.
    """
    return _TOMLDocument()


# Items
def integer(raw):  # type: (str) -> Integer
    return Integer(int(raw), Trivia(), raw)


def float_(raw):  # type: (str) -> Float
    return Float(float(raw), Trivia(), raw)


def boolean(raw):  # type: (str) -> Bool
    return Bool(raw == "true", Trivia())


def string(raw):  # type: (str) -> String
    return String(StringType.SLB, raw, raw, Trivia())


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

    return value(raw)


def table():  # type: () -> Table
    return Table(Container(), Trivia(indent="\n"), False)


def inline_table():  # type: () -> InlineTable
    return InlineTable(Container(), Trivia())


def aot():  # type: () -> AoT
    return AoT([])


def key(k):  # type: (str) -> Key
    return Key(k)


def value(raw):  # type: (str) -> Item
    return Parser(raw)._parse_value()


def key_value(src):  # type: (str) -> Tuple[Key, Item]
    return Parser(src)._parse_key_value()


def ws(src):  # type: (str) -> Whitespace
    return Whitespace(src)


def nl():  # type: (src) -> Whitespace
    return ws("\n")


def comment(string):  # type: (str) -> Comment
    return Comment(Trivia(comment_ws="  ", comment="# " + string))


def item(value):  # type: (Any) -> Item
    if isinstance(value, bool):
        return boolean(str(value).lower())
    elif isinstance(value, int):
        return integer(str(value))
    elif isinstance(value, float):
        return float_(str(value))
    elif isinstance(value, list):
        value = "[{}]".format(", ".join([item(v).as_string() for v in value]))

        return array(value)
    elif isinstance(value, str):
        return string(value)
    elif isinstance(value, _datetime.datetime):
        return datetime(value.isoformat().replace("+00:00", "Z"))
    elif isinstance(value, _datetime.date):
        return date(value.isoformat())
    elif isinstance(value, _datetime.time):
        return time(value.isoformat())

    raise ValueError("Invalid type {}".format(type(value)))
