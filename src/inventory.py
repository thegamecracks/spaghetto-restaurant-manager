from typing import Iterable, Union, Dict

from .inventorybase import InventoryBase
from .item import Item
from .inventoryitem import InventoryItem
from . import utils

__all__ = ['Inventory']


class Inventory(InventoryBase):
    """An inventory of items with unique names.

    Items can be accessed by name:
        >>> inv = Inventory([
        ...     Item('Coffee', 3, 'cup', '7.50'),
        ...     Item('Green Tea', 3, 'cup', '7.50')
        ... ])
        >>> inv['Coffee']
        InventoryItem('Coffee', 3, 'cup', Decimal('7.50'))

    Can be iterated through:
        >>> for item in inv:
        ...     print(item.name)
        Coffee
        Green Tea

    And supports some methods similar to sets and dictionaries:
        >>> inv.add(Item('Chocolate Milk', 1, 'cup', 200))  # Add a new item
        >>> inv.add(Item('Coffee', 1, 'cup', 200))  # Add to an existing item
        >>> inv['Coffee']
        Item('Coffee', 4, 'cup', 950)
        >>> inv.remove('Green Tea')  # Remove an existing item
        >>> len(inv)
        2

    Args:
        items (Iterable[Union[InventoryItem, Item]]):
            An iterable of InventoryItem objects.
            Item objects are automatically converted into InventoryItems.

    """
    _DEFAULT = object()
    _INV_TYPE = InventoryItem
    _items: Dict[str, _INV_TYPE]

    def __init__(self, items: Iterable[Union[_INV_TYPE, Item]] = ()):
        _items = {}
        for i in items:
            i = self.cast_to_inv_type(i)
            _items[i.name] = i
        self._items = _items

    def __contains__(self, item):
        return getattr(item, 'name', item) in self._items

    def __delitem__(self, item):
        del self._items[getattr(item, 'name', item)]

    def __getitem__(self, item):
        return self._items[getattr(item, 'name', item)]

    def add(self, item: Union[_INV_TYPE, Item]):
        if item.name not in self:
            self._items[item.name] = self.cast_to_inv_type(item)

    def discard(self, key):
        self._items.pop(getattr(key, 'name', key), None)

    def find(self, key, default=None) -> _INV_TYPE:
        """Find an item that fuzzy matches the given name. Similar to get()."""
        names = list(self._items)
        search = utils.fuzzy_match_word(getattr(key, 'name', key), names)
        return self.get(search, default) if search is not None else default

    def get(self, key, default=None) -> _INV_TYPE:
        return self._items.get(getattr(key, 'name', key), default)

    def pop(self, key, default=_DEFAULT) -> _INV_TYPE:
        if default is self._DEFAULT:
            return self._items.pop(getattr(key, 'name', key))
        return self._items.pop(getattr(key, 'name', key), default)

    def remove(self, key):
        del self._items[getattr(key, 'name', key)]

    def to_list(self):
        return [v for v in self._items.values()]

    @classmethod
    def from_list(cls, list_: list):
        return cls(cls._INV_TYPE.from_dict(d) for d in list_)

    @classmethod
    def cast_to_inv_type(cls, obj) -> _INV_TYPE:
        if isinstance(obj, cls._INV_TYPE):
            return obj
        elif isinstance(obj, Item):
            # Cast to inventory item
            return cls._INV_TYPE.from_item(obj)
        raise TypeError(
            f'Expected object of type {cls._INV_TYPE.__name__} '
            f'but received {obj!r} of type {type(obj).__name__}'
        )
