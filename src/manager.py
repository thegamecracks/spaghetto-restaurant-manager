"""This provides the base class for interfacing with a Business.
The base class comes with a minimal CLI."""
import cmd
import contextlib
import datetime
import traceback

from . import utils
from .business import Business
from .cliutils import input_boolean, input_integer, input_money
from .inventory import Inventory
from .item import Item

__all__ = ['Manager']


class Manager:
    def __init__(self, business: Business, filepath: str = None):
        self.business = business
        self.filepath = filepath

    @contextlib.contextmanager
    def start_transaction(self):
        """This is a context manager that can be used to automatically
        save the business data when exiting the context.
        This allows the data to be saved regardless if an exception occurs
        or the user closes the program unconventionally.

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
            pass

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
        self.business.to_file(filepath)

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

    def __init__(self, manager: Manager, cmdqueue=None):
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


class ManagerCLISubCMDBase(ManagerCLIBase):
    def do_back(self, arg):
        """Go back to the main window."""
        return True


class ManagerCLIMain(ManagerCLIBase):
    def do_balance(self, arg):
        """Display your business's balance."""
        balance = Business.balance
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


class ManagerCLIInventory(ManagerCLISubCMDBase):
    doc_header = 'Inventory Management'

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
