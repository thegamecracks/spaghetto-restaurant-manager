import decimal
from dataclasses import asdict, dataclass, field
from typing import List

from .item import Item

__all__ = ['Dish']


@dataclass
class Dish:
    """A named dish consisting of items.

    Args:
        name (str)
        items (Optional[List[Item]])
        price (int): The price of the dish.
        sales (Optional[int]): The monthly sales this dish makes.
        expenses_items (Optional[List[Item]]):
            A list of each ingredient with their total cost.

    """
    name: str
    items: List[Item] = field(default_factory=list, hash=False)
    price: decimal.Decimal = field(default=decimal.Decimal(), hash=False)
    sales: int = field(default=None, hash=False)
    expenses_items: List[Item] = field(default_factory=list, hash=False)

    def __post_init__(self):
        for i in self.items:
            i.price = decimal.Decimal()

    def __hash__(self):
        return hash((self.__class__, self.name))

    def __str__(self):
        return self.name

    @property
    def expenses(self):
        return sum(i.price for i in self.expenses_items)

    @property
    def revenue(self):
        return self.price * self.sales

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def _from_dict_deserialize(d: dict):
        items = d.get('items')
        if items is not None:
            d['items'] = [Item.from_dict(i) for i in items]
        expenses_items = d.get('expenses_items')
        if expenses_items is not None:
            d['expenses_items'] = [Item.from_dict(i) for i in expenses_items]
        return d

    @classmethod
    def from_dict(cls, d):
        return cls(**cls._from_dict_deserialize(d))
