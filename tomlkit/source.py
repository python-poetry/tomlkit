from __future__ import annotations

from typing import Any

from tomlkit.exceptions import ParseError
from tomlkit.exceptions import UnexpectedCharError
from tomlkit.toml_char import TOMLChar


class _State:
    def __init__(
        self,
        source: Source,
        save_marker: bool | None = False,
        restore: bool | None = False,
    ) -> None:
        self._source = source
        self._save_marker = save_marker
        self.restore = restore

    def __enter__(self) -> _State:
        # Entering this context manager - save the state
        # PERF: snapshot only the integer index + current char + marker.
        # We no longer carry an iterator (`_chars`) so there's no `copy(...)`
        # to do here — saving 3 attribute reads vs the original iter copy.
        self._idx = self._source._idx
        self._current = self._source._current
        self._marker = self._source._marker

        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception_val: BaseException | None,
        trace: Any,
    ) -> None:
        # Exiting this context manager - restore the prior state
        if self.restore or exception_type:
            self._source._idx = self._idx
            self._source._current = self._current
            if self._save_marker:
                self._source._marker = self._marker


class _StateHandler:
    """
    State preserver for the Parser.
    """

    def __init__(self, source: Source) -> None:
        self._source = source
        self._states: list[_State] = []

    def __call__(
        self,
        save_marker: bool | None = False,
        restore: bool | None = False,
    ) -> _State:
        return _State(self._source, save_marker, restore)

    def __enter__(self) -> _State:
        state = self()
        self._states.append(state)
        return state.__enter__()

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception_val: BaseException | None,
        trace: Any,
    ) -> None:
        state = self._states.pop()
        state.__exit__(exception_type, exception_val, trace)


class Source(str):
    EOF = TOMLChar("\0")

    def __init__(self, _: str) -> None:
        super().__init__()

        # PERF: previously built `iter([(i, TOMLChar(c)) for i, c in enumerate(self)])`
        # which materialized N tuples + N TOMLChars at init time (~584 k allocations
        # per 150-parse benchmark). Switching to an integer index over the underlying
        # str makes init O(1) and lets `inc()` just bump the index and slice the str.
        # The TOMLChar cache (toml_char.py) absorbs the per-character cost.
        self._idx = -1  # pre-start sentinel; first inc() will land on 0
        self._marker = 0
        self._current: TOMLChar = TOMLChar("")

        self._state = _StateHandler(self)

        self.inc()

    def reset(self) -> None:
        # initialize both idx and current
        self.inc()

        # reset marker
        self.mark()

    @property
    def state(self) -> _StateHandler:
        return self._state

    @property
    def idx(self) -> int:
        return self._idx

    @property
    def current(self) -> TOMLChar:
        return self._current

    @property
    def marker(self) -> int:
        return self._marker

    def extract(self) -> str:
        """
        Extracts the value between marker and index
        """
        return self[self._marker : self._idx]

    def inc(self, exception: type[ParseError] | None = None) -> bool:
        """
        Increments the parser if the end of the input has not been reached.
        Returns whether or not it was able to advance.
        """
        # PERF: integer increment + cached TOMLChar lookup, no iterator/next()/
        # StopIteration triage. After the first char of each kind has been seen,
        # `TOMLChar(self[i])` is a dict.get cache hit.
        next_idx = self._idx + 1
        if next_idx < len(self):
            self._idx = next_idx
            self._current = TOMLChar(self[next_idx])
            return True

        # Past end : pin to len, switch current to EOF, raise if asked.
        self._idx = len(self)
        self._current = self.EOF
        if exception:
            raise self.parse_error(exception) from None
        return False

    def advance_while(self, charset: frozenset) -> bool:
        """Advance while the current character is in ``charset``.

        Equivalent to ``while self.current in charset and self.inc(): pass`` but
        it scans the underlying string in a single pass and updates the index
        and current character only once, instead of paying a per-character
        ``inc()`` call. On return ``current`` is the first character NOT in
        ``charset`` (or EOF). Returns ``True`` if it stopped on a real
        character, ``False`` at EOF — the same value contract as the loop.
        """
        i = self._idx
        n = len(self)
        while i < n and self[i] in charset:
            i += 1
        if i < n:
            self._idx = i
            self._current = TOMLChar(self[i])
            return True
        self._idx = n
        self._current = self.EOF
        return False

    def advance_until(self, stopset: frozenset) -> bool:
        """Advance while the current character is NOT in ``stopset``.

        The mirror of :meth:`advance_while`: equivalent to
        ``while self.current not in stopset and self.inc(): pass`` in a single
        scan. On return ``current`` is the first character IN ``stopset`` (or
        EOF), with the same return-value contract.
        """
        i = self._idx
        n = len(self)
        while i < n and self[i] not in stopset:
            i += 1
        if i < n:
            self._idx = i
            self._current = TOMLChar(self[i])
            return True
        self._idx = n
        self._current = self.EOF
        return False

    def inc_n(self, n: int, exception: type[ParseError] | None = None) -> bool:
        """
        Increments the parser by n characters
        if the end of the input has not been reached.
        """
        return all(self.inc(exception=exception) for _ in range(n))

    def consume(self, chars: str, min: int = 0, max: int = -1) -> None:
        """
        Consume chars until min/max is satisfied is valid.
        """
        while self.current in chars and max != 0:
            min -= 1
            max -= 1
            if not self.inc():
                break

        # failed to consume minimum number of characters
        if min > 0:
            raise self.parse_error(UnexpectedCharError, self.current)

    def end(self) -> bool:
        """
        Returns True if the parser has reached the end of the input.
        """
        return self._current is self.EOF

    def mark(self) -> None:
        """
        Sets the marker to the index's current position
        """
        self._marker = self._idx

    def parse_error(
        self,
        exception: type[ParseError] = ParseError,
        *args: Any,
        **kwargs: Any,
    ) -> ParseError:
        """
        Creates a generic "parse error" at the current position.
        """
        line, col = self._to_linecol()

        return exception(line, col, *args, **kwargs)

    def _to_linecol(self) -> tuple[int, int]:
        cur = 0
        for i, line in enumerate(self.splitlines()):
            if cur + len(line) + 1 > self.idx:
                return (i + 1, self.idx - cur)

            cur += len(line) + 1

        return len(self.splitlines()), 0
