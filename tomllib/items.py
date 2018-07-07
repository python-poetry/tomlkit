import os

from datetime import date
from datetime import datetime
from datetime import time
from enum import Enum
from typing import List


class StringType(Enum):

    SLB = '"'
    MLB = '"""'
    SLL = "'"
    MLL = "'''"


class Trivia:
    """
    Trivia information (aka metadata).
    """

    def __init__(
        self, indent=None, comment_ws=None, comment=None, trail=None
    ):  # type: (str, str, str, str) -> None
        # Whitespace before a value.
        self.indent = indent or ""
        # Whitespace after a value, but before a comment.
        self.comment_ws = comment_ws or ""
        # Comment, starting with # character, or empty string if no comment.
        self.comment = comment or ""
        # Trailing newline.
        if trail is None:
            trail = os.linesep

        self.trail = trail


class KeyType(Enum):
    """
    The type of a Key.

    Keys can be bare (unquoted), or quoted using basic ("), or literal (')
    quotes following the same escaping rules as single-line StringType.
    """

    Bare = ""
    Basic = '"'
    Literal = "'"


class Key:
    """
    A key value.
    """

    def __init__(self, k, t=None, sep=None):  # type: (str) -> None
        self.t = t or KeyType.Bare
        self.sep = sep or " = "
        self.key = k

    @property
    def delimiter(self):  # type: () -> str
        return self.t.value

    def as_string(self):  # type: () -> str
        return "{}{}{}".format(self.delimiter, self.key, self.delimiter)

    def __hash__(self):  # type: () -> int
        return hash(self.key)

    def __eq__(self, other):  # type: (Key) -> bool
        return self.key == other.key

    def __str__(self):  # type: () -> str
        return self.as_string()

    def __repr__(self):  # type: () -> str
        return "<Key {}>".format(str(self))


class Item:
    """
    An item within a TOML document.
    """

    def __init__(self, trivia):  # type: (Trivia) -> None
        self._trivia = trivia

    @property
    def trivia(self):  # type: () -> Trivia
        return self._trivia

    @property
    def discriminant(self):  # type: () -> int
        raise NotImplementedError()

    def as_string(self):  # type: () -> str
        raise NotImplementedError()

    def __str__(self):  # type: () -> str
        return self.as_string()

    def __repr__(self):  # type: () -> str
        return "<{} {}>".format(self.__class__.__name__, str(self))


class Whitespace(Item):
    """
    A whitespace literal.
    """

    def __init__(self, s):  # type: (str) -> None
        self._s = s

    @property
    def s(self):  # type: () -> str
        return self._s

    @property
    def trivia(self):  # type: () -> Trivia
        raise RuntimeError("Called trivia on a non-value Item variant.")

    @property
    def discriminant(self):  # type: () -> int
        return 0

    def as_string(self):  # type: () -> str
        return self._s

    def __repr__(self):  # type: () -> str
        return "<{} {}>".format(self.__class__.__name__, repr(self._s))


class Comment(Item):
    """
    A comment literal.
    """

    @property
    def trivia(self):  # type: () -> Trivia
        raise RuntimeError("Called trivia on a non-value Item variant.")

    @property
    def discriminant(self):  # type: () -> int
        return 1

    def as_string(self):  # type: () -> str
        return "{}{}{}".format(
            self._trivia.indent, self._trivia.comment, self._trivia.trail
        )

    def __str__(self):  # type: () -> str
        return "{}{}".format(self._trivia.indent, self._trivia.comment)


class Integer(Item):
    """
    An integer literal.
    """

    def __init__(self, value, trivia, raw):  # type: (int, Trivia, str) -> None
        super(Integer, self).__init__(trivia)

        self._value = value
        self._raw = raw

    @property
    def discriminant(self):  # type: () -> int
        return 2

    def as_string(self):  # type: () -> str
        return self._raw


class Float(Item):
    """
    A float literal.
    """

    def __init__(self, value, trivia, raw):  # type: (float, Trivia, str) -> None
        super(Float, self).__init__(trivia)

        self._value = value
        self._raw = raw

    @property
    def discriminant(self):  # type: () -> int
        return 3

    def as_string(self):  # type: () -> str
        return self._raw


class Bool(Item):
    """
    A boolean literal.
    """

    def __init__(self, value, trivia):  # type: (float, Trivia) -> None
        super(Bool, self).__init__(trivia)

        self._value = value

    @property
    def discriminant(self):  # type: () -> int
        return 4

    def as_string(self):  # type: () -> str
        return str(self._value).lower()


