import copy
import decimal
from typing import List, Union, Iterable, Dict

from . import utils
from .inventorybase import InventoryBase
from .inventoryitementry import InventoryItemEntry
from .item import Item

__all__ = ['InventoryItem']


class InventoryItem(InventoryBase):
    """An item designed for use with the inventory.

    This differs from Item in that under the hood, different quantities
    and unit prices are stored in a dictionary and indexed by price,
    allowing the value of the item to be calculated when the quantity changes.

    This object's hash uses its name.

    Args:
        name (str)
        unit (str)
        items (List[InventoryItemEntry])

    """
    _INV_TYPE = InventoryItemEntry
    _items: Dict[decimal.Decimal, InventoryItemEntry]

    def __init__(self, name: str, unit: str,
                 items: Iterable[Union[InventoryItemEntry, Item]] = None):
        self.name = name
        self.unit = unit

        if items is None:
            items = ()

        _items = {}
        for i in items:
            if isinstance(i, Item):
                # Cast to entry
                i = InventoryItemEntry.from_item(i)
            elif not isinstance(i, InventoryItemEntry):
                raise TypeError(
                    f'Expected object of type {InventoryItemEntry.__name__} '
                    f'but received {i!r} of type {type(i).__name__}'
                )
            _items[i.price] = i

        self._items = _items

    def __repr__(self):
        return '{}({!r}, {!r}, {!r})'.format(
            self.__class__.__name__,
            self.name,
            self.unit,
            list(self._items.values())
        )

    def __str__(self):
        return '{q:,} {u} of {n}'.format(
            q=self.quantity,
            u=utils.plural(self.unit, self.quantity),
            n=self.name
        )

    def __hash__(self):
        return hash((self.__class__, self.name))

    def __add__(self, other):
        if isinstance(other, (self.__class__, InventoryItemEntry, Item)):
            new = self.copy()
            new.add(other)
        return NotImplemented

    def __iadd__(self, other):
        if isinstance(other, (self.__class__, InventoryItemEntry, Item)):
            self.add(other)
        else:
            raise TypeError(
                'Cannot add a {0.__name__} to an {1.__name__}'.format(
                    type(other), type(self)
                )
            )
        return self

    def __sub__(self, other):
        if isinstance(other, int):
            new = self.copy()
            new.subtract(other)
            return new
        return NotImplemented

    def __isub__(self, other):
        if isinstance(other, int):
            self.subtract(other)
        else:
            raise TypeError(
                'Cannot subtract a {0.__name__} from an {1.__name__}'.format(
                    type(other), type(self)
                )
            )
        return self

    @property
    def quantity(self):
        return sum(i.quantity for i in self)

    @property
    def price(self):
        return sum(i.quantity * i.price for i in self)

    def add(self, other: Union[InventoryItemEntry, Item]):
        """Add another InventoryItem, InventoryItemEntry, or Item to this."""
        def exc():
            return TypeError(
                'Cannot add a {0.__name__} to an {1.__name__}'.format(
                    type(other), type(self)
                )
            )

        def _add(e):
            """Add an entry and replace any exception from recursive calls
            with a top-level exception."""
            try:
                self.add(e)
            except TypeError:
                raise exc() from None

        if isinstance(other, self.__class__):
            for entry in other._items:
                _add(entry)
        elif isinstance(other, Item):
            if self.name != other.name:
                raise ValueError(f'Cannot add {other.name!r} to {self.name!r}')
            elif self.unit != other.unit:
                raise ValueError(
                    f'Cannot add item using {other.unit!r} units '
                    f'to another in {self.unit!r} units')
            _add(InventoryItemEntry.from_item(other))
        elif isinstance(other, InventoryItemEntry):
            current = self.get(other.price)
            if current is not None:
                # Add to current entry
                current.quantity += other.quantity
            else:
                self._items[other.price] = other
        else:
            raise exc()

    def copy(self):
        return copy.deepcopy(self)

    def cost_of(self, n: int = None, *, lowest_first=True) \
            -> decimal.Decimal:
        """Return the cost of some number of this item.

        If you want an average cost instead of precise inventory costs,
        use self.price / self.quantity.

        Args:
            n (Optional[int]): The amount to get the cost of.
                Defaults to the item's quantity.
            lowest_first (bool): If True, entries with the lowest price
                are used first.

        Returns:
            decimal.Decimal: The total value of n items
                (not rounded to the nearest cent).

        Raises:
            ValueError: n is greater than the quantity of the item.

        """
        if n is None:
            n = self.quantity
        elif n > self.quantity:
            raise ValueError(f'Cannot get cost of {n:,} items with '
                             f'only {self.quantity:,} available')

        entries = sorted(self, key=lambda e: e.price, reverse=not lowest_first)

        value = decimal.Decimal()
        for entry in entries:
            consumed = min(n, entry.quantity)
            n -= consumed
            value += entry.price * consumed

            if n <= 0:
                break

        return value

    def subtract(self, n: int = None, lowest_first=True) -> decimal.Decimal:
        """Subtract from the item's quantity.

        As it subtracts from its entries, if the entry's quantity goes to
        0, it is deleted from InventoryItem.

        Args:
            n (Optional[int]): The amount to subtract from quantity.
                Defaults to the item's quantity.
            lowest_first (bool): If True, entries with the lowest price
                are subtracted from first.

        Returns:
            decimal.Decimal: The total value of the items subtracted
                (not rounded to the nearest cent).

        Raises:
            ValueError: n is greater than the quantity of the item.

        """
        if n is None:
            n = self.quantity
        elif n > self.quantity:
            raise ValueError(
                f'Not enough items to subtract {n:,} from {self.quantity:,}')

        get_entry = min if lowest_first else max

        value = decimal.Decimal()
        while n > 0:
            entry: InventoryItemEntry = get_entry(self, key=lambda e: e.price)

            consumed = min(n, entry.quantity)
            entry.quantity -= consumed
            n -= consumed
            value += entry.price * consumed
            if entry.quantity <= 0:
                del self._items[entry.price]

        return value

    def to_dict(self):
        return {'name': self.name, 'unit': self.unit,
                'items': list(self._items.values())}

    @classmethod
    def from_dict(cls, d: dict):
        name = d.get('name')
        unit = d.get('unit')
        items = d.get('items')
        if items is not None:
            items = [InventoryItemEntry.from_dict(e) for e in items]
        return cls(name, unit, items)

    @classmethod
    def from_item(cls, item: Item):
        return cls(item.name, item.unit, [InventoryItemEntry.from_item(item)])

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
