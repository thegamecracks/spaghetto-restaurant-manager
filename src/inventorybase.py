from abc import ABC, abstractmethod


class InventoryBase(ABC):
    _DEFAULT = object()
    _INV_TYPE = object
    _items: dict

    def __bool__(self):
        return bool(self._items)

    def __contains__(self, item):
        return item in self._items

    def __iter__(self):
        return iter(self._items.values())

    def __len__(self):
        return len(self._items)

    def __getitem__(self, item):
        return self._items[item]

    @abstractmethod
    def add(self, item):
        """Add an item to the inventory.

        This has no effect if the item is already present.

        """

    @classmethod
    @abstractmethod
    def cast_to_inv_type(cls, obj):
        """Cast an object to _INV_TYPE."""
        if isinstance(obj, cls._INV_TYPE):
            return obj
        raise TypeError(
            f'Expected object of type {cls._INV_TYPE.__name__} '
            f'but received {obj!r} of type {type(obj).__name__}'
        )

    def discard(self, key):
        """Remove an item from the inventory if it exists.

        If the item does not exist in the inventory, does nothing.

        """
        self._items.pop(key, None)

    def get(self, key, default=None):
        """Return the value for key if key is in the dictionary, else default."""
        return self._items.get(key, default)

    def pop(self, key, default=_DEFAULT):
        """Remove and return an item from the inventory.
        If key is not found, default is returned if given, else KeyError is raised.

        Returns:
            Item
            `default`

        """
        if default is self._DEFAULT:
            return self._items.pop(key)
        return self._items.pop(key, default)

    def remove(self, key):
        """Remove an item from the inventory.

        If the item does not exist in the inventory, raises KeyError.

        """
        if hasattr(key, 'name'):
            del self._items[key.name]
        else:
            del self._items[key]

    def to_list(self):
        return [v for v in self._items.values()]
