import string


# Intern TOMLChar instances. A document is read one character at a time and
# draws on a tiny alphabet, so the same single-character strings get built over
# and over; caching one instance per character turns each repeat into a dict
# lookup. The cache is bounded by the alphabet seen (a few hundred entries at
# most for typical input).
_TOML_CHAR_CACHE: dict[str, "TOMLChar"] = {}


class TOMLChar(str):
    def __new__(cls, c: str) -> "TOMLChar":
        cached = _TOML_CHAR_CACHE.get(c)
        if cached is not None:
            return cached
        if len(c) > 1:
            raise ValueError("A TOML character must be of length 1")
        instance = super().__new__(cls, c)
        # Never intern the NUL character: Source uses TOMLChar("\0") as its
        # end-of-input sentinel and detects EOF by identity (`current is EOF`).
        # Caching "\0" would make a real U+0000 in the input share that identity,
        # so the parser would treat an embedded NUL as end-of-file instead of
        # rejecting it. Leaving it un-interned keeps EOF a unique sentinel.
        if c != "\0":
            _TOML_CHAR_CACHE[c] = instance
        return instance

    BARE = string.ascii_letters + string.digits + "-_"
    KV = "= \t"
    NUMBER = string.digits + "+-_.e"
    SPACES = " \t"
    NL = "\n\r"
    WS = SPACES + NL

    def is_bare_key_char(self) -> bool:
        """
        Whether the character is a valid bare key name or not.
        """
        return self in self.BARE

    def is_kv_sep(self) -> bool:
        """
        Whether the character is a valid key/value separator or not.
        """
        return self in self.KV

    def is_int_float_char(self) -> bool:
        """
        Whether the character if a valid integer or float value character or not.
        """
        return self in self.NUMBER

    def is_ws(self) -> bool:
        """
        Whether the character is a whitespace character or not.
        """
        return self in self.WS

    def is_nl(self) -> bool:
        """
        Whether the character is a new line character or not.
        """
        return self in self.NL

    def is_spaces(self) -> bool:
        """
        Whether the character is a space or not
        """
        return self in self.SPACES
