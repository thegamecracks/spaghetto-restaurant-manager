from typing import Optional, Union

from .cliutils import input_boolean, input_integer, input_money, is_integer
from .dish import Dish
from .inventoryitem import InventoryItem
from .item import Item
from .inventory import Inventory
from .manager import (Manager, ManagerCLIBase, ManagerCLIMain,
                      ManagerCLISubCMDBase)
from .restaurant import Restaurant
from . import utils

__all__ = ['RestaurantManager']


class RestaurantManager(Manager):
    """A manager for a restaurant."""
    _TYPE = Restaurant
    business: Restaurant

    def __init__(self, business: Restaurant, *args, **kwargs):
        super().__init__(business, *args, **kwargs)

    def describe_dish(self, dish: Dish) -> str:
        cost = self.business.cost_of_dish(dish, 1, average=True, default=None)
        if cost is not None:
            cost = utils.format_dollars(cost)
        else:
            cost = 'N/A; Missing ingredients'

        description = (
            'Price: {price}\n'
            'Average cost to produce: {cost}\n'
        ).format(
            price=utils.format_dollars(dish.price),
            cost=cost
        )

        if dish.sales is not None:
            revenue = dish.revenue
            expenses = dish.expenses
            description += (
                "Last month's sales: {sales}\n"
                'Revenue: {revenue}\n'
                'Expenses: {expenses}\n'
                'Profit: {profit}\n'
            ).format(
                sales=dish.sales,
                revenue=utils.format_dollars(revenue),
                expenses=utils.format_dollars(expenses),
                profit=utils.format_dollars(revenue - expenses)
            )
        else:
            description += "Last month's sales: N/A\n"

        if dish.items:
            description += 'Ingredients:\n- ' + '\n- '.join([
                str(i) for i in dish.items])

        return description.rstrip()

    def describe_invitem(self, item: InventoryItem) -> str:
        """Return a string describing a given inventory item.

        Args:
            item (InventoryItem)

        Returns:
            str

        """
        description = super().describe_invitem(item) + '\n'

        dishes = [
            d for d in self.business.dishes
            if item.name in (i.name for i in d.items)
        ]

        if dishes:
            description += 'Used in {:,} {}:\n'.format(
                len(dishes), utils.plural('dish', len(dishes)))
            description += '- ' + '\n- '.join([str(d) for d in dishes])

        return description.rstrip()

    def dish_mapping(self) -> dict:
        """Returns a mapping of indices to dishes.
        1: Dark, Rich, Hearty Roast Coffee
        ... """
        return {i: dish for i, dish in enumerate(self.business.dishes, start=1)}

    def add_dish(self, *args, **kwargs) -> Dish:
        """Helper function for adding a dish."""
        dish = Dish(*args, **kwargs)
        self.business.dishes.add(dish)
        return dish

    def remove_dish(self, dish: Dish):
        """Remove a dish from the restaurant."""
        self.business.dishes.remove(dish.name)

    def get_dish(self, s: Union[int, str]) -> Dish:
        """Lookup a Dish by index or name.

        Args:
            s (Union[int, str])

        Returns:
            Dish
            None

        """
        # Lookup by index
        try:
            index = int(s)
        except ValueError:
            pass
        else:
            return self.dish_mapping().get(index)

        # Fuzzy lookup by name
        return self.business.dishes.find(s)

    def run(self):
        """Start the user interface."""
        self.setup_business()

        RestaurantManagerCLIMain(self).cmdloop()


class RestaurantManagerCLIBase(ManagerCLIBase):
    def __getattr__(self, item: str):
        """When cmd.Cmd is getting help_* methods, replace 'business' with 'restaurant'
        in the docstrings."""

        def fallback():
            raise AttributeError('type {!r} has no attribute {!r}'.format(
                self.__class__.__name__, item
            )) from None

        target = 'business'
        replacement = 'restaurant'

        if item.startswith('help_'):
            funcname = f'do_{item[5:]}'
            func = getattr(self, funcname, None)
            if func is None:
                return fallback()
            doc = func.__doc__
            if doc is None:
                return fallback()

            def help_():
                print(utils.case_preserving_replace(doc, target, replacement))

            return help_
        else:
            return fallback()


class RestaurantManagerCLIMain(RestaurantManagerCLIBase, ManagerCLIMain):
    manager: RestaurantManager

    def do_dishes(self, arg):
        """View the business's dishes."""
        RestaurantManagerCLIDishes(self.manager).cmdloop()
        self.cmdqueue.append('help')


