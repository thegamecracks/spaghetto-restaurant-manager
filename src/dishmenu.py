from .dish import Dish
from .inventory import Inventory


class DishMenu(Inventory):
    """A subclass of Inventory designed for dishes."""

    @classmethod
    def from_list(cls, list_):
        return cls(Dish.from_dict(d) for d in list_)
