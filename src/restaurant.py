import collections
import decimal
from dataclasses import dataclass, field
import math
import numbers
import random
from typing import Optional, Dict, Tuple

from .business import Business
from .dishmenu import DishMenu
from .dish import Dish
from .transactiontype import TransactionType

__all__ = ['Restaurant']


@dataclass(order=False)
class Restaurant(Business):
    """
    Args:
        dishes (Optional[DishMenu]):
            The list of dishes.

    """
    dishes: DishMenu = field(default_factory=DishMenu)

    @staticmethod
    def func_popularity(dollars: numbers.Rational) -> float:
        """Generate the popularity of the restaurant on a scale of 100 to 1000.
        f($0) ~= 101
        f($230,000 * 100) ~= 200
        f($400,000 * 100) ~= 301
        f($1,000,000 * 100) ~= 700
        f($1,536,000 * 100) ~= 900
        f($2,000,000 * 100) ~= 966

        This formula is a generalised logistic function where:
            A = 0
            K = 1,000
            C = 1
            Q = 2.15
            B = 3 / 1,250,000
            v = 0.5
        Formula can be found at:
            https://en.wikipedia.org/wiki/Generalised_logistic_function

        Args:
            dollars (numbers.Rational): The business's balance in dollars.

        Returns:
            float

        """
        dollars = float(dollars)
        popularity = 1000 / (1 + 2.15 * math.e ** (-(3 / 1250000) * dollars)) ** 2
        return max(100., popularity)

    def cost_of_dish(self, dish: Dish, n: int, average=False,
                     lowest_first=True):
        """Return the cost it takes to create some number of this dish.

        Args:
            dish (Dish): The dish to get the cost of its ingredients.
            n (int): The number of this dish.
            average (bool): If True, uses the average costs of
                the dish's items in the inventory.
            lowest_first (bool): If True and `average` is False,
                uses the cheapest purchases in inventory first.

        Returns:
            decimal.Decimal

        Raises:
            ValueError: Either n is greater than the quantity of one of
                the inventory items; a requirement is missing from
                the inventory; or one of the inventory items was empty/missing.

        """
        cost = decimal.Decimal()

        for i in dish.items:
            try:
                inv_item = self.inventory[i.name]
            except KeyError as e:
                raise ValueError(f'Item {i!r} does not exist in inventory') from e

            if average:
                try:
                    cost += inv_item.price / inv_item.quantity * i.quantity
                except (ZeroDivisionError, decimal.InvalidOperation) as e:
                    raise ValueError(
                        f'Inventory item was empty: {inv_item!r}') from e
            else:
                cost += inv_item.cost_of(n, lowest_first=lowest_first)

        return n * cost

    def generate_metadata(self):
        super().generate_metadata()
        if self.metadata.get('popularity') is None:
            self.update_popularity()

    def on_next_month(self):
        super().on_next_month()
        self.update_sales()
        self.update_expenses()

    def sell_dish(self, dish: Dish, quantity=1, *, simulate=False) \
            -> Optional[decimal.Decimal]:
        """Try subtracting a dish's items from inventory and update the
        dish's expenses.

        Args:
            dish (Dish)
            quantity (int): The number of the dish to try selling.
            simulate (bool): If True, this will not affect the
                business's inventory.

        Returns:
            decimal.Decimal: The total value of the ingredients consumed.
            None: The inventory does not have enough items.

        """
        def get_expense_item(dish, inv_item):
            # Do linear search to find item
            for item in dish.expenses_items:
                if item.name == inv_item.name:
                    return item
            raise ValueError(f'Expense Item {inv_item.name!r} was missing '
                             f'from dish {dish!r}')

        items = []
        for i in dish.items:
            inv_item = self.inventory.get(i.name)
            n = i.quantity * quantity
            if inv_item is None or inv_item.quantity < n:
                return
            items.append((i, inv_item, n))

        total = decimal.Decimal()
        for i, inv_item, n in items:
            if simulate:
                total += inv_item.cost_of(n)
            else:
                value = inv_item.subtract(n)
                total += value
                # Include in dish expenses
                item = get_expense_item(dish, inv_item)
                item.price += value

        return total

    def update_popularity(self):
        old = self.metadata.get('popularity')
        new = self.func_popularity(self.balance)

        final = new
        if old is not None:
            # Linearly interpolate by 10%
            final = old + (new - old) * 0.1

        self.metadata['popularity'] = final
        return final

    def update_expenses(self) -> Tuple[decimal.Decimal, decimal.Decimal]:
        """Update the expenses of all dishes using their current sales.

        This will subtract the required ingredients for each dish
        from the inventory and update their `expenses_items` attribute,
        and add the sum of each dish's revenue to the balance.

        If there is not enough inventory for a particular dish,
        the `sales` will be updated to match what could be sold.
        Requirements are distributed evenly across the dishes so two
        dishes with the same requirements won't cause one to have 0 sales.

        Returns:
            Tuple[decimal.Decimal, decimal.Decimal]:
                The sum of revenue and the total value
                of the ingredients consumed.

        """
        sales: Dict[Dish, int] = collections.Counter()
        for d in self.dishes:
            d: Dish
            sales[d] = d.sales
            d.expenses_items = [i.copy(price=0) for i in d.items]

        expenses = revenue = decimal.Decimal()
        while any(s > 0 for s in sales.values()):
            insufficient = []

            for k, v in sales.items():
                cost = self.sell_dish(k)

                if cost is not None:
                    sales[k] -= 1
                    expenses += cost
                    revenue += k.price
                else:
                    # Cannot sell any more of this dish
                    k.sales -= v
                    insufficient.append(k)

            for dish in insufficient:
                del sales[dish]

        self.deposit('Dish Sales', revenue, TransactionType.SALES)

        return revenue, expenses

    def update_sales(self, none_only=False) -> int:
        """Update the sales of all dishes.

        Args:
            none_only (bool): If True, only dishes with a revenue
                of None are updated. This should be used for adding
                revenue data to new dishes.

        Returns:
            int: The number of dishes updated.

        """
        popularity = min(5., self.update_popularity() / 200 + 0.5)
        open_hours = 8
        num_dishes = len(self.dishes)
        randomness = random.uniform(0.81, 0.86)

        i = 0
        dish: Dish
        for dish in self.dishes:
            if none_only and dish.sales is not None:
                continue
            dollars = float(dish.price)
            # Artificially reduce price if it's a few cents below the dollar
            # by rounding down to the nearest 0.50
            dollars = int(dollars * 2) / 2
            # Factor in the popularity of the business with a
            # quadratic equation
            pop_factor = -0.6 * (popularity - 5) ** 2 + 115
            hour_factor = (open_hours + 171) / 180
            # Factor in the cost of the materials needed to create the item
            # with a logistic function
            try:
                cost_price_ratio = float(
                    self.cost_of_dish(dish, 1, average=True) / dish.price)
            except ValueError:
                cost_price_ratio = 0.
            cost_factor = 0.2 / (1 + math.e ** (-20 * cost_price_ratio)) - 0.1
            # Decaying exponential function
            dish.sales = int(
                ((1 + cost_factor - 1 / 2000 * dollars) ** (
                    -dollars + hour_factor * pop_factor * randomness
                    + 4 * cost_price_ratio
                ) - dollars) / num_dishes
            )
            i += 1

        return i

    @classmethod
    def _from_dict_deserialize(cls, d: dict):
        d = super()._from_dict_deserialize(d)
        dishes = d.get('dishes')
        if dishes is not None:
            d['dishes'] = DishMenu.from_list(dishes)
        return d
