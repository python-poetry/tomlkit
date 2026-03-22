from __future__ import annotations

import datetime
import re
import string

from typing import Any

from tomlkit._compat import decode
from tomlkit._utils import RFC_3339_LOOSE
from tomlkit._utils import _escaped
from tomlkit._utils import parse_rfc3339
from tomlkit.container import Container
from tomlkit.exceptions import EmptyKeyError
from tomlkit.exceptions import EmptyTableNameError
from tomlkit.exceptions import InternalParserError
from tomlkit.exceptions import InvalidCharInStringError
from tomlkit.exceptions import InvalidControlChar
from tomlkit.exceptions import InvalidDateError
from tomlkit.exceptions import InvalidDateTimeError
from tomlkit.exceptions import InvalidNumberError
from tomlkit.exceptions import InvalidTimeError
from tomlkit.exceptions import InvalidUnicodeValueError
from tomlkit.exceptions import ParseError
from tomlkit.exceptions import UnexpectedCharError
from tomlkit.exceptions import UnexpectedEofError
from tomlkit.items import AoT
from tomlkit.items import Array
from tomlkit.items import Bool
from tomlkit.items import BoolType
from tomlkit.items import Comment
from tomlkit.items import Date
from tomlkit.items import DateTime
from tomlkit.items import Float
from tomlkit.items import InlineTable
from tomlkit.items import Integer
from tomlkit.items import Item
from tomlkit.items import Key
from tomlkit.items import KeyType
from tomlkit.items import Null
from tomlkit.items import SingleKey
from tomlkit.items import String
from tomlkit.items import StringType
from tomlkit.items import Table
from tomlkit.items import Time
from tomlkit.items import Trivia
from tomlkit.items import Whitespace
from tomlkit.source import Source
from tomlkit.source import _StateHandler
from tomlkit.toml_char import BARE
from tomlkit.toml_char import KV
from tomlkit.toml_char import NL
from tomlkit.toml_char import SPACES
from tomlkit.toml_char import WS
from tomlkit.toml_document import TOMLDocument


CTRL_I = 0x09  # Tab
CTRL_J = 0x0A  # Line feed
CTRL_M = 0x0D  # Carriage return
CTRL_CHAR_LIMIT = 0x1F
CHR_DEL = 0x7F


