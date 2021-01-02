import decimal
from dataclasses import asdict, dataclass, field
from typing import List

from .item import Item


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
    price: decimal.Decimal = field(default_factory=decimal.Decimal, hash=False)
    sales: int = field(default=None, hash=False)
    expenses_items: List[Item] = field(default_factory=list, hash=False)

    def __post_init__(self):
        for i in self.items:
            i.price = 0

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

    @classmethod
    def from_dict(cls, d):
        d['items'] = [Item.from_dict(d) for d in d['items']]
        return cls(**d)
