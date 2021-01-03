from .cliutils import input_boolean, input_integer, input_money
from .dish import Dish
from .item import Item
from .inventory import Inventory
from .manager import (Manager, ManagerCLIBase, ManagerCLIMain,
                      ManagerCLISubCMDBase)
from .restaurant import Restaurant
from . import utils

__all__ = ['RestaurantManager']


def is_integer(s: str) -> bool:
    try:
        int(s)
    except ValueError:
        return False
    return True


class RestaurantManager(Manager):
    """A manager for a restaurant."""
    _TYPE = Restaurant
    business: Restaurant

    def __init__(self, business: Restaurant, *args, **kwargs):
        super().__init__(business, *args, **kwargs)

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

    def get_dish(self, s: str) -> Dish:
        """Lookup a Dish by index or name.

        Args:
            s (str)

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
    manager: RestaurantManager

    def print_dish_not_found(self, arg):
        if is_integer(arg):
            return print('That index does not exist!')
        else:
            return print('That dish name does not exist!\n'
                         '(check capitalization and spelling)')

    def input_dish(self, prompt: str, *, cancellable=False) -> Dish:
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
            # Get item name
            end = 'cancel' if i == 1 else 'finish'
            item_name = input(f'Item #{i} (type nothing to {end}): ').strip()
            if not item_name:
                return print('Cancelled creation.') if i == 1 else None

            # Get Item object if it exists
            inv_item = inv.get(item_name)
            if inv_item is not None:
                unit = inv_item.unit
            else:
                # Create new item in inventory
                unit = input('What unit is this item measured in? '
                             '(gram, mL, cup...) ').strip()
                inv_item = Item(item_name, 0, unit, 0)
                inv.add(inv_item)

            quantity = input_integer('How much of this item is required? '
                                     f'({utils.plural(unit)}) ', minimum=0)

            # Create Item
            return Item(item_name, quantity, unit, 0)

        business = self.manager.business
        inv: Inventory = business.inventory

        name = input('What is the name of your new dish? ').strip()
        if not name:
            return print('Cancelled creation.')

        # Input items
        requirements = []
        print('What items does your dish use?')
        i = 1
        item = input_item()
        while item is not None:
            requirements.append(item)
            i += 1
            item = input_item()

        dish = Dish(name, items=requirements)
        try:
            cost = business.cost_of_dish(dish, 1, average=True)
        except ValueError:
            pass
        else:
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
            if not dish:
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
            if not dish:
                return self.print_dish_not_found(arg)
        else:
            # Prompt user for dish
            dish = self.input_dish(
                "What is the dish you want to show? ", cancellable=True)
            if dish is None:
                return print('Cancelled.')

        try:
            cost = utils.format_dollars(
                business.cost_of_dish(dish, 1, average=True))
        except ValueError:
            cost = 'N/A; Missing ingredients'

        print(dish)
        print('Price:', utils.format_dollars(dish.price))
        print('Average cost to produce:', cost)
        if dish.sales is not None:
            revenue = dish.revenue
            expenses = dish.expenses
            print("Last month's sales:", dish.sales)
            print('Revenue:', utils.format_dollars(revenue))
            print('Expenses:', utils.format_dollars(expenses))
            print('Profit:', utils.format_dollars(revenue - expenses))
        else:
            print("Last month's sales: N/A")
        print('Ingredients:')
        for i in dish.items:
            print(i)
