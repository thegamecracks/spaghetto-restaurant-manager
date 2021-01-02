from .dish import Dish
from .inventory import Inventory


class DishMenu(Inventory):
    """A subclass of Inventory designed for dishes."""
    _INV_TYPE = Dish
