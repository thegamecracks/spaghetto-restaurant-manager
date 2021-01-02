from dataclasses import dataclass, field, replace, asdict
import decimal

from .item import Item

__all__ = ['InventoryItemEntry']


@dataclass
class InventoryItemEntry:
    """An entry in InventoryItem.
    `price` is stored as the unit price.
    """
    quantity: int = field(hash=False)
    price: decimal.Decimal

    def __post_init__(self):
        self.price = decimal.Decimal(self.price)

    def copy(self, **kwargs):
        return replace(self, **kwargs)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

    @classmethod
    def from_item(cls, item: Item):
        q = item.quantity
        p = item.price / q if q or item.price else 0
        return cls(quantity=q, price=p)
