import datetime as _datetime

from collections.abc import Mapping
from typing import IO
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
from .items import Item as _Item
from .items import Key
from .items import SingleKey
from .items import String
from .items import Table
from .items import Time
from .items import Trivia
from .items import Whitespace
from .items import item
from .parser import Parser
from .toml_document import TOMLDocument


def loads(string: str) -> TOMLDocument:
    """
    Parses a string into a TOMLDocument.

    Alias for parse().
    """
    return parse(string)


def dumps(data: Mapping, sort_keys: bool = False) -> str:
    """
    Dumps a TOMLDocument into a string.
    """
    if not isinstance(data, Container) and isinstance(data, Mapping):
        data = item(dict(data), _sort_keys=sort_keys)

    try:
        # data should be a `Container` (and therefore implement `as_string`)
        # for all type safe invocations of this function
        return data.as_string()  # type: ignore[attr-defined]
    except AttributeError as ex:
        msg = f"Expecting Mapping or TOML Container, {type(data)} given"
        raise TypeError(msg) from ex


def load(fp: IO) -> TOMLDocument:
    """
    Load toml document from a file-like object.
    """
    return parse(fp.read())


def dump(data: Mapping, fp: IO[str], *, sort_keys: bool = False) -> None:
    """
    Dump a TOMLDocument into a writable file stream.
    """
    fp.write(dumps(data, sort_keys=sort_keys))


def parse(string: str) -> TOMLDocument:
    """
    Parses a string into a TOMLDocument.
    """
    return Parser(string).parse()


def document() -> TOMLDocument:
    """
    Returns a new TOMLDocument instance.
    """
    return TOMLDocument()


# Items
def integer(raw: str) -> Integer:
    return item(int(raw))


def float_(raw: str) -> Float:
    return item(float(raw))


def boolean(raw: str) -> Bool:
    return item(raw == "true")


def string(raw: str) -> String:
    return item(raw)


def date(raw: str) -> Date:
    value = parse_rfc3339(raw)
    if not isinstance(value, _datetime.date):
        raise ValueError("date() only accepts date strings.")

    return item(value)


def time(raw: str) -> Time:
    value = parse_rfc3339(raw)
    if not isinstance(value, _datetime.time):
        raise ValueError("time() only accepts time strings.")

    return item(value)


def datetime(raw: str) -> DateTime:
    value = parse_rfc3339(raw)
    if not isinstance(value, _datetime.datetime):
        raise ValueError("datetime() only accepts datetime strings.")

    return item(value)


def array(raw: str = None) -> Array:
    if raw is None:
        raw = "[]"

    return value(raw)


def table() -> Table:
    return Table(Container(), Trivia(), False)


def inline_table() -> InlineTable:
    return InlineTable(Container(), Trivia(), new=True)


def aot() -> AoT:
    return AoT([])


def key(k: str) -> Key:
    return SingleKey(k)


def value(raw: str) -> _Item:
    return Parser(raw)._parse_value()


def key_value(src: str) -> Tuple[Key, _Item]:
    return Parser(src)._parse_key_value()


def ws(src: str) -> Whitespace:
    return Whitespace(src, fixed=True)


def nl() -> Whitespace:
    return ws("\n")


def comment(string: str) -> Comment:
    return Comment(Trivia(comment_ws="  ", comment="# " + string))
