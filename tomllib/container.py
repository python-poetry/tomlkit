from typing import Dict
from typing import Generator
from typing import List
from typing import Optional
from typing import Tuple

from .exceptions import NonExistentKey
from .items import AoT
from .items import Comment
from .items import Item
from .items import Key
from .items import Null
from .items import Table
from .items import Trivia
from .items import Whitespace


class Container(dict):
    """
    A container for items within a TOMLDocument.
    """

    def __init__(self):  # type: () -> None
        self._map = {}  # type: Dict[Key, int]
        self._body = []  # type: List[Tuple[Optional[Key], Item]]

    @property
    def body(self):  # type: () -> List[Tuple[Optional[Key], Item]]
        return self._body

    def append(self, key, item):  # type: (Key, Item) -> None
        from .api import item as _item

        if not isinstance(key, Key) and key is not None:
            key = Key(key)

        if not isinstance(item, Item):
            item = _item(item)

        self._map[key] = len(self._body)

        self._body.append((key, item))

        return item

    def remove(self, key):  # type: (Key) -> None
        idx = self._map.pop(key, None)
        if idx is None:
            raise NonExistentKey(key)

        self._body[idx] = (None, Null())

    def last_item(self):  # type: () -> Optional[Item]
        if self._body:
            return self._body[-1][1]

    def as_string(self):  # type: () -> str
        s = ""
        for k, v in self._body:
            if k:
                if isinstance(v, Table):
                    open_, close = "[", "]"
                    if v.is_aot_element():
                        open_, close = "[[", "]]"

                    cur = "{}{}{}{}{}{}{}{}".format(
                        v.trivia.indent,
                        open_,
                        k.as_string(),
                        close,
                        v.trivia.comment_ws,
                        v.trivia.comment,
                        v.trivia.trail,
                        v.as_string(),
                    )
                elif isinstance(v, AoT):
                    cur = ""
                    key = k.as_string()
                    for table in v.body:
                        cur += "{}[[{}]]{}{}{}".format(
                            table.trivia.indent,
                            key,
                            table.trivia.comment_ws,
                            table.trivia.comment,
                            table.trivia.trail,
                        )
                        cur += table.as_string()
                else:
                    cur = "{}{}{}{}{}{}{}".format(
                        v.trivia.indent,
                        k.as_string(),
                        k.sep,
                        v.as_string(),
                        v.trivia.comment_ws,
                        v.trivia.comment,
                        v.trivia.trail,
                    )
            else:
                cur = v.as_string()

            s += cur

        return s

    # Helpers

    def comment(self, comment):  # type: (str) -> Comment
        if not comment.strip().startswith("#"):
            comment = "# " + comment

        comment = Comment(Trivia("", "  ", comment))

        self.append(None, comment)

        return comment

    def nl(self):  # type: (str) -> Whitespace
        self.append(None, Whitespace("\n"))

    # Dictionary methods

    def keys(self):  # type: () -> Generator[Key]
        for k, _ in self._body:
            if k is None:
                continue

            yield k

    def values(self):  # type: () -> Generator[Item]
        for _, v in self._body:
            yield v

    def items(self):  # type: () -> Generator[Item]
        for k, v in self._body:
            if k is None:
                continue

            yield k, v

    def __contains__(self, key):  # type: (Key) -> bool
        return key in self._map

    def __getitem__(self, key):  # type: (Key) -> Item
        if not isinstance(key, Key):
            key = Key(key)

        idx = self._map.get(key, None)
        if idx is None:
            raise NonExistentKey(key)

        return self._body[idx][1]

    def __setitem__(self, key, value):  # type: (Union[Key, str], Any) -> None
        if key in self:
            self._replace(key, key, value)
        else:
            self.append(key, value)

    def _replace(self, key, new_key, value):  # type: (Key, Key, Item) -> None
        idx = self._map.get(key, None)
        if idx is None:
            raise NonExistentKey(key)

        self._replace_at(idx, new_key, value)

    def _replace_at(self, idx, new_key, value):  # type: (int, Key, Item) -> None
        self._body[idx] = (new_key, value)