class RestaurantManagerCLIDishes(RestaurantManagerCLIBase, ManagerCLISubCMDBase):
    doc_header = 'Dish Management'

    manager: RestaurantManager

    @staticmethod
    def print_dish_not_found(arg):
        if is_integer(arg):
            return print('That index does not exist!')
        else:
            return print('Could not find a matching name for that dish.')

    def input_dish(self, prompt: str, *, cancellable=False) -> Optional[Dish]:
        """Prompt the user for an existing dish.

        Args:
            prompt (str): The initial message to show the user.
            cancellable (bool): Whether the user can cancel the prompt or not.

        Returns:
            Dish
            None: if `cancellable` and user inputs nothing.

        """
        if cancellable:
            prompt += '(type nothing to cancel) '

        arg = input(prompt).strip()
        dish = self.manager.get_dish(arg)
        while dish is None:
            if not arg and cancellable:
                return
            arg = input('Could not find that dish: ').strip()
            dish = self.manager.get_dish(arg)
        return dish

    def do_add(self, arg):
        """Add a new dish to the menu."""

        def input_item():
            """Get an item from the user."""
            existing_names = frozenset(it.name for it in requirements)
            # Get item name
            end = 'cancel' if i == 1 else 'finish'
            item_name = input(f'Item #{i} (type nothing to {end}): ').strip()
            while item_name in existing_names:
                input('You have already entered that item: ').strip()
            if not item_name:
                return None

            # Get Item object if it exists
            inv_item = inv.get(item_name)
            if inv_item is not None:
                unit = inv_item.unit
            else:
                # Create new item in inventory
                unit = input('What unit is this item measured in? '
                             '(gram, millilitre, cup...)\n'
                             '(type nothing to redo): ').strip()
                if not unit:
                    return False
                inv_item = Item(item_name, 0, unit)
                inv.add(inv_item)

            quantity = input_integer(
                f'How much of this item is required? ({utils.plural(unit)})\n'
                f'(type nothing to redo): ',
                minimum=0, default=0
            )
            if not quantity:
                return False

            # Create Item
            return Item(item_name, quantity, unit)

        def cancel():
            print('Cancelled creation.')

        business = self.manager.business
        inv: Inventory = business.inventory

        name = input('What is the name of your new dish? ').strip()
        if not name:
            return cancel()

        # Input items
        requirements = []
        print('What items does your dish use?')
        i = 1
        item = input_item()
        while item is not None:
            if isinstance(item, Item):
                requirements.append(item)
                i += 1
            item = input_item()
        if item is None and i == 1:
            return cancel()

        dish = Dish(name, items=requirements)
        cost = business.cost_of_dish(dish, 1, average=True, default=None)
        if cost is not None:
            print('Estimated cost of dish (based on current inventory):',
                  utils.format_dollars(cost))
        dish.price = input_money('How much should this dish cost? $', minimum=0)

        # Add dish
        business.dishes.add(dish)
        print('Your dish has been created!')

    def do_list(self, arg):
        """List the dishes on the menu."""
        if not self.manager.business.dishes:
            return print('Your menu currently has no dishes.')

        print('Menu:')
        for i, dish in self.manager.dish_mapping().items():
            print(f'{i:,}: {dish}')

    def do_remove(self, arg):
        """Remove a dish by name.
Usage: remove [name_or_index]"""
        if not self.manager.business.dishes:
            return print('Your menu currently has no dishes.')

        arg = arg.strip()

        if arg:
            # User supplied argument
            dish = self.manager.get_dish(arg)
            if dish is None:
                return self.print_dish_not_found(arg)
        else:
            # Prompt user for dish
            dish = self.input_dish(
                "What is the dish you want to remove? ", cancellable=True)
            if dish is None:
                return print('Cancelled deletion.')

        print(dish.name)
        if input_boolean('Are you sure you want to delete this dish? (y/n) '):
            self.manager.remove_dish(dish)
            print('Deleted dish!')
        else:
            print('Cancelled deletion.')

    def do_show(self, arg):
        """Show the requirements for a dish.
Usage: show [name_or_index]"""
        business = self.manager.business
        if not business.dishes:
            return print('Your menu currently has no dishes.')

        arg = arg.strip()

        if arg:
            # User supplied argument
            dish = self.manager.get_dish(arg)
            if dish is None:
                return self.print_dish_not_found(arg)
        else:
            # Prompt user for dish
            dish = self.input_dish(
                "What is the dish you want to show? ", cancellable=True)
            if dish is None:
                return print('Cancelled.')

        print(dish)
        print(self.manager.describe_dish(dish))
