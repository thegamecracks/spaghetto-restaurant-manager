"""This provides the base class for interfacing with a Business.
The base class comes with a minimal CLI."""
import cmd
import contextlib
import datetime
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


class ManagerCLIBase(cmd.Cmd):
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

    def postcmd(self, stop, line):
        """Called after a command dispatch is finished.
        Prints a message if the business's balance is negative."""
        balance = self.manager.business.balance
        if balance < 0:
            print("Warning: the business's balance is negative! "
                  f'({utils.format_cents(balance)})')
        return stop


class ManagerCLIMain(ManagerCLIBase):
    def do_balance(self, arg):
        """Display your business's balance."""
        balance = self.manager.business.balance
        print(f"Your business's balance is {utils.format_cents(balance)}.")

    def do_exit(self, arg):
        """Exit the program. This automatically saves your data."""
        return True

    def do_inventory(self, arg):
        """Interact with your business's inventory.
        WIP: This currently only prints the inventory of the business."""
        ManagerCLIInventory(self.manager).cmdloop()
        self.cmdqueue.append('help')

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


class ManagerCLIInventory(ManagerCLIBase):
    doc_header = 'Inventory Management'

    def do_back(self, arg):
        """Go back to the main window."""
        return True

    def do_buy(self, arg):
        """Buy an item using the business's balance."""
        business = self.manager.business
        inv = business.inventory

        name = input('What is the name of the item? ').strip()
        item = inv.get(name)

        if item is not None:
            unit = item.unit
        else:
            unit = input('What unit is this item measured in? ')

        quantity = input_integer('How much do you want to buy? ', minimum=0)
        price = input_money(
            'What is the TOTAL cost of this item? $', minimum=0)

        # Create the new item and update the business
        new_item = Item(name, quantity, unit, price)
        business.buy_item(new_item)
        print(f'{new_item} purchased!')

    def do_history(self, arg):
        """Display recent transactions (up to 50 within last 5 days)."""
        transactions = self.manager.business.get_transactions(
            50, after=datetime.timedelta(days=5)
        )

        if not transactions:
            return print('There are no recent transactions.')

        # Determine longest length that cost would be printed for padding
        cents_longest = max(
            len(utils.format_cents(t.cents)) for t in transactions)

        # Print transactions
        for t in transactions:
            local_time = t.timestamp.replace(
                tzinfo=datetime.timezone.utc
            ).astimezone()
            print('{time} : {cents} : {title}'.format(
                time=local_time.strftime('%c (%z)'),
                cents=f"{utils.format_cents(t.cents):{cents_longest}}",
                title=t.title
            ))

    def do_list(self, arg):
        """List the items in your inventory."""
        print('Inventory:')
        for i, item in enumerate(self.manager.business.inventory, start=1):
            print(f'{i:,}: {item}')


class Manager:
    def __init__(self, business: Business, filepath: str = None):
        self.business = business
        self.filepath = filepath

    @contextlib.contextmanager
    def start_transaction(self):
        """This is a context manager that can be used to automatically
        save the business data when exiting the context.

        Usage:
            >>> with manager.start_transaction():
            ...     manager.run()

        """
        try:
            yield self
        finally:
            self.save_business()

    def setup_business(self):
        """Setup the business's balance and inventory if they are None."""
        business = self.business
        if business.balance is None:
            business.balance = input_money(
                "What is your business's current balance? $")
        
        if business.inventory is None:
            print("Let's set up your business's current inventory!")
            print("(if you intend to buy new items using your balance, skip this part)")
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
