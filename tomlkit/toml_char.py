import string

from ._compat import PY2
from ._compat import unicode

if PY2:
    from functools32 import lru_cache
else:
    from functools import lru_cache


class TOMLChar(unicode):
    def __init__(self, c):
        super(TOMLChar, self).__init__()

        if len(self) > 1:
            raise ValueError("A TOML character must be of length 1")

    @lru_cache(maxsize=None)
    def is_bare_key_char(self):  # type: () -> bool
        """
        Whether the character is a valid bare key name or not.
        """
        return self in string.ascii_letters + string.digits + "-" + "_"

    @lru_cache(maxsize=None)
    def is_kv_sep(self):  # type: () -> bool
        """
        Whether the character is a valid key/value separator ot not.
        """
        return self in "= \t"

    @lru_cache(maxsize=None)
    def is_int_float_char(self):  # type: () -> bool
        """
        Whether the character if a valid integer or float value character or not.
        """
        return self in string.digits + "+" + "-" + "_" + "." + "e"

    @lru_cache(maxsize=None)
    def is_ws(self):  # type: () -> bool
        """
        Whether the character is a whitespace character or not.
        """
        return self in " \t\r\n"

    @lru_cache(maxsize=None)
    def is_nl(self):  # type: () -> bool
        """
        Whether the character is a new line character or not.
        """
        return self in "\n\r"

    @lru_cache(maxsize=None)
    def is_spaces(self):  # type: () -> bool
        """
        Whether the character is a space or not
        """
        return self in " \t"
