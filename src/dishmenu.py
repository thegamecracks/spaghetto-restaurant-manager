from typing import Dict, Iterable

from .dish import Dish
from .inventory import Inventory

__all__ = ['DishMenu']


class DishMenu(Inventory):
    """A subclass of Inventory designed for dishes."""
    _DEFAULT = object()
    _INV_TYPE = Dish
    _items: Dict[str, _INV_TYPE]

    def __init__(self, items: Iterable[_INV_TYPE] = ()):
        super().__init__(items)

    def add(self, item: _INV_TYPE):
        return super().add(item)

    def discard(self, key: str):
        return super().discard(key)

    def find(self, key: str, default=None) -> _INV_TYPE:
        """Find an item that fuzzy matches the given name. Similar to get()."""
        return super().find(key, default)

    def get(self, key: str, default=None) -> _INV_TYPE:
        return super().get(key, default)

    def pop(self, key: str, default=_DEFAULT) -> _INV_TYPE:
        # Can't use super for this; _DEFAULT is unique to this class
        if default is self._DEFAULT:
            return self._items.pop(key)
        return self._items.pop(key, default)

    @classmethod
    def cast_to_inv_type(cls, obj) -> _INV_TYPE:
        if isinstance(obj, cls._INV_TYPE):
            return obj
        raise TypeError(
            f'Expected object of type {cls._INV_TYPE.__name__} '
            f'but received {obj!r} of type {type(obj).__name__}'
        )
