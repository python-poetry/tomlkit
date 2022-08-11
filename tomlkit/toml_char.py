import string

from tomlkit._utils import lru


class TOMLChar(str):
    def __init__(self, c):
        super().__init__()

        if len(self) > 1:
            raise ValueError("A TOML character must be of length 1")

    BARE = string.ascii_letters + string.digits + "-_"
    KV = "= \t"
    NUMBER = string.digits + "+-_.e"
    SPACES = " \t"
    NL = "\n\r"
    WS = SPACES + NL

    @lru
    def is_bare_key_char(self) -> bool:
        """
        Whether the character is a valid bare key name or not.
        """
        return self in self.BARE

    @lru
    def is_kv_sep(self) -> bool:
        """
        Whether the character is a valid key/value separator or not.
        """
        return self in self.KV

    @lru
    def is_int_float_char(self) -> bool:
        """
        Whether the character if a valid integer or float value character or not.
        """
        return self in self.NUMBER

    @lru
    def is_ws(self) -> bool:
        """
        Whether the character is a whitespace character or not.
        """
        return self in self.WS

    @lru
    def is_nl(self) -> bool:
        """
        Whether the character is a new line character or not.
        """
        return self in self.NL

    @lru
    def is_spaces(self) -> bool:
        """
        Whether the character is a space or not
        """
        return self in self.SPACES