class DateTime(Item):
    """
    A datetime literal.
    """

    def __init__(self, value, trivia, raw):  # type: (datetime, Trivia, str) -> None
        super(DateTime, self).__init__(trivia)

        self._value = value
        self._raw = raw

    @property
    def discriminant(self):  # type: () -> int
        return 5

    def as_string(self):  # type: () -> str
        return self._raw


class Date(Item):
    """
    A date literal.
    """

    def __init__(self, value, trivia, raw):  # type: (date, Trivia, str) -> None
        super(Date, self).__init__(trivia)

        self._value = value
        self._raw = raw

    @property
    def discriminant(self):  # type: () -> int
        return 6

    def as_string(self):  # type: () -> str
        return self._raw


class Time(Item):
    """
    A time literal.
    """

    def __init__(self, value, trivia, raw):  # type: (time, Trivia, str) -> None
        super(Time, self).__init__(trivia)

        self._value = value
        self._raw = raw

    @property
    def discriminant(self):  # type: () -> int
        return 7

    def as_string(self):  # type: () -> str
        return self._raw


class Array(Item):
    """
    An array literal
    """

    def __init__(self, value, trivia):  # type: (list, Trivia) -> None
        super(Array, self).__init__(trivia)

        self._value = value

    @property
    def discriminant(self):  # type: () -> int
        return 8

    def is_homogeneous(self):  # type: () -> bool
        if not self._value:
            return True

        discriminants = [
            i.discriminant
            for i in self._value
            if not isinstance(i, (Whitespace, Comment))
        ]

        return len(set(discriminants)) == 1

    def as_string(self):  # type: () -> str
        return "[{}]".format("".join(item.as_string() for item in self._value))


class Table(Item):
    """
    A table literal.
    """

    def __init__(
        self, value, trivia, is_aot_element
    ):  # type: (tomllib.container.Container, Trivia, bool) -> None
        super(Table, self).__init__(trivia)

        self._value = value
        self._is_aot_element = is_aot_element

    @property
    def value(self):  # type: () -> tomllib.container.Container
        return self._value

    @property
    def discriminant(self):  # type: () -> int
        return 9

    def append(self, key, item):  # type: (Key, Item) -> None
        """
        Appends a (key, item) to the table.
        """
        self._value.append(key, item)

    def remove(self, key):  # type: (Key) -> None
        self._value.remove(key)

    def is_aot_element(self):  # type: () -> bool
        return self._is_aot_element

    def as_string(self):  # type: () -> str
        return self._value.as_string()

    def __repr__(self):  # type: () -> str
        return "<Table>".format()


class InlineTable(Item):
    """
    An inline table literal.
    """

    def __init__(
        self, value, trivia
    ):  # type: (tomllib.container.Container, Trivia) -> None
        super(InlineTable, self).__init__(trivia)

        self._value = value

    @property
    def discriminant(self):  # type: () -> int
        return 10

    def append(self, key, item):  # type: (Key, Item) -> None
        """
        Appends a (key, item) to the table.
        """
        self._value.append(key, item)

    def remove(self, key):  # type: (Key) -> None
        self._value.remove(key)

    def as_string(self):  # type: () -> str
        buf = "{"
        for i, (k, v) in enumerate(self._value.body):
            if k is None:
                buf += v.as_string()
                if i == len(self._value.body) - 1:
                    buf = buf.rstrip(", ")

                continue

            buf += "{}{} = {}{}{}".format(
                v.trivia.indent,
                k.as_string(),
                v.as_string(),
                v.trivia.comment,
                v.trivia.trail,
            )

            if i != len(self._value.body) - 1:
                buf += ", "

        buf += "}"

        return buf


class String(Item):
    """
    A string literal.
    """

    def __init__(
        self, t, value, original, trivia
    ):  # type: (StringType, str, original, Trivia) -> None
        super(String, self).__init__(trivia)

        self._t = t
        self._value = value
        self._original = original

    @property
    def discriminant(self):  # type: () -> int
        return 11

    def as_string(self):  # type: () -> str
        return "{}{}{}".format(self._t.value, self._original, self._t.value)


class AoT(Item):
    """
    An array of table literal
    """

    def __init__(self, body):  # type: (List[Item]) -> None
        self._body = body

    @property
    def body(self):  # type: () -> List[Item]
        return self._body

    @property
    def trivia(self):  # type: () -> Trivia
        raise RuntimeError("Called trivia on a non-value Item variant.")

    @property
    def discriminant(self):  # type: () -> int
        return 12

    def as_string(self):  # type: () -> str
        b = ""
        for table in self._body:
            b += table.as_string()

        return b


class Null(Item):
    """
    A null item.
    """

    def __init__(self):  # type: () -> None
        pass

    @property
    def discriminant(self):  # type: () -> int
        return -1

    def as_string(self):  # type: () -> str
        return ""
