from .item import Item
from . import utils


class Inventory:
    """An inventory of items with unique names.

    Items can be accessed by name:
        >>> inv = Inventory([
        ...     Item('Coffee', 3, 'cup', 750),
        ...     Item('Green Tea', 3, 'cup', 750)
        ... ])
        >>> inv['Coffee']
        Item('Coffee', 3, 'cup', 300)

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
        items (Iterable): An iterable of Item objects.

    """

    _DEFAULT = object()

    def __init__(self, items=()):
        self._items = {i.name: i for i in items}

    def __contains__(self, item):
        return item in self._items

    def __iter__(self):
        return iter(self._items.values())

    def __len__(self):
        return len(self._items)

    def __getitem__(self, item):
        return self._items[item]

    def __repr__(self):
        return '{}({!r})'.format(
            self.__class__.__name__,
            [i for i in self._items]
        )

    def add(self, item):
        """Add an Item to the inventory.

        This has no effect if the item is already present.

        """
        if item.name not in self:
            self._items[item.name] = item

    def discard(self, key: str):
        """Remove an Item from the inventory if it exists, by name.

        If the item does not exist in the inventory, does nothing.

        """
        self._items.pop(key, None)

    def find(self, key: str, default=None) -> Item:
        """Find an item that starts with the given name. Similar to get()."""
        names = list(self._items)
        search = utils.fuzzy_match_word(key, names)
        return self.get(search) if search is not None else None

    def get(self, key: str, default=None) -> Item:
        """Return the value for key if key is in the dictionary, else default.

        Returns:
            Item
            None

        """
        return self._items.get(key, default)

    def pop(self, key, default=_DEFAULT) -> Item:
        """Remove and return an Item from the inventory.
        If key is not found, default is returned if given, else KeyError is raised.

        Returns:
            Item
            `default`

        """
        if default is self._DEFAULT:
            return self._items.pop(key)
        return self._items.pop(key, default)

    def remove(self, key):
        """Remove an Item from the inventory by name.

        If the item does not exist in the inventory, raises KeyError.

        """
        if isinstance(key, str):
            del self._items[key]
        else:
            del self._items[key.name]

    def to_list(self):
        return [v for v in self._items.values()]

    @classmethod
    def from_list(cls, list_):
        return cls(Item.from_dict(d) for d in list_)
