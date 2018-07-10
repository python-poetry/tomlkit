# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import itertools
import string

from copy import copy
from typing import Iterator
from typing import Optional
from typing import Tuple

from ._compat import PY2
from ._compat import decode
from ._utils import parse_rfc3339
from .container import Container
from .exceptions import InvalidNumberOrDateError
from .exceptions import MixedArrayTypesError
from .exceptions import ParseError
from .exceptions import UnexpectedCharError
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
from .items import Null
from .items import String
from .items import StringType
from .items import Table
from .items import Time
from .items import Trivia
from .items import Whitespace
from .toml_char import TOMLChar
from .toml_document import TOMLDocument


class Parser:
    """
    Parser for TOML documents.
    """

    def __init__(self, string):  # type: (str) -> None
        # Input to parse
        self._src = decode(string)  # type: str
        # Iterator used for getting characters from src.
        self._chars = iter([(i, TOMLChar(c)) for i, c in enumerate(self._src)])
        # Current byte offset into src.
        self._idx = 0
        # Current character
        self._current = TOMLChar("")  # type: TOMLChar
        # Index into src between which and idx slices will be extracted
        self._marker = 0

        self._aot_stack = []

        self.inc()

    def extract(self):  # type: () -> str
        """
        Extracts the value between marker and index
        """
        if self.end():
            return self._src[self._marker :]
        else:
            return self._src[self._marker : self._idx]

    def inc(self):  # type: () -> bool
        """
        Increments the parser if the end of the input has not been reached.
        Returns whether or not it was able to advance.
        """
        try:
            self._idx, self._current = next(self._chars)

            return True
        except StopIteration:
            self._idx = len(self._src)
            self._current = TOMLChar("\0")

            return False

    def inc_n(self, n):  # type: (int) -> bool
        """
        Increments the parser by n characters
        if the end of the input has not been reached.
        """
        for _ in range(n):
            if not self.inc():
                return False

        return True

    def end(self):  # type: () -> bool
        """
        Returns True if the parser has reached the end of the input.
        """
        return self._idx >= len(self._src) or self._current == "\0"

    def mark(self):  # type: () -> None
        """
        Sets the marker to the index's current position
        """
        self._marker = self._idx

    def parse(self):  # type: () -> TOMLDocument
        body = TOMLDocument()

        # Take all keyvals outside of tables/AoT's.
        while not self.end():
            # Break out if a table is found
            if self._current == "[":
                break

            # Otherwise, take and append one KV
            item = self._parse_item()
            if not item:
                break

            key, value = item
            if not self._merge_ws(value, body):
                body.append(key, value)

            self.mark()

        while not self.end():
            key, value = self._parse_table()
            if isinstance(value, Table) and value.is_aot_element():
                # This is just the first table in an AoT. Parse the rest of the array
                # along with it.
                value = self._parse_aot(value, key.key)

            body.append(key, value)

        return body

    def _merge_ws(self, item, container):  # type: (Item, Container) -> bool:
        """
        Merges the given Item with the last one currently in the given Container if
        both are whitespace items.

        Returns True if the items were merged.
        """
        last = container.last_item()
        if not last:
            return False

        if not isinstance(item, Whitespace) or not isinstance(last, Whitespace):
            return False

        start = self._idx - (len(last.s) + len(item.s))
        container.body[-1] = (
            container.body[-1][0],
            Whitespace(self._src[start : self._idx]),
        )

        return True

    def parse_error(self, kind=ParseError, args=None):  # type: () -> None
        """
        Creates a generic "parse error" at the current position.
        """
        line, col = self._to_linecol(self._idx)

        if args:
            return kind(line, col, *args)
        else:
            return kind(line, col)

    def _to_linecol(self, offset):  # type: (int) -> Tuple[int, int]
        cur = 0
        for i, line in enumerate(self._src.splitlines()):
            if cur + len(line) + 1 > offset:
                return (i + 1, offset - cur)

            cur += len(line) + 1

        return len(self._src.splitlines()), 0

    def _is_child(self, parent, child):  # type: (str, str) -> bool
        """
        Returns whether a key is strictly a child of another key.
        AoT siblings are not considered children of one another.
        """
        return child != parent and child.startswith(parent)

    def _parse_item(self):  # type: () -> Optional[Tuple[Optional[Key], Item]]
        """
        Attempts to parse the next item and returns it, along with its key
        if the item is value-like.
        """
        self.mark()
        saved_idx = self._save_idx()

        while True:
            c = self._current
            if c == "\n":
                # Found a newline; Return all whitespace found up to this point.
                self.inc()

                return (None, Whitespace(self.extract()))
            elif c in " \t\r":
                # Skip whitespace.
                if not self.inc():
                    return (None, Whitespace(self.extract()))
            elif c == "#":
                # Found a comment, parse it
                indent = self.extract()
                cws, comment, trail = self._parse_comment_trail()

                return (None, Comment(Trivia(indent, cws, comment, trail)))
            elif c == "[":
                # Found a table, delegate to the calling function.
                return
            else:
                # Begining of a KV pair.
                # Return to beginning of whitespace so it gets included
                # as indentation for the KV about to be parsed.
                self._restore_idx(*saved_idx)
                key, value = self._parse_key_value(True)

                return key, value

    def _save_idx(self):  # type: () -> Tuple[Iterator, int, str]
        if PY2:
            return itertools.tee(self._chars)[1], self._idx, self._current

        return copy(self._chars), self._idx, self._current

    def _restore_idx(self, chars, idx, current):  # type: (Iterator, int, str) -> None
        self._chars = chars
        self._idx = idx
        self._current = current

    def _parse_comment_trail(self):  # type: () -> Tuple[str, str, str]
        """
        Returns (comment_ws, comment, trail)
        If there is no comment, comment_ws and comment will
        simply be empty.
        """
        if self.end():
            return "", "", ""

        comment = ""
        comment_ws = ""
        self.mark()

        while True:
            c = self._current

            if c == "\n":
                break
            elif c == "#":
                comment_ws = self.extract()

                self.mark()
                self.inc()  # Skip #

                # The comment itself
                while not self.end() and not self._current.is_nl() and self.inc():
                    pass

                comment = self.extract()
                self.mark()

                break
            elif c in " \t\r,":
                self.inc()
            else:
                break

            if self.end():
                break

        while self._current.is_spaces() and self.inc():
            pass

        trail = ""
        if self._idx != self._marker or self._current.is_ws():
            trail = self.extract()

        return comment_ws, comment, trail

    def _parse_key_value(self, parse_comment=False):  # type: (bool) -> (Key, Item)
        # Leading indent
        self.mark()

        while self._current.is_spaces() and self.inc():
            pass

        indent = self.extract()

        # Key
        key = self._parse_key()
        self.mark()
        while self._current.is_kv_sep() and self.inc():
            pass

        key.sep = self.extract()

        # Value
        val = self._parse_value()

        # Comment
        if parse_comment:
            cws, comment, trail = self._parse_comment_trail()
            meta = val.trivia
            meta.comment_ws = cws
            meta.comment = comment
            meta.trail = trail
        else:
            val.trivia.trail = ""

        val.trivia.indent = indent

        return key, val

    def _parse_key(self):  # type: () -> Key
        """
        Parses a Key at the current position;
        WS before the key must be exhausted first at the callsite.
        """
        if self._current in "\"'":
            return self._parse_quoted_key()
        else:
            return self._parse_bare_key()

    def _parse_quoted_key(self):  # type: () -> Key
        """
        Parses a key enclosed in either single or double quotes.
        """
        quote_style = self._current
        key_type = None
        for t in KeyType:
            if t.value == quote_style:
                key_type = t
                break

        if key_type is None:
            raise RuntimeError("Should not have entered _parse_quoted_key()")

        self.inc()
        self.mark()

        while self._current != quote_style and self.inc():
            pass

        key = self.extract()
        self.inc()

        return Key(key, key_type, "")

    def _parse_bare_key(self):  # type: () -> Key
        """
        Parses a bare key.
        """
        self.mark()
        while self._current.is_bare_key_char() and self.inc():
            pass

        key = self.extract()

        return Key(key, sep="")

    def _parse_value(self):  # type: () -> Item
        """
        Attempts to parse a value at the current position.
        """
        self.mark()
        trivia = Trivia()

        c = self._current
        if c == '"':
            return self._parse_basic_string()
        elif c == "'":
            return self._parse_literal_string()
        elif c == "t" and self._src[self._idx :].startswith("true"):
            # Boolean: true
            self.inc_n(4)

            return Bool(True, trivia)
        elif c == "f" and self._src[self._idx :].startswith("false"):
            # Boolean: true
            self.inc_n(5)

            return Bool(False, trivia)
        elif c == "[":
            # Array
            elems = []  # type: List[Item]
            self.inc()

            while self._current != "]":
                self.mark()
                while self._current.is_ws() or self._current == ",":
                    self.inc()

                if self._idx != self._marker:
                    elems.append(Whitespace(self.extract()))

                if self._current == "]":
                    break

                if self._current == "#":
                    cws, comment, trail = self._parse_comment_trail()

                    next_ = Comment(Trivia("", cws, comment, trail))
                else:
                    next_ = self._parse_value()

                elems.append(next_)

            self.inc()

            res = Array(elems, trivia)

            if res.is_homogeneous():
                return res

            raise self.parse_error(MixedArrayTypesError)
        elif c == "{":
            # Inline table
            elems = Container()
            self.inc()

            while self._current != "}":
                if self._current.is_ws() or self._current == ",":
                    self.inc()
                    continue

                key, val = self._parse_key_value(False)
                elems.append(key, val)

            self.inc()

            return InlineTable(elems, trivia)
        elif c in string.digits + "+" + "-":
            # Integer, Float, Date, Time or DateTime
            while self._current not in " \t\n\r#,]}" and self.inc():
                pass

            raw = self.extract()

            item = self._parse_number(raw, trivia)
            if item:
                return item

            try:
                res = parse_rfc3339(raw)
            except ValueError:
                res = None

            if res is None:
                raise self.parse_error(InvalidNumberOrDateError)

            if isinstance(res, datetime.datetime):
                return DateTime(res, trivia, raw)
            elif isinstance(res, datetime.time):
                return Time(res, trivia, raw)
            elif isinstance(res, datetime.date):
                return Date(res, trivia, raw)
            else:
                raise self.parse_error(InvalidNumberOrDateError)
        else:
            raise self.parse_error(UnexpectedCharError, (c))

    def _parse_number(self, raw, trivia):  # type: (str, Trivia) -> Optional[Item]
        # Leading zeros are not allowed
        if len(raw) > 1 and raw.startswith("0") and not raw.startswith("0."):
            return

        # Underscores should be surrounded by digits
        # TODO
        clean = "".join([c for c in raw if raw not in "_ "])

        try:
            return Integer(int(clean), trivia, raw)
        except ValueError:
            try:
                return Float(float(clean), trivia, raw)
            except ValueError:
                return

    def _parse_literal_string(self):  # type: () -> Item
        return self._parse_string("'")

    def _parse_basic_string(self):  # type: () -> Item
        return self._parse_string('"')

    def _parse_string(self, delim):  # type: (str) -> Item
        # TODO: handle escaping
        multiline = False

        if delim == "'":
            str_type = StringType.SLL
        else:
            str_type = StringType.SLB

        # Skip opening delim
        if not self.inc():
            return self.parse_error(UnexpectedEofError)

        if self._current == delim:
            self.inc()

            if self._current == delim:
                multiline = True
                if delim == "'":
                    str_type = StringType.MLL
                else:
                    str_type = StringType.MLB

                if not self.inc():
                    return self.parse_error(UnexpectedEofError)
            else:
                # Empty string
                return String(str_type, "", "", Trivia())

        self.mark()

        previous = None
        while True:
            if previous and previous != "\\" and self._current == delim:
                val = self.extract()

                if multiline:
                    for _ in range(3):
                        if self._current != delim:
                            # Not a triple quote, leave in result as-is.
                            continue

                        self.inc()  # TODO: Handle EOF
                else:
                    self.inc()

                return String(str_type, val, val, Trivia())
            else:
                previous = self._current
                if not self.inc():
                    return self.parse_error(UnexpectedEofError)

    def _parse_table(self):  # type: (Optional[str]) -> Tuple[Key, Item]
        """
        Parses a table element.
        """
        indent = self.extract()
        self.inc()  # Skip opening bracket

        is_aot = False
        if self._current == "[":
            if not self.inc():
                raise self.parse_error(UnexpectedEofError)

            is_aot = True

        # Key
        self.mark()
        while self._current != "]" and self.inc():
            pass

        name = self.extract()
        key = Key(name, sep="")

        self.inc()  # Skip closing bracket
        if is_aot:
            # TODO: Verify close bracket
            self.inc()

        cws, comment, trail = self._parse_comment_trail()

        result = Null()
        values = Container()

        while not self.end():
            item = self._parse_item()
            if item:
                _key, item = item
                if not self._merge_ws(item, values):
                    values.append(_key, item)
            else:
                if self._current == "[":
                    _, name_next = self._peek_table()

                    if self._is_child(name, name_next):
                        key_next, table_next = self._parse_table()
                        key_next = Key(key_next.key[len(name + ".") :])

                        values.append(key_next, table_next)

                        # Picking up any sibling
                        while not self.end():
                            _, name_next = self._peek_table()

                            if not self._is_child(name, name_next):
                                break

                            key_next, table_next = self._parse_table()
                            key_next = Key(key_next.key[len(name + ".") :])

                            values.append(key_next, table_next)
                    else:
                        table = Table(
                            values, Trivia(indent, cws, comment, trail), is_aot
                        )

                        result = table
                        if is_aot and (
                            not self._aot_stack or name != self._aot_stack[-1]
                        ):
                            result = self._parse_aot(table, name)

                    break
                else:
                    raise self.parse_error(
                        InternalParserError,
                        ("_parse_item() returned None on a non-bracket character."),
                    )

        if isinstance(result, Null):
            result = Table(values, Trivia(indent, cws, comment, trail), is_aot)

        return key, result

    def _peek_table(self):  # type: () -> Tuple[bool, str]
        """
        Peeks ahead non-intrusively by cloning then restoring the
        initial state of the parser.

        Returns the name of the table about to be parsed,
        as well as whether it is part of an AoT.
        """
        # Save initial state
        idx = self._save_idx()
        marker = self._marker

        if self._current != "[":
            raise self.parse_error(
                InternalParserError, ("_peek_table() entered on non-bracket character")
            )

        # AoT
        self.inc()
        is_aot = False
        if self._current == "[":
            self.inc()
            is_aot = True

        self.mark()

        while self._current != "]" and self.inc():
            table_name = self.extract()

        # Restore initial state
        self._restore_idx(*idx)
        self._marker = marker

        return is_aot, table_name

    def _parse_aot(self, first, name_first):  # type: (Item, str) -> Item
        """
        Parses all siblings of the provided table first and bundles them into
        an AoT.
        """
        payload = [first]
        self._aot_stack.append(name_first)
        while not self.end():
            is_aot_next, name_next = self._peek_table()
            if is_aot_next and name_next == name_first:
                _, table = self._parse_table()
                payload.append(table)
            else:
                break

        self._aot_stack.pop()

        return AoT(payload)
