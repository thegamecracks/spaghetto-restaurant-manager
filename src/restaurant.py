from .business import Business
from .dishmenu import DishMenu


class Restaurant(Business):
    """
    Args:
        dishes (Optional[List[Dish]]):
            The list of dishes.

    """
    def __init__(self, balance=None, inventory=None,
                 dishes=None, transactions=None):
        super().__init__(balance=balance, inventory=inventory,
                         transactions=transactions)
        if dishes is None:
            dishes = []
        self.dishes = dishes

    @classmethod
    def _from_dict_deserialize(cls, d):
        d = super()._from_dict_deserialize(d)
        dishes = d.get('dishes')
        if dishes is not None:
            d['dishes'] = DishMenu.from_list(dishes)
        return d
