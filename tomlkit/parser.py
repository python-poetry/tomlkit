# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import re
import string

from typing import Iterator
from typing import Optional
from typing import Tuple
from typing import Union

from ._compat import chr
from ._compat import decode
from ._compat import timezone
from ._utils import _escaped
from ._utils import _utc
from .container import Container
from .exceptions import EmptyKeyError
from .exceptions import EmptyTableNameError
from .exceptions import InternalParserError
from .exceptions import InvalidCharInStringError
from .exceptions import InvalidNumberOrDateError
from .exceptions import MixedArrayTypesError
from .exceptions import ParseError
from .exceptions import UnexpectedCharError
from .exceptions import UnexpectedEofError
from .exceptions import Restore
from .items import AoT
from .items import Array
from .items import Bool
from .items import Comment
from .items import Date
from .items import DateTime
from .items import Float
from .items import FloatType
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
from .source import Source
from .toml_char import TOMLChar
from .toml_document import TOMLDocument


class Parser:
    """
    Parser for TOML documents.
    """

    def __init__(self, string):  # type: (str) -> None
        # Input to parse
        self._src = Source(decode(string))

        self._aot_stack = []

    @property
    def _state(self):
        return self._src.state

    @property
    def _idx(self):
        return self._src.idx

    @property
    def _current(self):
        return self._src.current

    @property
    def _marker(self):
        return self._src.marker

    def extract(self):  # type: () -> str
        """
        Extracts the value between marker and index
        """
        return self._src.extract()

    def inc(self, exception=None):  # type: () -> bool
        """
        Increments the parser if the end of the input has not been reached.
        Returns whether or not it was able to advance.
        """
        return self._src.inc(exception=exception)

    def inc_n(self, n, exception=None):  # type: (int) -> bool
        """
        Increments the parser by n characters
        if the end of the input has not been reached.
        """
        return self._src.inc_n(n=n, exception=exception)

    def consume(self, chars, min=0, max=-1, restore=True):
        """
        Consume chars until min/max is satisfied is valid.
        """
        self._src.consume(chars=chars, min=min, max=max, restore=restore)

    def end(self):  # type: () -> bool
        """
        Returns True if the parser has reached the end of the input.
        """
        return self._src.end()

    def mark(self):  # type: () -> None
        """
        Sets the marker to the index's current position
        """
        self._src.mark()

    def parse_error(self, exception=ParseError, *args):
        """
        Creates a generic "parse error" at the current position.
        """
        return self._src.parse_error(exception, *args)

    def parse(self):  # type: () -> TOMLDocument
        body = TOMLDocument(True)

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
            if key is not None and key.is_dotted():
                # We actually have a table
                self._handle_dotted_key(body, key, value)
            elif not self._merge_ws(value, body):
                body.append(key, value)

            self.mark()

        while not self.end():
            key, value = self._parse_table()
            if isinstance(value, Table) and value.is_aot_element():
                # This is just the first table in an AoT. Parse the rest of the array
                # along with it.
                value = self._parse_aot(value, key.key)

            body.append(key, value)

        body.parsing(False)

        return body

    def _merge_ws(self, item, container):  # type: (Item, Container) -> bool
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

    def _is_child(self, parent, child):  # type: (str, str) -> bool
        """
        Returns whether a key is strictly a child of another key.
        AoT siblings are not considered children of one another.
        """
        parent_parts = tuple(self._split_table_name(parent))
        child_parts = tuple(self._split_table_name(child))

        if parent_parts == child_parts:
            return False

        return parent_parts == child_parts[: len(parent_parts)]

    def _split_table_name(self, name):  # type: (str) -> Generator[Key]
        in_name = False
        current = ""
        t = KeyType.Bare
        for c in name:
            c = TOMLChar(c)

            if c == ".":
                if in_name:
                    current += c
                    continue

                if not current:
                    raise self.parse_error()

                yield Key(current, t=t, sep="")

                current = ""
                t = KeyType.Bare
                continue
            elif c in {"'", '"'}:
                if in_name:
                    if t == KeyType.Literal and c == '"':
                        current += c
                        continue

                    if c != t.value:
                        raise self.parse_error()

                    in_name = False
                else:
                    in_name = True
                    t = KeyType.Literal if c == "'" else KeyType.Basic

                continue
            elif in_name or c.is_bare_key_char():
                current += c
            else:
                raise self.parse_error()

        if current:
            yield Key(current, t=t, sep="")

    def _parse_item(self):  # type: () -> Optional[Tuple[Optional[Key], Item]]
        """
        Attempts to parse the next item and returns it, along with its key
        if the item is value-like.
        """
        self.mark()
        with self._state as state:
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
                    state.restore = True
                    break

        return self._parse_key_value(True)

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
            elif c in " \t\r":
                self.inc()
            else:
                raise self.parse_error(UnexpectedCharError, c)

            if self.end():
                break

        while self._current.is_spaces() and self.inc():
            pass

        if self._current == "\r":
            self.inc()

        if self._current == "\n":
            self.inc()

        trail = ""
        if self._idx != self._marker or self._current.is_ws():
            trail = self.extract()

        return comment_ws, comment, trail

    def _parse_key_value(
        self, parse_comment=False, inline=True
    ):  # type: (bool, bool) -> (Key, Item)
        # Leading indent
        self.mark()

        while self._current.is_spaces() and self.inc():
            pass

        indent = self.extract()

        # Key
        key = self._parse_key()
        if not key.key.strip():
            raise self.parse_error(EmptyKeyError)

        self.mark()

        found_equals = self._current == "="
        while self._current.is_kv_sep() and self.inc():
            if self._current == "=":
                if found_equals:
                    raise self.parse_error(UnexpectedCharError, "=")
                else:
                    found_equals = True
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
        dotted = False
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

        if self._current == ".":
            self.inc()
            dotted = True
            key += "." + self._parse_key().as_string()
            key_type = KeyType.Bare
        else:
            self.inc()

        return Key(key, key_type, "", dotted)

    def _parse_bare_key(self):  # type: () -> Key
        """
        Parses a bare key.
        """
        key_type = None
        dotted = False

        self.mark()
        while self._current.is_bare_key_char() and self.inc():
            pass

        key = self.extract()

        if self._current == ".":
            self.inc()
            dotted = True
            key += "." + self._parse_key().as_string()
            key_type = KeyType.Bare

        return Key(key, key_type, "", dotted)

    def _handle_dotted_key(
        self, container, key, value
    ):  # type: (Container, Key) -> None
        names = tuple(self._split_table_name(key.key))
        name = names[0]
        name._dotted = True
        if name in container:
            table = container.item(name)
        else:
            table = Table(Container(True), Trivia(), False, is_super_table=True)
            container.append(name, table)

        for i, _name in enumerate(names[1:]):
            if i == len(names) - 2:
                _name.sep = key.sep

                table.append(_name, value)
            else:
                _name._dotted = True
                if _name in table.value:
                    table = table.value.item(_name)
                else:
                    table.append(
                        _name,
                        Table(
                            Container(True),
                            Trivia(),
                            False,
                            is_super_table=i < len(names) - 2,
                        ),
                    )

                    table = table[_name]

    def _parse_value(self):  # type: () -> Item
        """
        Attempts to parse a value at the current position.
        """
        self.mark()

        with self._state:
            return self._parse_basic_string()

        with self._state:
            return self._parse_literal_string()

        with self._state:
            return self._parse_datetime()

        with self._state:
            return self._parse_date()

        with self._state:
            return self._parse_time()

        with self._state:
            return self._parse_float()

        with self._state:
            return self._parse_integer()

        trivia = Trivia()
        c = self._current
        if c == "t" and self._src[self._idx :].startswith("true"):
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

            try:
                res = Array(elems, trivia)
            except ValueError:
                raise self.parse_error(MixedArrayTypesError)

            if res.is_homogeneous():
                return res

            raise self.parse_error(MixedArrayTypesError)
        elif c == "{":
            # Inline table
            elems = Container(True)
            self.inc()

            while self._current != "}":
                self.mark()
                while self._current.is_spaces() or self._current == ",":
                    self.inc()

                if self._idx != self._marker:
                    ws = self.extract().lstrip(",")
                    if ws:
                        elems.append(None, Whitespace(ws))

                if self._current == "}":
                    break

                key, val = self._parse_key_value(False, inline=True)
                elems.append(key, val)

            self.inc()

            return InlineTable(elems, trivia)
        else:
            raise self.parse_error(UnexpectedCharError, c)

    def _get_offset(self):
        mark_offset = self._idx

        # sign
        sign = self._current
        self.inc(exception=True)

        # hour
        mark = self._idx
        if self._current in "01":
            self.inc(exception=True)
            self.consume(string.digits, min=1, max=1)
        elif self._current in "2":
            self.inc(exception=True)
            self.consume("0123", min=1, max=1)
        else:
            raise Restore
        hour = int(self._src[mark : self._idx])

        # delimiter [:]
        self.consume(":", min=1, max=1)

        # minute
        mark = self._idx
        if self._current in "012345":
            self.inc(exception=True)
            self.consume(string.digits, min=1, max=1)
        else:
            raise Restore
        minute = int(self._src[mark : self._idx])

        seconds = hour * 3600 + minute * 60
        offset = datetime.timedelta(seconds=seconds)
        if sign == "-":
            offset = -offset

        raw = self._src[mark_offset : self._idx]
        return timezone(offset, str(raw))

    def _parse_datetime(self):
        mark = self._idx

        year, month, day = self._get_date()

        # delimiter [T ]
        self.consume("T ", min=1, max=1)

        hour, minute, second, microsecond = self._get_time()

        # delimiter [Z] or timezone
        tzinfo = {}
        if self._current in "Z":
            self.inc()
            tzinfo = {"tzinfo": _utc}
        elif self._current in "+-":
            tzinfo = {"tzinfo": self._get_offset()}

        value = datetime.datetime(
            year, month, day, hour, minute, second, microsecond, **tzinfo
        )
        raw = self._src[mark : self._idx]

        return DateTime(value, Trivia(), raw)

    def _get_date(self):
        # year
        mark = self._idx
        self.consume(string.digits, min=1)
        year = int(self._src[mark : self._idx])

        # delimiter [-]
        self.consume("-", min=1, max=1)

        # month
        mark = self._idx
        if self._current in "0":
            self.inc(exception=True)
            self.consume("123456789", min=1, max=1)
        elif self._current in "1":
            self.inc(exception=True)
            self.consume("012", min=1, max=1)
        else:
            raise Restore
        month = int(self._src[mark : self._idx])

        # delimiter [-]
        self.consume("-", min=1, max=1)

        # day
        mark = self._idx
        if self._current in "0":
            self.inc(exception=True)
            self.consume("123456789", min=1, max=1)
        elif self._current in "12":
            self.inc(exception=True)
            self.consume(string.digits, min=1, max=1)
        elif self._current in "3":
            self.inc(exception=True)
            self.consume("01", min=1, max=1)
        else:
            raise Restore
        day = int(self._src[mark : self._idx])

        return year, month, day

    def _parse_date(self):
        mark = self._idx

        year, month, day = self._get_date()

        value = datetime.date(year, month, day)
        raw = self._src[mark : self._idx]

        return Date(value, Trivia(), raw)

    def _get_time(self):
        # hour
        mark = self._idx
        if self._current in "01":
            self.inc(exception=True)
            self.consume(string.digits, 1, 1)
        elif self._current in "2":
            self.inc(exception=True)
            self.consume("0123", 1, 1)
        else:
            raise Restore
        hour = int(self._src[mark : self._idx])

        # delimiter [:]
        self.consume(":", 1, 1)

        # minute
        mark = self._idx
        if self._current in "012345":
            self.inc(exception=True)
            self.consume(string.digits, 1, 1)
        else:
            raise Restore
        minute = int(self._src[mark : self._idx])

        # delimiter [:]
        self.consume(":", 1, 1)

        # second
        mark = self._idx
        if self._current in "012345":
            self.inc(exception=True)
            self.consume(string.digits, 1, 1)
        elif self._current in "6":
            self.inc(exception=True)
            self.consume("0", 1, 1)
        else:
            raise Restore
        second = int(self._src[mark : self._idx])

        # microsecond
        mark = self._idx
        microsecond = 0
        if self._current == ".":
            self.inc(exception=True)
            self.consume(string.digits, 1, 6)
            microsecond = int("{:<06s}".format(self._src[mark : self._idx]))

        return hour, minute, second, microsecond

    def _parse_time(self):
        mark = self._idx

        hour, minute, second, microsecond = self._get_time()

        value = datetime.time(hour, minute, second, microsecond)
        raw = self._src[mark : self._idx]

        return Time(value, Trivia(), raw)

    def _get_sign(self):  # type: (Parser) -> str
        # if the current char is a sign, consume it
        sign = ""
        if self._current in "+-":
            sign = self._current

            # consume this sign, EOF here is problematic as it would be a bare sign
            self.inc(exception=True)

        return sign

    def _remove_underscore(self, raw, digits):
        # Underscores should be surrounded by digits
        pattern = "(?i)(?<=[{0}])_(?=[{0}])".format(digits)
        clean = re.sub(pattern, "", raw)
        if "_" in clean:
            raise Restore

        return clean

    def _is_zero(self):
        if self._current == "0":
            # consume this zero, EOF here means its just a zero
            self.inc()

            if self._current in string.digits:
                # there is at least one leading zero, this is not allowed
                raise Restore

            return True
        return False

    def _parse_special_float(self, style, sign):
        style = FloatType(style)

        # mark the start of the special
        mark = self._idx

        # only keep parsing for special float if the characters match the style
        # try consuming rest of chars in style
        for c in style:
            self.consume(c, min=1, max=1)

        raw = self._src[mark : self._idx]

        return Float(float(sign + style.value), Trivia(), sign + raw)

    def _parse_float(self):
        # get the sign if there is one
        sign = self._get_sign()

        # try inf
        with self._state:
            return self._parse_special_float(FloatType.INF, sign)

        # try nan
        with self._state:
            return self._parse_special_float(FloatType.NAN, sign)

        # assert the next value is a digit
        if self._current not in string.digits:
            raise Restore

        # mark the start of the number
        mark = self._idx

        # if the first digit is zero check for leading zero
        zero = self._is_zero()

        # what characters are allowed
        digits = string.digits
        digitsu = digits + "_"

        # consume as many valid characters as possible
        # (must consume at least one if we didn't get a zero value)
        self.consume(digitsu, min=0 if zero else 1)

        decimal = exponent = False
        if self._current == ".":
            # decimal
            decimal = True

            # consume this char, EOF here is problematic (middle of number)
            self.inc(exception=True)

            # consume as many valid characters as possible (at least one)
            self.consume(digitsu, min=1)

        if self._current in "eE":
            # exponent
            exponent = True

            # consume this char, EOF here is problematic (middle of number)
            self.inc(exception=True)

            self._get_sign()

            # consume as many valid characters as possible (at least one)
            self.consume(digitsu, min=1)

        # must have a decimal and/or exponent
        if not (decimal or exponent):
            raise Restore

        # get the raw number
        raw = self._src[mark : self._idx]

        # cleanup number as needed
        clean = self._remove_underscore(raw, digits)

        try:
            return Float(float(sign + clean), Trivia(), sign + raw)
        except ValueError:
            pass

        raise Restore

    def _get_base(self, sign, zero):  # type: (str, bool) -> (int, str)
        # default is decimal
        base = 10
        digits = string.digits

        if zero and self._current in "box":
            # binary, octal, or hexadecimal

            if sign:
                # cannot have a sign
                raise Restore

            if self._current == "b":
                # binary
                base = 2
                digits = "01"
            elif self._current == "o":
                # octal
                base = 8
                digits = "01234567"
            elif self._current == "x":
                # hexadecimal
                base = 16
                digits = "0123456789abcdefABCDEF"  # ignore case

            # consume this char, EOF here is bad (middle of number)
            self.inc(exception=True)

        return base, digits

    def _parse_integer(self):
        # get the sign if there is one
        sign = self._get_sign()

        # assert the next value is a digit
        if self._current not in string.digits:
            raise Restore

        # mark the start of the number
        mark = self._idx

        # if the first digit is zero check for leading zero
        zero = self._is_zero()

        # determine what base this is
        base, digits = self._get_base(sign, zero)
        digitsu = digits + "_"

        # consume as many valid characters as possible
        # (must consume at least one if we didn't get a zero value)
        self.consume(digitsu, min=0 if zero else 1)

        # get the raw number
        raw = self._src[mark : self._idx]

        # cleanup number as needed
        clean = self._remove_underscore(raw, digits)

        try:
            return Integer(int(sign + clean, base), Trivia(), sign + raw)
        except ValueError:
            pass

        raise Restore

    def _parse_literal_string(self):  # type: () -> Item
        return self._parse_string(StringType.SLL)

    def _parse_basic_string(self):  # type: () -> Item
        return self._parse_string(StringType.SLB)

    def _parse_escaped_char(self, multiline):
        if multiline and self._current.is_ws():
            # When the last non-whitespace character on a line is
            # a \, it will be trimmed along with all whitespace
            # (including newlines) up to the next non-whitespace
            # character or closing delimiter.
            # """\
            #     hello \
            #     world"""
            tmp = ""
            while self._current.is_ws():
                tmp += self._current
                # consume the whitespace, EOF here is an issue
                # (middle of string)
                self.inc(exception=UnexpectedEofError)
                continue

            # the escape followed by whitespace must have a newline
            # before any other chars
            if "\n" not in tmp:
                raise self.parse_error(InvalidCharInStringError, self._current)

            return ""

        if self._current in _escaped:
            c = _escaped[self._current]

            # consume this char, EOF here is an issue (middle of string)
            self.inc(exception=UnexpectedEofError)

            return c

        if self._current in {"u", "U"}:
            # this needs to be a unicode
            u, ue = self._peek_unicode(self._current == "U")
            if u is not None:
                # consume the U char and the unicode value
                self.inc_n(len(ue) + 1)

                return u

        raise self.parse_error(InvalidCharInStringError, self._current)

    def _parse_string(self, delim):  # type: (str) -> Item
        delim = StringType(delim)
        assert delim.is_singleline()

        # only keep parsing for string if the current character matches the delim
        if self._current != delim.unit:
            raise Restore

        # consume the opening/first delim, EOF here is an issue
        # (middle of string or middle of delim)
        self.inc(exception=UnexpectedEofError)

        if self._current == delim.unit:
            # consume the closing/second delim, we do not care if EOF occurs as
            # that would simply imply an empty single line string
            if not self.inc() or self._current != delim.unit:
                # Empty string
                return String(delim, "", "", Trivia())

            # consume the third delim, EOF here is an issue (middle of string)
            self.inc(exception=UnexpectedEofError)

            delim = delim.toggle()  # convert delim to multi delim

        self.mark()  # to extract the original string with whitespace and all
        value = ""

        # A newline immediately following the opening delimiter will be trimmed.
        if delim.is_multiline() and self._current == "\n":
            # consume the newline, EOF here is an issue (middle of string)
            self.inc(exception=UnexpectedEofError)

        escaped = False  # whether the previous key was ESCAPE
        while True:
            if delim.is_singleline() and self._current.is_nl():
                # single line cannot have actual newline characters
                raise self.parse_error(InvalidCharInStringError, self._current)
            elif not escaped and self._current == delim.unit:
                # try to process current as a closing delim
                original = self.extract()

                close = ""
                if delim.is_multiline():
                    # try consuming three delims as this would mean the end of
                    # the string
                    for last in [False, False, True]:
                        if self._current != delim.unit:
                            # Not a triple quote, leave in result as-is.
                            # Adding back the characters we already consumed
                            value += close
                            close = ""  # clear the close
                            break

                        close += delim.unit

                        # consume this delim, EOF here is only an issue if this
                        # is not the third (last) delim character
                        self.inc(exception=UnexpectedEofError if not last else None)

                    if not close:  # if there is no close characters, keep parsing
                        continue
                else:
                    close = delim.unit

                    # consume the closing delim, we do not care if EOF occurs as
                    # that would simply imply the end of self._src
                    self.inc()

                return String(delim, value, original, Trivia())
            elif delim.is_basic() and escaped:
                # attempt to parse the current char as an escaped value, an exception
                # is raised if this fails
                value += self._parse_escaped_char(delim.is_multiline())

                # no longer escaped
                escaped = False
            elif delim.is_basic() and self._current == "\\":
                # the next char is being escaped
                escaped = True

                # consume this char, EOF here is an issue (middle of string)
                self.inc(exception=UnexpectedEofError)
            else:
                # this is either a literal string where we keep everything as is,
                # or this is not a special escaped char in a basic string
                value += self._current

                # consume this char, EOF here is an issue (middle of string)
                self.inc(exception=UnexpectedEofError)

    def _parse_table(
        self, parent_name=None
    ):  # type: (Optional[str]) -> Tuple[Key, Union[Table, AoT]]
        """
        Parses a table element.
        """
        if self._current != "[":
            raise self.parse_error(
                InternalParserError, "_parse_table() called on non-bracket character."
            )

        indent = self.extract()
        self.inc()  # Skip opening bracket

        if self.end():
            raise self.parse_error(UnexpectedEofError)

        is_aot = False
        if self._current == "[":
            if not self.inc():
                raise self.parse_error(UnexpectedEofError)

            is_aot = True

        # Key
        self.mark()
        while self._current != "]" and self.inc():
            if self.end():
                raise self.parse_error(UnexpectedEofError)

            pass

        name = self.extract()
        if not name.strip():
            raise self.parse_error(EmptyTableNameError)

        key = Key(name, sep="")
        name_parts = tuple(self._split_table_name(name))
        missing_table = False
        if parent_name:
            parent_name_parts = tuple(self._split_table_name(parent_name))
        else:
            parent_name_parts = tuple()

        if len(name_parts) > len(parent_name_parts) + 1:
            missing_table = True

        name_parts = name_parts[len(parent_name_parts) :]

        values = Container(True)

        self.inc()  # Skip closing bracket
        if is_aot:
            # TODO: Verify close bracket
            self.inc()

        cws, comment, trail = self._parse_comment_trail()

        result = Null()

        if len(name_parts) > 1:
            if missing_table:
                # Missing super table
                # i.e. a table initialized like this: [foo.bar]
                # without initializing [foo]
                #
                # So we have to create the parent tables
                table = Table(
                    Container(True),
                    Trivia(indent, cws, comment, trail),
                    is_aot and name_parts[0].key in self._aot_stack,
                    is_super_table=True,
                    name=name_parts[0].key,
                )

                result = table
                key = name_parts[0]

                for i, _name in enumerate(name_parts[1:]):
                    if _name in table:
                        child = table[_name]
                    else:
                        child = Table(
                            Container(True),
                            Trivia(indent, cws, comment, trail),
                            is_aot and i == len(name_parts[1:]) - 1,
                            is_super_table=i < len(name_parts[1:]) - 1,
                            name=_name.key,
                            display_name=name if i == len(name_parts[1:]) - 1 else None,
                        )

                    if is_aot and i == len(name_parts[1:]) - 1:
                        table.append(_name, AoT([child], name=table.name, parsed=True))
                    else:
                        table.append(_name, child)

                    table = child
                    values = table.value
        else:
            if name_parts:
                key = name_parts[0]

        while not self.end():
            item = self._parse_item()
            if item:
                _key, item = item
                if not self._merge_ws(item, values):
                    if _key is not None and _key.is_dotted():
                        self._handle_dotted_key(values, _key, item)
                    else:
                        values.append(_key, item)
            else:
                if self._current == "[":
                    is_aot_next, name_next = self._peek_table()

                    if self._is_child(name, name_next):
                        key_next, table_next = self._parse_table(name)

                        values.append(key_next, table_next)

                        # Picking up any sibling
                        while not self.end():
                            _, name_next = self._peek_table()

                            if not self._is_child(name, name_next):
                                break

                            key_next, table_next = self._parse_table(name)

                            values.append(key_next, table_next)

                    break
                else:
                    raise self.parse_error(
                        InternalParserError,
                        "_parse_item() returned None on a non-bracket character.",
                    )

        if isinstance(result, Null):
            result = Table(
                values,
                Trivia(indent, cws, comment, trail),
                is_aot,
                name=name,
                display_name=name,
            )

            if is_aot and (not self._aot_stack or name != self._aot_stack[-1]):
                result = self._parse_aot(result, name)

        return key, result

    def _peek_table(self):  # type: () -> Tuple[bool, str]
        """
        Peeks ahead non-intrusively by cloning then restoring the
        initial state of the parser.

        Returns the name of the table about to be parsed,
        as well as whether it is part of an AoT.
        """
        # we always want to restore after exiting this scope
        with self._state(save_marker=True, restore=True):
            if self._current != "[":
                raise self.parse_error(
                    InternalParserError,
                    "_peek_table() entered on non-bracket character",
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

            return is_aot, table_name

    def _parse_aot(self, first, name_first):  # type: (Table, str) -> AoT
        """
        Parses all siblings of the provided table first and bundles them into
        an AoT.
        """
        payload = [first]
        self._aot_stack.append(name_first)
        while not self.end():
            is_aot_next, name_next = self._peek_table()
            if is_aot_next and name_next == name_first:
                _, table = self._parse_table(name_first)
                payload.append(table)
            else:
                break

        self._aot_stack.pop()

        return AoT(payload, parsed=True)

    def _peek(self, n):  # type: (int) -> str
        """
        Peeks ahead n characters.

        n is the max number of characters that will be peeked.
        """
        # we always want to restore after exiting this scope
        with self._state(restore=True):
            buf = ""
            for _ in range(n):
                if self._current not in " \t\n\r#,]}":
                    buf += self._current
                    self.inc()
                    continue

                break
            return buf

    def _peek_unicode(self, is_long):  # type: () -> Tuple[bool, str]
        """
        Peeks ahead non-intrusively by cloning then restoring the
        initial state of the parser.

        Returns the unicode value is it's a valid one else None.
        """
        # we always want to restore after exiting this scope
        with self._state(save_marker=True, restore=True):
            if self._current not in {"u", "U"}:
                raise self.parse_error(
                    InternalParserError, "_peek_unicode() entered on non-unicode value"
                )

            # AoT
            self.inc()  # Dropping prefix
            self.mark()

            if is_long:
                chars = 8
            else:
                chars = 4

            if not self.inc_n(chars):
                value, extracted = None, None
            else:
                extracted = self.extract()

                try:
                    value = chr(int(extracted, 16))
                except ValueError:
                    value = None

            return value, extracted
