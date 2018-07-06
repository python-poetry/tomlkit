from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from .items import AoT
from .items import Item
from .items import Key
from .items import Table


class Container:
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
        self._map[key] = len(self._body)

        self._body.append((key, item))

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
