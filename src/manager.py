"""This provides the base class for interfacing with a Business.
The base class comes with a minimal CLI."""
import cmd
import contextlib
import decimal
import traceback
from typing import List

from . import utils
from .business import Business
from .cliutils import input_integer, input_money
from .inventory import Inventory
from .item import Item
from .loanmenu import LoanMenu
from .transaction import Transaction

__all__ = ['Manager']


class Manager:
    _TYPE = Business
    RANDOM_LOANS = 8

    def __init__(self, business: Business, loan_menu: LoanMenu = None,
                 filepath: str = None, encrypted=False):
        self.business = business
        self.loan_menu = loan_menu
        self.filepath = filepath
        self.encrypted = encrypted

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
        """Setup the business's balance and inventory if they are None.
        This is intended for the CLI."""
        business = self.business
        if business.balance is None:
            business.balance = input_money(
                "What is your business's current balance? $")

        if business.employee_count is None:
            business.employee_count = input_integer(
                "How many employees do you have? ", minimum=0)

        if business.inventory is None:
            print("Let's set up your business's current inventory!")
            print("(if you intend to buy new items using your balance, skip this part)")
            self.setup_inventory()

        if self.loan_menu is None:
            self.loan_menu = LoanMenu.from_random(self.RANDOM_LOANS)
        self.business.generate_metadata()

    @classmethod
    def from_filepath(cls, filepath, *, encrypted=False):
        business = cls._TYPE.from_file(filepath)
        return cls(business, filepath=filepath, encrypted=encrypted)

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
        self.business.to_file(filepath, encrypted=self.encrypted)

    def reload_business(self, filepath=None):
        """Reload the business's data from `filepath`.
        Defaults to `self.filepath` if no filepath is provided."""
        filepath = filepath or self.filepath
        with open(filepath, encoding='utf-8') as f:
            self.business = self._TYPE.from_file(f)

    def run(self):
        """Start the user interface.
        Override this method in a subclass to implement a new interface."""
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

    def postcmd(self, stop, line):
        """Called after a command dispatch is finished.
        Prints a message if the business's balance is negative."""
        balance = self.manager.business.balance
        if balance < 0:
            print("Warning: the business's balance is negative! "
                  f'({utils.format_dollars(balance)})')
        return stop


class ManagerCLISubCMDBase(ManagerCLIBase):
    def do_back(self, arg):
        """Go back to the main window."""
        return True


class ManagerCLIMain(ManagerCLIBase):
    def do_exit(self, arg):
        """Exit the program. This automatically saves your data."""
        return True

    def do_finances(self, arg):
        """Manage your business's finances."""
        ManagerCLIFinances(self.manager).cmdloop()
        self.cmdqueue.append('help')

    def do_inventory(self, arg):
        """Interact with your business's inventory.
WIP: This currently only prints the inventory of the business."""
        ManagerCLIInventory(self.manager).cmdloop()
        self.cmdqueue.append('help')

    def do_load(self, arg):
        """Load your business's data."""
        try:
            self.manager.reload_business()
        except Exception as e:
            print('An error occurred while loading:')
            traceback.print_exception(type(e), e, e.__traceback__)
        else:
            print('Successfully loaded!')

    def do_save(self, arg):
        """Save your business's data onto disk."""
        try:
            self.manager.save_business()
        except Exception as e:
            print('An error occurred while saving:')
            traceback.print_exception(type(e), e, e.__traceback__)
        else:
            print('Successfully saved!')

    def do_step(self, arg):
        """Go to the next month."""
        business = self.manager.business
        business.step(weeks=4)
        print(business.format_date(business.total_weeks))

    def do_time(self, arg):
        """View the current year, month, and week."""
        business = self.manager.business
        print('The current date is:', business.format_date(business.total_weeks))


class ManagerCLIFinancesEmployees(ManagerCLISubCMDBase):
    doc_header = 'Employee Management'

    def preloop(self):
        """Show count at the start of the loop."""
        self.cmdqueue.append('count')

    def do_count(self, arg):
        """View the number of employees."""
        count = self.manager.business.employee_count
        tense = 'is' if count == 1 else 'are'
        print('There {} {} {}.'.format(
            tense,
            count,
            utils.plural('employee', count)
        ))

    def do_decrease(self, arg):
        """Decrease the number of employees.
Usage: decrease <number>"""
        arg = arg.strip()
        if not arg:
            return print('Usage: decrease <number>')
        try:
            num = int(arg)
        except ValueError:
            return print('Could not parse your number.')

        if num < 1:
            return print('You must remove at least one employee.')

        count = self.manager.business.employee_count
        new = count - num
        if new < 0:
            return print(
                'You cannot remove over {} {} (the current count is {}).'.format(
                    num,
                    utils.plural('employee', num),
                    count
                )
            )

        self.manager.business.employee_count = new

        print('You have removed {} {}! Your new count is {}.'.format(
            num,
            utils.plural('employee', num),
            new
        ))

    def do_increase(self, arg):
        """Increase the number of employees.
Usage: increase <number>"""
        arg = arg.strip()
        if not arg:
            return print('Usage: increase <number>')
        try:
            num = int(arg)
        except ValueError:
            return print('Could not parse your number.')

        if num < 1:
            return print('You must add at least one employee.')

        self.manager.business.employee_count += num

        print('You have added {} {}! Your new count is {}.'.format(
            num,
            utils.plural('employee', num),
            self.manager.business.employee_count
        ))


