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

    def generate_metadata(self):
        if self.metadata.get('popularity') is None:
            self.update_popularity()

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

    def step(self, *, weeks: int):
        """Step the business by N weeks.
        Every new month, dishes are sold, updating the business's balance
        and all dishes' sales and expenses.
        """
        if weeks < 0:
            raise ValueError(f'weeks ({weeks}) cannot be negative')

        year, month = self.year, self.month
        while weeks > 0:
            change = min(weeks, 4 - self.week)
            self.total_weeks += change
            weeks -= change

            new_year, new_month = self.year, self.month

            if new_month > month:
                self.update_sales()
                self.update_expenses()

            year, month = new_year, new_month

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

        self.balance += revenue
        self.add_transaction('Dish Sales', revenue)

        return revenue, expenses

    def update_sales(self, none_only=False) -> int:
        """Update the sales of all dishes.

        Pro tips (based on the current equations):
            The optimal dish price is $10.47.
            Dishes priced at $65.17 or over will attract 0 customers.

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
        for dish in self.dishes:
            if none_only and dish.sales is not None:
                continue
            dollars = float(dish.price)
            # Quadratic equation in vertex form
            pop_factor = -0.6 * (popularity - 5) ** 2 + 115
            hour_factor = (open_hours + 171) / 180
            # Decaying exponential function
            dish.sales = round(
                (1.1 ** (-dollars + hour_factor * pop_factor * randomness)
                 - dollars) / num_dishes
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