class Parser:
    """
    Parser for TOML documents.
    """

    def __init__(self, string: str | bytes) -> None:
        # Input to parse
        self._src = Source(decode(string))

        self._aot_stack: list[Key] = []

    @property
    def _state(self) -> _StateHandler:
        return self._src._state

    @property
    def _idx(self) -> int:
        return self._src._idx

    @property
    def _current(self) -> str:
        return self._src._current

    @property
    def _marker(self) -> int:
        return self._src._marker

    def extract(self) -> str:
        """
        Extracts the value between marker and index
        """
        return self._src.extract()

    def inc(self, exception: type[ParseError] | None = None) -> bool:
        """
        Increments the parser if the end of the input has not been reached.
        Returns whether or not it was able to advance.
        """
        return self._src.inc(exception=exception)

    def inc_n(self, n: int, exception: type[ParseError] | None = None) -> bool:
        """
        Increments the parser by n characters
        if the end of the input has not been reached.
        """
        return self._src.inc_n(n=n, exception=exception)

    def consume(self, chars: str, min: int = 0, max: int = -1) -> None:
        """
        Consume chars until min/max is satisfied is valid.
        """
        return self._src.consume(chars=chars, min=min, max=max)

    def end(self) -> bool:
        """
        Returns True if the parser has reached the end of the input.
        """
        return self._src.end()

    def mark(self) -> None:
        """
        Sets the marker to the index's current position
        """
        self._src.mark()

    def parse_error(
        self,
        exception: type[ParseError] = ParseError,
        *args: Any,
        **kwargs: Any,
    ) -> ParseError:
        """
        Creates a generic "parse error" at the current position.
        """
        return self._src.parse_error(exception, *args, **kwargs)

    def parse(self) -> TOMLDocument:
        body = TOMLDocument(True)
        src = self._src

        # Take all keyvals outside of tables/AoT's.
        while src._idx < src._length:
            # Break out if a table is found
            if src._current == "[":
                break

            # Otherwise, take and append one KV
            item = self._parse_item()
            if not item:
                break

            key, value = item
            if (key is not None and key.is_multi()) or not self._merge_ws(value, body):
                # We actually have a table
                try:
                    body.append(key, value)
                except Exception as e:
                    raise src.parse_error(ParseError, str(e)) from e

            src._marker = src._idx

        while src._idx < src._length:
            key, value = self._parse_table()
            if isinstance(value, Table) and value.is_aot_element():
                # This is just the first table in an AoT. Parse the rest of the array
                # along with it.
                value = self._parse_aot(value, key)

            try:
                body.append(key, value)
            except Exception as e:
                raise src.parse_error(ParseError, str(e)) from e

        body.parsing(False)

        return body

    def _merge_ws(self, item: Item, container: Container) -> bool:
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

    def _is_child(self, parent: Key, child: Key) -> bool:
        """
        Returns whether a key is strictly a child of another key.
        AoT siblings are not considered children of one another.
        """
        parent_parts = tuple(parent)
        child_parts = tuple(child)

        if parent_parts == child_parts:
            return False

        return parent_parts == child_parts[: len(parent_parts)]

    def _parse_item(self) -> tuple[Key | None, Item] | None:
        """
        Attempts to parse the next item and returns it, along with its key
        if the item is value-like.
        """
        src = self._src
        src._marker = src._idx
        with src._state as state:
            while True:
                c = src._current
                if c == "\n":
                    # Found a newline; Return all whitespace found up to this point.
                    src.inc()

                    return None, Whitespace(src.extract())
                elif c in " \t\r":
                    if c == "\r":
                        with src._state(restore=True):
                            if not src.inc() or src._current != "\n":
                                raise src.parse_error(
                                    InvalidControlChar, CTRL_M, "documents"
                                )
                    # Skip whitespace.
                    if not src.inc():
                        return None, Whitespace(src.extract())
                elif c == "#":
                    # Found a comment, parse it
                    indent = src.extract()
                    cws, comment, trail = self._parse_comment_trail()

                    return None, Comment(Trivia(indent, cws, comment, trail))
                elif c == "[":
                    # Found a table, delegate to the calling function.
                    return None
                else:
                    # Beginning of a KV pair.
                    # Return to beginning of whitespace so it gets included
                    # as indentation for the KV about to be parsed.
                    state.restore = True
                    break

        return self._parse_key_value(True)

    def _parse_comment_trail(self, parse_trail: bool = True) -> tuple[str, str, str]:
        """
        Returns (comment_ws, comment, trail)
        If there is no comment, comment_ws and comment will
        simply be empty.
        """
        src = self._src
        if src._idx >= src._length:
            return "", "", ""

        comment = ""
        comment_ws = ""
        src._marker = src._idx

        while True:
            c = src._current

            if c == "\n":
                break
            elif c == "#":
                comment_ws = src.extract()

                src._marker = src._idx
                src.inc()  # Skip #

                # The comment itself
                while src._idx < src._length and src._current not in NL:
                    code = ord(src._current)
                    if code == CHR_DEL or (code <= CTRL_CHAR_LIMIT and code != CTRL_I):
                        raise src.parse_error(InvalidControlChar, code, "comments")

                    if not src.inc():
                        break

                comment = src.extract()
                src._marker = src._idx

                break
            elif c in " \t\r":
                if c == "\r":
                    with src._state(restore=True):
                        if not src.inc() or src._current != "\n":
                            raise src.parse_error(
                                InvalidControlChar, CTRL_M, "comments"
                            )
                src.inc()
            else:
                raise src.parse_error(UnexpectedCharError, c)

            if src._idx >= src._length:
                break

        trail = ""
        if parse_trail:
            while src._current in SPACES and src.inc():
                pass

            if src._current == "\r":
                with src._state(restore=True):
                    if not src.inc() or src._current != "\n":
                        raise src.parse_error(InvalidControlChar, CTRL_M, "documents")
                src.inc()

            if src._current == "\n":
                src.inc()

            if src._idx != src._marker or src._current in WS:
                trail = src.extract()

        return comment_ws, comment, trail

    def _parse_key_value(self, parse_comment: bool = False) -> tuple[Key, Item]:
        # Leading indent
        src = self._src
        src._marker = src._idx

        while src._current in SPACES and src.inc():
            pass

        indent = src.extract()

        # Key
        key = self._parse_key()

        src._marker = src._idx

        found_equals = src._current == "="
        while src._current in KV and src.inc():
            if src._current == "=":
                if found_equals:
                    raise src.parse_error(UnexpectedCharError, "=")
                else:
                    found_equals = True
        if not found_equals:
            raise src.parse_error(UnexpectedCharError, src._current)

        if not key.sep:
            key.sep = src.extract()
        else:
            key.sep += src.extract()

        # Value
        val = self._parse_value()
        # Comment
        if parse_comment:
            cws, comment, trail = self._parse_comment_trail()
            meta = val.trivia
            if not meta.comment_ws:
                meta.comment_ws = cws

            meta.comment = comment
            meta.trail = trail
        else:
            val.trivia.trail = ""

        val.trivia.indent = indent

        return key, val

    def _parse_key(self) -> Key:
        """
        Parses a Key at the current position;
        WS before the key must be exhausted first at the callsite.
        """
        src = self._src
        src._marker = src._idx
        while src._current in SPACES and src.inc():
            pass
        if src._current in "\"'":
            return self._parse_quoted_key()
        else:
            return self._parse_bare_key()

    def _parse_quoted_key(self) -> Key:
        """
        Parses a key enclosed in either single or double quotes.
        """
        src = self._src
        # Extract the leading whitespace
        original = src.extract()
        quote_style = src._current
        key_type = next((t for t in KeyType if t.value == quote_style), None)

        if key_type is None:
            raise RuntimeError("Should not have entered _parse_quoted_key()")

        key_str = self._parse_string(
            StringType.SLB if key_type == KeyType.Basic else StringType.SLL
        )
        if key_str._t.is_multiline():
            raise src.parse_error(UnexpectedCharError, key_str._t.value)
        original += key_str.as_string()
        src._marker = src._idx
        while src._current in SPACES and src.inc():
            pass
        original += src.extract()
        result: Key = SingleKey(str(key_str), t=key_type, sep="", original=original)
        if src._current == ".":
            src.inc()
            result = result.concat(self._parse_key())

        return result

    def _parse_bare_key(self) -> Key:
        """
        Parses a bare key.
        """
        src = self._src
        while (src._current in BARE or src._current in SPACES) and src.inc():
            pass

        original = src.extract()
        key_s = original.strip()
        if not key_s:
            # Empty key
            raise src.parse_error(EmptyKeyError)

        if " " in key_s:
            # Bare key with spaces in it
            raise src.parse_error(ParseError, f'Invalid key "{key_s}"')

        result: Key = SingleKey(key_s, KeyType.Bare, "", original)

        if src._current == ".":
            src.inc()
            result = result.concat(self._parse_key())

        return result

    def _parse_value(self) -> Item:
        """
        Attempts to parse a value at the current position.
        """
        src = self._src
        src._marker = src._idx
        c = src._current
        trivia = Trivia()

        if c == StringType.SLB.value:
            return self._parse_basic_string()
        elif c == StringType.SLL.value:
            return self._parse_literal_string()
        elif c == BoolType.TRUE.value[0]:
            return self._parse_true()
        elif c == BoolType.FALSE.value[0]:
            return self._parse_false()
        elif c == "[":
            return self._parse_array()
        elif c == "{":
            return self._parse_inline_table()
        elif c in "+-" or self._peek(4) in {
            "+inf",
            "-inf",
            "inf",
            "+nan",
            "-nan",
            "nan",
        }:
            # Number
            while src._current not in " \t\n\r#,]}" and src.inc():
                pass

            raw = src.extract()

            item = self._parse_number(raw, trivia)
            if item is not None:
                return item

            raise src.parse_error(InvalidNumberError)
        elif c in string.digits:
            # Integer, Float, Date, Time or DateTime
            while src._current not in " \t\n\r#,]}" and src.inc():
                pass

            raw = src.extract()

            m = RFC_3339_LOOSE.match(raw)
            if m:
                if m.group("date") and m.group("time"):
                    # datetime
                    try:
                        dt = parse_rfc3339(raw)
                        assert isinstance(dt, datetime.datetime)
                        return DateTime(
                            dt.year,
                            dt.month,
                            dt.day,
                            dt.hour,
                            dt.minute,
                            dt.second,
                            dt.microsecond,
                            dt.tzinfo,
                            trivia,
                            raw,
                        )
                    except ValueError:
                        raise src.parse_error(InvalidDateTimeError) from None

                if m.group("date"):
                    try:
                        dt = parse_rfc3339(raw)
                        assert isinstance(dt, datetime.date)
                        date = Date(dt.year, dt.month, dt.day, trivia, raw)
                        src._marker = src._idx
                        while src._current not in "\t\n\r#,]}" and src.inc():
                            pass

                        time_raw = src.extract()
                        time_part = time_raw.rstrip()
                        trivia.comment_ws = time_raw[len(time_part) :]
                        if not time_part:
                            return date

                        dt = parse_rfc3339(raw + time_part)
                        assert isinstance(dt, datetime.datetime)
                        return DateTime(
                            dt.year,
                            dt.month,
                            dt.day,
                            dt.hour,
                            dt.minute,
                            dt.second,
                            dt.microsecond,
                            dt.tzinfo,
                            trivia,
                            raw + time_part,
                        )
                    except ValueError:
                        raise src.parse_error(InvalidDateError) from None

                if m.group("time"):
                    try:
                        t = parse_rfc3339(raw)
                        assert isinstance(t, datetime.time)
                        return Time(
                            t.hour,
                            t.minute,
                            t.second,
                            t.microsecond,
                            t.tzinfo,
                            trivia,
                            raw,
                        )
                    except ValueError:
                        raise src.parse_error(InvalidTimeError) from None

            item = self._parse_number(raw, trivia)
            if item is not None:
                return item

            raise src.parse_error(InvalidNumberError)
        else:
            raise src.parse_error(UnexpectedCharError, c)

    def _parse_true(self) -> Bool:
        return self._parse_bool(BoolType.TRUE)

    def _parse_false(self) -> Bool:
        return self._parse_bool(BoolType.FALSE)

    def _parse_bool(self, style: BoolType) -> Bool:
        src = self._src
        with src._state:
            style = BoolType(style)

            # only keep parsing for bool if the characters match the style
            # try consuming rest of chars in style
            for c in style:
                src.consume(c, min=1, max=1)

            return Bool(style, Trivia())

    def _parse_array(self) -> Array:
        src = self._src
        # Consume opening bracket, EOF here is an issue (middle of array)
        src.inc(exception=UnexpectedEofError)

        elems: list[Item] = []
        prev_value = None
        while True:
            # consume whitespace
            mark = src._idx
            src.consume(SPACES + NL)
            indent = src[mark : src._idx]
            newline = set(NL) & set(indent)
            if newline:
                elems.append(Whitespace(indent))
                continue

            # consume comment
            if src._current == "#":
                cws, comment, trail = self._parse_comment_trail(parse_trail=False)
                elems.append(Comment(Trivia(indent, cws, comment, trail)))
                continue

            # consume indent
            if indent:
                elems.append(Whitespace(indent))
                continue

            # consume closing bracket
            if src._current == "]":
                # consume closing bracket, EOF here doesn't matter
                src.inc()
                break

            # consume value
            if not prev_value:
                try:
                    elems.append(self._parse_value())
                    prev_value = True
                    continue
                except UnexpectedCharError:
                    pass

            # consume comma
            if prev_value and src._current == ",":
                src.inc(exception=UnexpectedEofError)
                # If the previous item is Whitespace, add to it
                if isinstance(elems[-1], Whitespace):
                    elems[-1]._s = elems[-1].s + ","
                else:
                    elems.append(Whitespace(","))
                prev_value = False
                continue

            raise src.parse_error(UnexpectedCharError, src._current)

        try:
            res = Array(elems, Trivia())
        except ValueError:
            pass
        else:
            return res

        raise src.parse_error(ParseError, "Failed to parse array")

    def _parse_inline_table(self) -> InlineTable:
        src = self._src
        # consume opening bracket, EOF here is an issue (middle of array)
        src.inc(exception=UnexpectedEofError)

        elems = Container(True)
        expect_key = True
        while True:
            while True:
                # consume whitespace and newlines
                mark = src._idx
                src.consume(SPACES + NL)
                raw = src[mark : src._idx]
                if raw:
                    elems.add(Whitespace(raw))

                if src._current != "#":
                    break

                cws, comment, trail = self._parse_comment_trail(parse_trail=False)
                elems.add(Comment(Trivia("", cws, comment, trail)))

            if src._current == "}":
                # consume closing bracket, EOF here doesn't matter
                src.inc()
                break

            if expect_key:
                if src._current == ",":
                    raise src.parse_error(UnexpectedCharError, src._current)
                key, val = self._parse_key_value(False)
                elems.add(key, val)
                expect_key = False
                continue

            if src._current != ",":
                raise src.parse_error(UnexpectedCharError, src._current)

            elems.add(Whitespace(","))
            # consume comma, EOF here is an issue (middle of inline table)
            src.inc(exception=UnexpectedEofError)
            expect_key = True

        return InlineTable(elems, Trivia())

    def _parse_number(self, raw: str, trivia: Trivia) -> Item | None:
        # Leading zeros are not allowed
        sign = ""
        if raw.startswith(("+", "-")):
            sign = raw[0]
            raw = raw[1:]

        if len(raw) > 1 and (
            (raw.startswith("0") and not raw.startswith(("0.", "0o", "0x", "0b", "0e")))
            or (sign and raw.startswith("."))
        ):
            return None

        if raw.startswith(("0o", "0x", "0b")) and sign:
            return None

        digits = "[0-9]"
        base = 10
        if raw.startswith("0b"):
            digits = "[01]"
            base = 2
        elif raw.startswith("0o"):
            digits = "[0-7]"
            base = 8
        elif raw.startswith("0x"):
            digits = "[0-9a-f]"
            base = 16

        # Underscores should be surrounded by digits
        clean = re.sub(f"(?i)(?<={digits})_(?={digits})", "", raw).lower()

        if "_" in clean:
            return None

        if clean.endswith(".") or (
            not clean.startswith("0x") and clean.split("e", 1)[0].endswith(".")
        ):
            return None

        try:
            return Integer(int(sign + clean, base), trivia, sign + raw)
        except ValueError:
            try:
                return Float(float(sign + clean), trivia, sign + raw)
            except ValueError:
                return None

    def _parse_literal_string(self) -> String:
        with self._state:
            return self._parse_string(StringType.SLL)

    def _parse_basic_string(self) -> String:
        with self._state:
            return self._parse_string(StringType.SLB)

    def _parse_escaped_char(self, multiline: bool) -> str:
        src = self._src
        if multiline and src._current in WS:
            # When the last non-whitespace character on a line is
            # a \, it will be trimmed along with all whitespace
            # (including newlines) up to the next non-whitespace
            # character or closing delimiter.
            # """\
            #     hello \
            #     world"""
            tmp = ""
            while src._current in WS:
                tmp += src._current
                # consume the whitespace, EOF here is an issue
                # (middle of string)
                src.inc(exception=UnexpectedEofError)
                continue

            # the escape followed by whitespace must have a newline
            # before any other chars
            if "\n" not in tmp:
                raise src.parse_error(InvalidCharInStringError, src._current)

            return ""

        if src._current in _escaped:
            c = _escaped[src._current]

            # consume this char, EOF here is an issue (middle of string)
            src.inc(exception=UnexpectedEofError)

            return c

        if src._current in {"u", "U"}:
            # this needs to be a unicode
            u, ue = self._peek_unicode(src._current == "U")
            if u is not None:
                assert ue is not None
                # consume the U char and the unicode value
                src.inc_n(len(ue) + 1)

                return u

            raise src.parse_error(InvalidUnicodeValueError)

        if src._current == "x":
            h, he = self._peek_hex()
            if h is not None:
                assert he is not None
                # consume the x char and the hex value
                src.inc_n(len(he) + 1)
                return h

            raise src.parse_error(InvalidUnicodeValueError)

        raise src.parse_error(InvalidCharInStringError, src._current)

    def _parse_string(self, delim: StringType) -> String:
        src = self._src
        # only keep parsing for string if the current character matches the delim
        if src._current != delim.unit:
            raise src.parse_error(
                InternalParserError,
                f"Invalid character for string type {delim}",
            )

        # consume the opening/first delim, EOF here is an issue
        # (middle of string or middle of delim)
        src.inc(exception=UnexpectedEofError)

        if src._current == delim.unit:
            # consume the closing/second delim, we do not care if EOF occurs as
            # that would simply imply an empty single line string
            if not src.inc() or src._current != delim.unit:
                # Empty string
                return String(delim, "", "", Trivia())

            # consume the third delim, EOF here is an issue (middle of string)
            src.inc(exception=UnexpectedEofError)

            delim = delim.toggle()  # convert delim to multi delim

        src._marker = src._idx  # to extract the original string with whitespace and all
        value = ""

        # Pre-compute delim properties — these are constant through the loop
        delim_is_singleline = delim.is_singleline()
        delim_is_multiline = delim.is_multiline()
        delim_is_basic = delim.is_basic()
        delim_unit = delim.unit

        # A newline immediately following the opening delimiter will be trimmed.
        if delim_is_multiline:
            if src._current == "\n":
                # consume the newline, EOF here is an issue (middle of string)
                src.inc(exception=UnexpectedEofError)
            else:
                cur: str = src._current
                with src._state(restore=True):
                    if src.inc():
                        cur += src._current
                if cur == "\r\n":
                    src.inc_n(2, exception=UnexpectedEofError)

        escaped = False  # whether the previous key was ESCAPE
        while True:
            code = ord(src._current)
            if (
                delim_is_singleline
                and not escaped
                and (code == CHR_DEL or (code <= CTRL_CHAR_LIMIT and code != CTRL_I))
            ) or (
                delim_is_multiline
                and not escaped
                and (
                    code == CHR_DEL
                    or (
                        code <= CTRL_CHAR_LIMIT and code not in (CTRL_I, CTRL_J, CTRL_M)
                    )
                )
            ):
                raise src.parse_error(InvalidControlChar, code, "strings")
            elif delim_is_multiline and not escaped and src._current == "\r":
                with src._state(restore=True):
                    if not src.inc() or src._current != "\n":
                        raise src.parse_error(InvalidControlChar, CTRL_M, "strings")
            elif not escaped and src._current == delim_unit:
                # try to process current as a closing delim
                original = src.extract()

                close = ""
                if delim_is_multiline:
                    # Consume the delimiters to see if we are at the end of the string
                    close = ""
                    while src._current == delim_unit:
                        close += src._current
                        src.inc()

                    if len(close) < 3:
                        # Not a triple quote, leave in result as-is.
                        # Adding back the characters we already consumed
                        value += close
                        continue

                    if len(close) == 3:
                        # We are at the end of the string
                        return String(delim, value, original, Trivia())

                    if len(close) >= 6:
                        raise src.parse_error(InvalidCharInStringError, src._current)

                    value += close[:-3]
                    original += close[:-3]

                    return String(delim, value, original, Trivia())
                else:
                    # consume the closing delim, we do not care if EOF occurs as
                    # that would simply imply the end of self._src
                    src.inc()

                return String(delim, value, original, Trivia())
            elif delim_is_basic and escaped:
                # attempt to parse the current char as an escaped value, an exception
                # is raised if this fails
                value += self._parse_escaped_char(delim_is_multiline)

                # no longer escaped
                escaped = False
            elif delim_is_basic and src._current == "\\":
                # the next char is being escaped
                escaped = True

                # consume this char, EOF here is an issue (middle of string)
                src.inc(exception=UnexpectedEofError)
            else:
                # this is either a literal string where we keep everything as is,
                # or this is not a special escaped char in a basic string
                value += src._current

                # consume this char, EOF here is an issue (middle of string)
                src.inc(exception=UnexpectedEofError)

    def _parse_table_header(self) -> tuple[str, bool, Key]:
        """
        Parses the header of a table ([key] or [[key]]).

        Returns (indent, is_aot, key).
        Leaves the parser positioned at the closing ']'.
        """
        indent = self.extract()
        self.inc()  # Skip opening bracket

        if self.end():
            raise self.parse_error(UnexpectedEofError)

        is_aot = False
        if self._current == "[":
            if not self.inc():
                raise self.parse_error(UnexpectedEofError)

            is_aot = True
        try:
            key = self._parse_key()
        except EmptyKeyError:
            raise self.parse_error(EmptyTableNameError) from None

        return indent, is_aot, key

    def _parse_table(
        self,
        parent_name: Key | None = None,
        parent: Table | None = None,
        _header: tuple[str, bool, Key] | None = None,
    ) -> tuple[Key, Table | AoT]:
        """
        Parses a table element.
        """
        if _header is not None:
            indent, is_aot, key = _header
        else:
            if self._current != "[":
                raise self.parse_error(
                    InternalParserError,
                    "_parse_table() called on non-bracket character.",
                )
            indent, is_aot, key = self._parse_table_header()

        if self.end():
            raise self.parse_error(UnexpectedEofError)
        elif self._current != "]":
            raise self.parse_error(UnexpectedCharError, self._current)

        key.sep = ""
        full_key = key
        name_parts = tuple(key)
        if any(" " in part.key.strip() and part.is_bare() for part in name_parts):
            raise self.parse_error(
                ParseError, f'Invalid table name "{full_key.as_string()}"'
            )

        missing_table = False
        if parent_name:
            parent_name_parts = tuple(parent_name)
        else:
            parent_name_parts = ()

        if len(name_parts) > len(parent_name_parts) + 1:
            missing_table = True

        name_parts = name_parts[len(parent_name_parts) :]

        values = Container(True)

        self.inc()  # Skip closing bracket
        if is_aot:
            # TODO: Verify close bracket
            self.inc()

        cws, comment, trail = self._parse_comment_trail()

        result: Table | AoT = Null()  # type: ignore[assignment]
        table = Table(
            values,
            Trivia(indent, cws, comment, trail),
            is_aot,
            name=name_parts[0].key if name_parts else key.key,
            display_name=full_key.as_string(),
            is_super_table=False,
        )

        if len(name_parts) > 1:
            if missing_table:
                # Missing super table
                # i.e. a table initialized like this: [foo.bar]
                # without initializing [foo]
                #
                # So we have to create the parent tables
                table = Table(
                    Container(True),
                    Trivia("", cws, comment, trail),
                    is_aot and name_parts[0] in self._aot_stack,
                    is_super_table=True,
                    name=name_parts[0].key,
                )

            result = table
            key = name_parts[0]

            for i, _name in enumerate(name_parts[1:]):
                child = table.get(
                    _name,
                    Table(
                        Container(True),
                        Trivia(indent, cws, comment, trail),
                        is_aot and i == len(name_parts) - 2,
                        is_super_table=i < len(name_parts) - 2,
                        name=_name.key,
                        display_name=(
                            full_key.as_string() if i == len(name_parts) - 2 else None
                        ),
                    ),
                )

                if is_aot and i == len(name_parts) - 2:
                    table.raw_append(_name, AoT([child], name=table.name, parsed=True))
                else:
                    table.raw_append(_name, child)

                table = child
                values = table.value
        else:
            if name_parts:
                key = name_parts[0]

        while not self.end():
            parsed = self._parse_item()
            if parsed:
                _key, _val = parsed
                if not self._merge_ws(_val, values):
                    table.raw_append(_key, _val)
            else:
                if self._current == "[":
                    # Parse header tentatively to check for child table
                    src = self._src
                    saved = (src._idx, src._current, src._marker)
                    header = self._parse_table_header()
                    key_next = header[2]

                    if self._is_child(full_key, key_next):
                        key_next, table_next = self._parse_table(
                            full_key, table, _header=header
                        )
                        table.raw_append(key_next, table_next)

                        # Picking up any sibling
                        while not self.end():
                            saved = (src._idx, src._current, src._marker)
                            header = self._parse_table_header()
                            key_next = header[2]

                            if not self._is_child(full_key, key_next):
                                src._idx, src._current, src._marker = saved
                                break

                            key_next, table_next = self._parse_table(
                                full_key, table, _header=header
                            )
                            table.raw_append(key_next, table_next)
                    else:
                        src._idx, src._current, src._marker = saved

                    break
                else:
                    raise self.parse_error(
                        InternalParserError,
                        "_parse_item() returned None on a non-bracket character.",
                    )
        table.value._validate_out_of_order_table()
        if isinstance(result, Null):
            result = table

            if is_aot and (not self._aot_stack or full_key != self._aot_stack[-1]):
                result = self._parse_aot(result, full_key)

        return key, result

    def _parse_aot(self, first: Table, name_first: Key) -> AoT:
        """
        Parses all siblings of the provided table first and bundles them into
        an AoT.
        """
        payload: list[Table] = [first]
        self._aot_stack.append(name_first)
        src = self._src
        while not self.end():
            saved = (src._idx, src._current, src._marker)
            header = self._parse_table_header()
            is_aot_next = header[1]
            name_next = header[2]
            if is_aot_next and name_next == name_first:
                _, table = self._parse_table(name_first, _header=header)
                assert isinstance(table, Table)
                payload.append(table)
            else:
                src._idx, src._current, src._marker = saved
                break

        self._aot_stack.pop()

        return AoT(payload, parsed=True)

    def _peek(self, n: int) -> str:
        """
        Peeks ahead n characters.

        n is the max number of characters that will be peeked.
        """
        # we always want to restore after exiting this scope
        with self._state(restore=True):
            buf = ""
            for _ in range(n):
                if self._current not in " \t\n\r#,]}\0":
                    buf += self._current
                    self.inc()
                    continue

                break
            return buf

    def _peek_unicode(self, is_long: bool) -> tuple[str | None, str | None]:
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

                if extracted[0].lower() == "d" and extracted[1].strip("01234567"):
                    return None, None

                try:
                    value = chr(int(extracted, 16))
                except (ValueError, OverflowError):
                    value = None

            return value, extracted

    def _peek_hex(self) -> tuple[str | None, str | None]:
        with self._state(save_marker=True, restore=True):
            if self._current != "x":
                raise self.parse_error(
                    InternalParserError, "_peek_hex() entered on non-hex value"
                )

            self.inc()  # Dropping prefix
            self.mark()

            if not self.inc_n(2):
                return None, None

            extracted = self.extract()
            if extracted.strip("0123456789abcdefABCDEF"):
                return None, None

            try:
                value = chr(int(extracted, 16))
            except (ValueError, OverflowError):
                value = None

            return value, extracted