class ManagerCLIFinances(ManagerCLISubCMDBase):
    doc_header = 'Finance Management'

    def print_transactions(self, transactions: List[Transaction]):
        business = self.manager.business
        weeks = []
        dollars = []

        for t in transactions:
            weeks.append(business.format_date(t.week))
            dollars.append(utils.format_dollars(t.dollars))

        week_longest = max(len(w) for w in weeks)
        dollars_longest = max(len(d) for d in dollars)

        # Print transactions
        for w, d, t in zip(weeks, dollars, transactions):
            print('{week} : {dollars} : {title}'.format(
                week=f'{w:>{week_longest}}',
                dollars=f'{d:>{dollars_longest}}',
                title=t.title
            ))

    def do_balance(self, arg):
        """Display your business's balance."""
        balance = self.manager.business.balance
        print(f"Your business's balance is {utils.format_dollars(balance)}.")

    def do_employees(self, arg):
        """View and modify the number of employees in your business."""
        ManagerCLIFinancesEmployees(self.manager).cmdloop()
        self.cmdqueue.append('help')

    def do_expenses(self, arg):
        """View the current and last month's expenses."""
        business = self.manager.business
        after = business.total_weeks - business.total_weeks % 4 - 4
        transactions = business.get_transactions(after=after, key=lambda t: t.dollars < 0)

        if not transactions:
            return print('There are no recent expenses.')

        self.print_transactions(transactions)

    def do_history(self, arg):
        """Display the last 20 transactions."""
        business = self.manager.business
        transactions = business.get_transactions(20)

        if not transactions:
            return print('There are no recent transactions.')

        self.print_transactions(transactions)

    def do_loans(self, arg):
        """View the business's loans."""
        # TODO: Loan sub-interface

    def do_revenue(self, arg):
        """View the current and last month's income transactions."""
        business = self.manager.business
        after = business.total_weeks - business.total_weeks % 4 - 4
        transactions = self.manager.business.get_transactions(key=lambda t: t.dollars > 0)

        if not transactions:
            return print('There are no recent income transactions.')

        self.print_transactions(transactions)


class ManagerCLIInventory(ManagerCLISubCMDBase):
    doc_header = 'Inventory Management'

    def input_money_per(self, prompt, minimum=None, maximum=None):
        """Get money input from the user.
        This variant of `input_money` returns a tuple. The first
        element is the money they inputted, and the second is a boolean
        denoting if the user inputted "per" at the end.
        """
        def parse(s):
            s = s.lower()
            is_unit_price = s.endswith('per')
            try:
                dollars = utils.parse_dollars(s.rstrip('per'))
            except ValueError:
                return 'Could not parse your amount: $'
            if minimum is not None and dollars < minimum:
                return f'Must be above {minimum:,}: $'
            elif maximum is not None and dollars > maximum:
                return f'Must be below {maximum:,}: $'
            return dollars, is_unit_price

        if minimum is not None:
            minimum = decimal.Decimal(minimum)
        if maximum is not None:
            maximum = decimal.Decimal(maximum)

        result = parse(input(prompt))
        while isinstance(result, str):
            result = parse(input(result))
        return result

    def do_buy(self, arg):
        """Buy an item using the business's balance."""
        business = self.manager.business
        inv = business.inventory

        name = input('What is the name of the item? ').strip()

        if not name:
            return print('Cancelled purchase.')

        item = inv.get(name)

        if item is not None:
            unit = item.unit
        else:
            unit = input('What unit is this item measured in? ')

        quantity = input_integer('How much do you want to buy? ', minimum=0)
        price, is_unit = self.input_money_per(
            'What is the cost of your purchase? (type "per" at the end if '
            f'you are specifying the unit price)\n{self.prompt}$', minimum=0
        )
        if is_unit:
            price *= quantity

        # Create the new item and update the business
        new_item = Item(name, quantity, unit, price)
        business.buy_item(new_item)
        print(f'{new_item} purchased!')

    def do_list(self, arg):
        """List the items in your inventory."""
        print('Inventory:')
        for i, item in enumerate(self.manager.business.inventory, start=1):
            print(f'{i:,}: {item}')
