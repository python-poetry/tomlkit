from __future__ import unicode_literals

from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from ._compat import decode
from .exceptions import KeyAlreadyPresent
from .exceptions import NonExistentKey
from .items import AoT
from .items import Comment
from .items import Item
from .items import Key
from .items import Null
from .items import Table
from .items import Whitespace
from .items import item as _item


class Container(dict):
    """
    A container for items within a TOMLDocument.
    """

    def __init__(self, parsed=False):  # type: (bool) -> None
        self._map = {}  # type: Dict[Key, int]
        self._body = []  # type: List[Tuple[Optional[Key], Item]]
        self._parsed = parsed

    @property
    def body(self):  # type: () -> List[Tuple[Optional[Key], Item]]
        return self._body

    @property
    def value(self):  # type: () -> Dict[Any, Any]
        d = {}
        for k, v in self._body:
            if k is None:
                continue

            k = k.key
            v = v.value

            if isinstance(v, Container):
                v = v.value

            if k in d:
                d[k].update(v)
            else:
                d[k] = v

        return d

    def parsing(self, parsing):  # type: (bool) -> None
        self._parsed = parsing

        for k, v in self._body:
            if isinstance(v, Table):
                v.value.parsing(parsing)
            elif isinstance(v, AoT):
                for t in v.body:
                    t.value.parsing(parsing)

    def add(
        self, key, item=None
    ):  # type: (Union[Key, Item, str], Optional[Item]) -> Item
        """
        Adds an item to the current Container.
        """
        if item is None:
            if not isinstance(key, (Comment, Whitespace)):
                raise ValueError(
                    "Non comment/whitespace items must have an associated key"
                )

            key, item = None, key

        return self.append(key, item)

    def append(self, key, item):  # type: (Key, Item) -> Item
        if not isinstance(key, Key) and key is not None:
            key = Key(key)

        if not isinstance(item, Item):
            item = _item(item)

        if isinstance(item, (AoT, Table)) and item.name is None:
            item.name = key.key

        if (
            isinstance(item, Table)
            and self._body
            and not self._parsed
            and not item.trivia.indent
        ):
            item.trivia.indent = "\n"

        if isinstance(item, AoT) and self._body and not self._parsed:
            if item and "\n" not in item[0].trivia.indent:
                item[0].trivia.indent = "\n" + item[0].trivia.indent
            else:
                self.append(None, Whitespace("\n"))

        if key is not None and key in self:
            current = self._body[self._map[key]][1]
            if isinstance(item, Table):
                if not isinstance(current, (Table, AoT)):
                    raise KeyAlreadyPresent(key)

                if item.is_aot_element():
                    # New AoT element found later on
                    # Adding it to the current AoT
                    if not isinstance(current, AoT):
                        current = AoT([current, item], parsed=self._parsed)

                        self._replace(key, key, current)
                    else:
                        current.append(item)

                    return item
                elif current.is_super_table():
                    if item.is_super_table():
                        for k, v in item.value.body:
                            current.append(k, v)

                        return current
                else:
                    raise KeyAlreadyPresent(key)
            elif isinstance(item, AoT):
                if not isinstance(current, Table):
                    raise KeyAlreadyPresent(key)

                if not current.is_super_table():
                    raise KeyAlreadyPresent(key)

                item_table = item.body[0]

                if not item_table.is_super_table():
                    raise KeyAlreadyPresent(key)
            else:
                raise KeyAlreadyPresent(key)

        if key is not None:
            super(Container, self).__setitem__(key.key, item.value)

        is_table = isinstance(item, (Table, AoT))
        if key is not None and self._body and not self._parsed:
            # If there is already at least one table in the current container
            # an the given item is not a table, we need to find the last
            # item that is not a table and insert after it
            # If not such item exists, insert at the top of the table
            key_after = None
            idx = 0
            for k, v in self._body:
                if isinstance(v, (Whitespace, Null)) and not v.is_fixed():
                    continue

                if not is_table and isinstance(v, (Table, AoT)):
                    break

                key_after = k or idx
                idx += 1

            if key_after is not None:
                if isinstance(key_after, int):
                    if key_after + 1 < len(self._body) - 1:
                        return self._insert_at(key_after + 1, key, item)
                else:
                    return self._insert_after(key_after, key, item)
            else:
                return self._insert_at(0, key, item)

        self._map[key] = len(self._body)

        self._body.append((key, item))

        return item

    def remove(self, key):  # type: (Key) -> None
        if not isinstance(key, Key):
            key = Key(key)

        idx = self._map.pop(key, None)
        if idx is None:
            raise NonExistentKey(key)

        self._body[idx] = (None, Null())

        super(Container, self).__delitem__(key.key)

    def _insert_after(
        self, key, other_key, item
    ):  # type: (Union[str, Key], Union[str, Key], Union[Item, Any]) -> Item
        if key is None:
            raise ValueError("Key cannot be null in insert_before()")

        if key not in self:
            raise NonExistentKey(key)

        if not isinstance(key, Key):
            key = Key(key)

        if not isinstance(other_key, Key):
            other_key = Key(other_key)

        item = _item(item)

        idx = self._map[key]

        # Increment indices after the current index
        for k, v in self._map.items():
            if v > idx:
                self._map[k] = v + 1

        self._map[other_key] = idx + 1
        self._body.insert(idx + 1, (other_key, item))

        return item

    def _insert_at(
        self, idx, key, item
    ):  # type: (int, Union[str, Key], Union[Item, Any]) -> Item
        if idx > len(self._body) - 1:
            raise ValueError("Unable to insert at position {}".format(idx))

        if not isinstance(key, Key):
            key = Key(key)

        item = _item(item)

        # Increment indices after the current index
        for k, v in self._map.items():
            if v >= idx:
                self._map[k] = v + 1

        self._map[key] = idx
        self._body.insert(idx, (key, item))

        return item

    def item(self, key):  # type: (Key) -> Item
        if not isinstance(key, Key):
            key = Key(key)

        idx = self._map.get(key, None)
        if idx is None:
            raise NonExistentKey(key)

        return self._body[idx][1]

    def last_item(self):  # type: () -> Optional[Item]
        if self._body:
            return self._body[-1][1]

    def as_string(self, prefix=None):  # type: () -> str
        s = ""
        for k, v in self._body:
            if k is not None:
                if isinstance(v, Table):
                    if v.is_super_table():
                        if k.is_dotted():
                            key = k.as_string()

                            for _k, _v in v.value.body:
                                if isinstance(_v, Table):
                                    s += v.as_string(prefix=key)
                                else:
                                    _key = key
                                    if prefix is not None:
                                        _key = prefix + "." + _key

                                    s += "{}{}{}{}{}{}{}".format(
                                        _v.trivia.indent,
                                        _key + "." + decode(_k.as_string()),
                                        _k.sep,
                                        decode(_v.as_string()),
                                        _v.trivia.comment_ws,
                                        decode(_v.trivia.comment),
                                        _v.trivia.trail,
                                    )
                        else:
                            s += v.as_string(prefix=k.as_string())

                        continue

                    if v.display_name is not None:
                        key = v.display_name
                    else:
                        key = k.as_string()

                        if prefix is not None:
                            key = prefix + "." + key

                    open_, close = "[", "]"
                    if v.is_aot_element():
                        open_, close = "[[", "]]"

                    cur = "{}{}{}{}{}{}{}{}".format(
                        v.trivia.indent,
                        open_,
                        decode(key),
                        close,
                        v.trivia.comment_ws,
                        decode(v.trivia.comment),
                        v.trivia.trail,
                        v.as_string(prefix=key),
                    )
                elif isinstance(v, AoT):
                    key = k.as_string()
                    if prefix is not None:
                        key = prefix + "." + key

                    cur = ""
                    key = decode(key)
                    for table in v.body:
                        if table.is_super_table():
                            cur += table.as_string(prefix=key)
                        else:
                            cur += "{}[[{}]]{}{}{}".format(
                                table.trivia.indent,
                                key,
                                table.trivia.comment_ws,
                                decode(table.trivia.comment),
                                table.trivia.trail,
                            )
                            cur += table.as_string(prefix=key)
                else:
                    cur = "{}{}{}{}{}{}{}".format(
                        v.trivia.indent,
                        decode(k.as_string()),
                        k.sep,
                        decode(v.as_string()),
                        v.trivia.comment_ws,
                        decode(v.trivia.comment),
                        v.trivia.trail,
                    )
            else:
                cur = v.as_string()

            s += cur

        return s

    # Dictionary methods

    def keys(self):  # type: () -> Generator[Key]
        for k, _ in self._body:
            if k is None:
                continue

            yield k.key

    def values(self):  # type: () -> Generator[Item]
        for k, v in self._body:
            if k is None:
                continue

            yield v.value

    def items(self):  # type: () -> Generator[Item]
        for k, v in self.value.items():
            if k is None:
                continue

            yield k, v

    def __contains__(self, key):  # type: (Key) -> bool
        if not isinstance(key, Key):
            key = Key(key)

        return key in self._map

    def __getitem__(self, key):  # type: (Key) -> Item
        if not isinstance(key, Key):
            key = Key(key)

        idx = self._map.get(key, None)
        if idx is None:
            raise NonExistentKey(key)

        item = self._body[idx][1]
        value = item.value

        return value

    def __setitem__(self, key, value):  # type: (Union[Key, str], Any) -> None
        if key is not None and key in self:
            self._replace(key, key, value)
        else:
            self.append(key, value)

    def __delitem__(self, key):  # type: (Union[Key, str]) -> None
        self.remove(key)

    def _replace(self, key, new_key, value):  # type: (Key, Key, Item) -> None
        if not isinstance(key, Key):
            key = Key(key)

        if not isinstance(new_key, Key):
            new_key = Key(new_key)

        idx = self._map.get(key, None)
        if idx is None:
            raise NonExistentKey(key)

        self._replace_at(idx, new_key, value)

    def _replace_at(self, idx, new_key, value):  # type: (int, Key, Item) -> None
        k, v = self._body[idx]

        self._map[new_key] = self._map.pop(k)

        value = _item(value)

        # Copying trivia
        if not isinstance(value, (Whitespace, AoT)):
            value.trivia.indent = v.trivia.indent
            value.trivia.comment_ws = v.trivia.comment_ws
            value.trivia.comment = v.trivia.comment
            value.trivia.trail = v.trivia.trail

        self._body[idx] = (new_key, value)

        super(Container, self).__setitem__(new_key.key, value.value)

    def __str__(self):  # type: () -> str
        return str(self.value)

    def __eq__(self, other):  # type: (Dict) -> bool
        if not isinstance(other, dict):
            return NotImplemented

        return self.value == other
