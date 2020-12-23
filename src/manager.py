"""This provides the base class for interfacing with a Business.
The base class comes with a minimal CLI."""
import cmd
import traceback

from . import utils
from .business import Business
from .inventory import Inventory
from .item import Item

__all__ = ['Manager']


def input_boolean(prompt):
    def parse(s):
        if s in ('yes', 'y'):
            return True
        elif s in ('no', 'n'):
            return False
        return None

    ans = input(prompt).lower().strip()
    meaning = parse(ans)

    while meaning is None:
        ans = input('Unknown answer: ').lower().strip()
        meaning = parse(ans)

    return meaning


def input_integer(prompt, minimum=None, maximum=None):
    """

    Args:
        prompt (str): The initial message to prompt the user.
        minimum (Optional[int]): The minimum value in cents (inclusive).
        maximum (Optional[int]): The maximum value in cents (inclusive).

    """
    def parse(s):
        try:
            s = int(s)
        except ValueError:
            return 'Unknown integer: '
        if minimum is not None and s < minimum:
            return f'Must be above {minimum:,}: '
        elif maximum is not None and s > maximum:
            return f'Must be below {maximum:,}: '
        return s

    result = parse(input(prompt))
    while isinstance(result, str):
        result = parse(input(result))
    return result


def parse_decimal(s: str):
    """Parse a decimal number into its whole and decimal parts.

    Returns:
        Tuple[int, int]

    """
    # Find the decimal point (and assert there aren't multiple points)
    point = s.find('.')
    if point == -1:
        point = len(s)
    elif s.count('.') > 1:
        raise ValueError('Too many decimal points')

    # Separate the whole and decimal part ("3", "14"),
    whole, decimal = s[:point], s[point+1:]
    whole = whole if whole else 0
    decimal = decimal if decimal else 0

    # Parse into integers and return them as a tuple
    return int(whole), int(decimal)


def input_money(prompt, minimum=None, maximum=None):
    """Accurately parse a decimal number in dollars into cents.

    Args:
        prompt (str)
        minimum (Optional[int]): The minimum value in cents (inclusive).
        maximum (Optional[int]): The maximum value in cents (inclusive).

    Returns:
        int

    """
    def parse(s):
        try:
            whole, decimal = parse_decimal(s)
        except ValueError:
            return 'Could not parse your amount: $'
        cents = whole * 100 + decimal
        if minimum is not None and cents < minimum:
            return f'Must be above {minimum:,}: $'
        elif maximum is not None and cents > maximum:
            return f'Must be below {maximum:,}: $'
        return cents

    result = parse(input(prompt))
    while isinstance(result, str):
        result = parse(input(result))
    return result


class ManagerCLIMain(cmd.Cmd):
    intro = ''  # Message when shell is opened
    prompt_default = '> '
    prompt = prompt_default  # Input prompt

    ruler = '='  # Used for help message headers
    doc_leader = ''  # Printed before the documentation headers
    doc_header = 'Commands (type help <command>):'
    misc_header = 'Help topics (type help <topic>):'
    undoc_header = 'Undocumented commands'
    nohelp = 'There is no information on "%s".'

    def __init__(self, manager, cmdqueue=None):
        super().__init__()
        self.manager = manager

        if cmdqueue is None:
            cmdqueue = ['help']
        self.cmdqueue = cmdqueue

        self.do_help.__func__.__doc__ = (
            'List available commands or get detailed information about a command/topic.\n'
            'Usage: help [cmd/topic]\n'
            'Usage: ?[cmd/topic]'
        )

    def print(self, *args, **kwargs):
        print(*args, file=self.stdout, **kwargs)

    # ===== Commands =====
    def do_balance(self, arg):
        """Display your business's balance."""
        balance = self.manager.business.balance
        self.print(f"Your business's balance is {utils.cents_string(balance)}.")

    def do_exit(self, arg):
        """Exit the program."""
        if input_boolean('Would you like to save your data before exiting? '
                         '(y/n) '):
            self.do_save(arg)
        return True

    def do_inventory(self, arg):
        """Interact with your business's inventory.
        WIP: This currently only prints the inventory of the business."""
        # TODO: make another Cmd for this
        print('Inventory:')
        for i, item in enumerate(self.manager.business.inventory, start=1):
            print(f'1: {item}')

    def do_save(self, arg):
        """Save your business's data onto disk."""
        try:
            self.manager.save_business()
        except Exception as e:
            print('An error occurred while saving:')
            traceback.print_exception(type(e), e, e.__traceback__)
        else:
            print('Successfully saved!')

    def do_load(self, arg):
        """Load your business's data."""
        try:
            self.manager.reload_business()
        except Exception as e:
            print('An error occurred while loading:')
            traceback.print_exception(type(e), e, e.__traceback__)
        else:
            print('Successfully loaded!')


class Manager:
    def __init__(self, business: Business, filepath: str = None):
        self.business = business
        self.filepath = filepath

    def setup_business(self):
        """Setup the business's balance and inventory if they are None."""
        business = self.business
        if business.balance is None:
            business.balance = input_money(
                "What is your business's current balance? $")
        
        if business.inventory is None:
            print("Let's set up your business's inventory!")
            self.setup_inventory()

    @classmethod
    def from_filepath(cls, filepath):
        with open(filepath, encoding='utf-8') as f:
            business = Business.from_file(f)
        return cls(business, filepath=filepath)

    def setup_inventory(self):
        """Setup the business's inventory."""
        def input_item():
            name = input(f'Item #{item_num:,} name (type nothing to finish): ').strip()
            if not name:
                return

            quantity = input_integer('Quantity: ', minimum=0)
            unit = input('Unit of quantity (gram, mL, cup...): ').strip()
            price = input_money('Total cost of item: $')

            return Item(name, quantity, unit, price)

        inv = Inventory()
        item_num = 1

        item = input_item()
        while item is not None:
            inv.add(item)
            item_num += 1
            item = input_item()

        self.business.inventory = inv

    def save_business(self, filepath=None):
        """Save the business to `filepath`.
        Defaults to `self.filepath` if no filepath is provided."""
        filepath = filepath or self.filepath
        with open(filepath, 'w', encoding='utf-8') as f:
            self.business.to_file(f)

    def reload_business(self, filepath=None):
        """Reload the business's data from `filepath`.
        Defaults to `self.filepath` if no filepath is provided."""
        filepath = filepath or self.filepath
        with open(filepath, encoding='utf-8') as f:
            self.business = type(self.business).from_file(f)

    def run(self):
        """Start the user interface."""
        self.setup_business()

        ManagerCLIMain(self).cmdloop()
