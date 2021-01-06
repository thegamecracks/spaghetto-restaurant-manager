"""This provides the base class for interfacing with a Business.
The base class comes with a minimal CLI."""
import cmd
import contextlib
import decimal
import os
import traceback
from typing import List, Union, Optional

from . import utils
from .business import Business
from .cliutils import input_integer, input_money, input_boolean, is_integer, input_choice
from .inventory import Inventory
from .inventoryitem import InventoryItem
from .item import Item
from .loan import Loan
from .loanmenu import LoanMenu
from .loanpaybacktype import LoanPaybackType
from .transaction import Transaction

__all__ = ['Manager']


class Manager:
    _TYPE = Business

    def __init__(self, business: Business, filepath: str = None, compressed=False):
        self.business = business
        self.filepath = filepath
        self.compressed = compressed
        self.deleted = False

    def delete_business(self):
        """Delete the business's save file and mark this as deleted."""
        os.remove(self.filepath)
        self.deleted = True

    @staticmethod
    def describe_invitem(item: InventoryItem) -> str:
        """Return a string describing a given inventory item.

        Args:
            item (InventoryItem)

        Returns:
            str

        """
        description = (
            f'Quantity: {item.quantity}\n'
            f'Total value: {utils.format_dollars(item.cost_of())}'
        )
        return description

    @staticmethod
    def describe_loan(loan: Loan) -> str:
        """Return a string describing a given loan.

        Args:
            loan (Loan)

        Returns:
            str

        """
        description = (
            'Term: {term} {terms}\n'
            'Amount: {amount}\n'
            'Remaining {payback} payments: {payments}\n'
            'Next payment will be: {nextpayment}, in {nexttime}'
        ).format(
            term=loan.term,
            terms=utils.plural('year', loan.term),
            amount=utils.format_dollars(loan.amount),
            payback=str(loan.payback_type),
            payments=loan.remaining_payments,
            nextpayment=utils.format_dollars(loan.get_next_payment()),
            nexttime=utils.format_weeks(loan.remaining_weeks % loan.payback_type
                                        or loan.payback_type)
        )
        return description

    def get_invitem(self, s: Union[int, str]) -> InventoryItem:
        """Lookup an InventoryItem by index or name.

        Args:
            s (Union[int, str])

        Returns:
            InventoryItem
            None

        """
        inv = self.business.inventory
        # Lookup by index
        try:
            index = int(s)
        except ValueError:
            pass
        else:
            mapping = self.invitem_mapping()
            return mapping.get(index)

        # Fuzzy lookup by name
        return inv.find(s)

    def get_loan(self, s: Union[int, str], menu: LoanMenu = None) -> Loan:
        """Lookup a Loan by index or name.

        Args:
            s (Union[int, str])
            menu (Optional[LoanMenu]): The menu to check for loans.
                Defaults to the business's own loans.

        Returns:
            Loan
            None

        """
        # Lookup by index
        try:
            index = int(s)
        except ValueError:
            pass
        else:
            mapping = self.loan_mapping(menu)
            return mapping.get(index)

        # Fuzzy lookup by name
        return menu.find(s)

    def loan_mapping(self, menu: LoanMenu = None):
        """Returns a mapping of indices to business loans.
        1: BMO "Petty Businesses" Loan
        ...
        If you want a mapping of a different set of loans (such as the
        'loan_menu' metadata), you can pass that as an argument.
        """
        menu = self.business.loans if menu is None else menu
        return {i: loan for i, loan in enumerate(menu, start=1)}

    def invitem_mapping(self) -> dict:
        """Returns a mapping of indices to inventory items.
        1: Dark Coffee Beans
        ... """
        return {i: item for i, item in enumerate(self.business.inventory, start=1)}

    def reload_business(self, filepath=None):
        """Reload the business's data from `filepath`.
        Defaults to `self.filepath` if no filepath is provided.

        If self.deleted, this is a no-op.

        """
        if self.deleted:
            return

        filepath = filepath or self.filepath
        with open(filepath, encoding='utf-8') as f:
            self.business = self._TYPE.from_file(f)

    def run(self):
        """Start the user interface.
        Override this method in a subclass to implement a new interface."""
        self.setup_business()

        ManagerCLIMain(self).cmdloop()

    def save_business(self, filepath=None):
        """Save the business to `filepath`.
        Defaults to `self.filepath` if no filepath is provided.

        Except for `with manager.start_transaction(): ...`, this method
        will always succeed regardless if the business is deleted.
        This allows a last resort save while the program is still alive.

        """
        filepath = filepath or self.filepath
        self.business.to_file(filepath, compressed=self.compressed)

    def setup_business(self):
        """Setup the business's balance and inventory if they are None.
        This is intended for the CLI."""
        business = self.business
        if business.balance is None:
            balance = input_money(
                "What is your business's current balance? $")
            business.deposit('Initial balance', balance)

        if business.employee_count is None:
            business.employee_count = input_integer(
                "How many employees do you have? ", minimum=1)

        if business.inventory is None:
            print("Let's set up your business's current inventory!")
            print("(if you intend to buy new items using your balance, skip this part)")
            self.setup_inventory()

        self.business.generate_metadata()

    def setup_inventory(self):
        """Setup the business's inventory."""
        def input_item():
            name = input(f'Item #{item_num:,} name (type nothing to finish): ').strip()
            while name in inv:
                name = input('You have already used that name: ').strip()
            if not name:
                return

            quantity = input_integer('Quantity: ', minimum=0)
            unit = input('Unit of quantity (gram, millilitre, cup...): ').strip()
            price = input_money('Total cost of item: $', minimum=0)

            return Item(name, quantity, unit, price)

        inv = Inventory()
        item_num = 1

        item = input_item()
        while item is not None:
            inv.add(item)
            item_num += 1
            item = input_item()

        self.business.inventory = inv

    @contextlib.contextmanager
    def start_transaction(self):
        """This is a context manager that can be used to automatically
        save the business data when exiting the context.
        This allows the data to be saved regardless if an exception occurs
        or the user closes the program unconventionally.

        If self.deleted however, the save will not be executed.

        Usage:
            >>> with manager.start_transaction():
            ...     manager.run()

        """
        try:
            yield self
        finally:
            if not self.deleted:
                self.save_business()

    @classmethod
    def from_filepath(cls, filepath, *, compressed=False):
        business = cls._TYPE.from_file(filepath)
        return cls(business, filepath=filepath, compressed=compressed)


class ManagerCLIBase(cmd.Cmd):
    intro = ''  # Message when shell is opened
    prompt_default = '> '
    prompt = prompt_default  # Input prompt

    ruler = '='  # Used for help message headers
    doc_leader = ''  # Printed before the documentation headers
    doc_header = 'Commands (type help <command> to see their usage):'
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

    def default(self, line: str) -> bool:
        command, arg, line = self.parseline(line)
        try:
            hidden = getattr(self, 'condhidden_' + command)
        except AttributeError:
            return super().default(line)

        return hidden(arg)

    def get_names(self):
        """Modifies get_names to support dynamic commands."""
        return dir(self)

    def add_conditional(self, name, func):
        setattr(self, name, func)

    def delete_conditional(self, name):
        try:
            delattr(self, name)
        except AttributeError:
            pass

    def set_conditional(self, name, func, enable: bool):
        """Set a conditional command as enabled or not."""
        if enable:
            self.add_conditional(name, func)
        else:
            self.delete_conditional(name)

    def update_conditional(self):
        """Method stub for adding/removing dynamic commands."""

    def preloop(self):
        self.update_conditional()

    def postcmd(self, stop, line):
        """Called after a command dispatch is finished.
        Prints a message if the business's balance is negative."""
        balance = self.manager.business.balance
        if balance < 0:
            print("Warning: the business's balance is negative! "
                  f'({utils.format_dollars(balance)})')
        self.update_conditional()
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
        print(utils.format_date(business.total_weeks))

    def do_time(self, arg):
        """View the current year, month, and week."""
        business = self.manager.business
        print('The current date is:', utils.format_date(business.total_weeks))


class ManagerCLIFinancesEmployees(ManagerCLISubCMDBase):
    doc_header = 'Employee Management'

    def preloop(self):
        """Show count at the start of the loop."""
        super().preloop()
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


class ManagerCLIFinancesLoans(ManagerCLISubCMDBase):
    doc_header = 'Loan Management'

    @staticmethod
    def print_loan_not_found(arg):
        if is_integer(arg):
            return print('That index does not exist!')
        else:
            return print('Could not find a matching name for that loan.')

    def input_loan(self, menu: LoanMenu, prompt: str, *, cancellable=False) \
            -> Optional[Loan]:
        """Prompt the user for an existing loan.

        Args:
            menu (LoanMenu): The menu to get loans from.
            prompt (str): The initial message to show the user.
            cancellable (bool): Whether the user can cancel the prompt or not.

        Returns:
            Loan
            None: if `cancellable` and user inputs nothing.

        """
        if cancellable:
            prompt += '(type nothing to cancel) '

        arg = input(prompt).strip()
        loan = self.manager.get_loan(arg, menu)
        while loan is None:
            if not arg and cancellable:
                return
            arg = input('Could not find that loan: ').strip()
            loan = self.manager.get_loan(arg, menu)
        return loan

    def do_apply(self, arg):
        """Apply for a loan (or just see the requirements of one).
Usage: apply [name_or_index]"""
        def cancel():
            print('Cancelled application.')
        business = self.manager.business
        if business.loans:
            return print('You have already applied for a loan.')

        arg = arg.strip()

        loan_menu: LoanMenu = business.metadata['loan_menu']
        if arg:
            # User supplied argument
            loan = self.manager.get_loan(arg, loan_menu)
            if loan is None:
                return self.print_loan_not_found(arg)
        else:
            loan = self.input_loan(
                loan_menu, "What is the loan you want to apply for? ",
                cancellable=True
            )
            if loan is None:
                return cancel()

        print(loan)
        name = 'subsidy' if loan.is_subsidy else 'loan'

        print(f'Amount: {utils.format_dollars(loan.amount)}')
        if not loan.is_subsidy:
            rate_type = str(loan.interest_type)
            rate_frequency = loan.interest_type.frequency
            if rate_frequency:
                rate_type = f'{rate_frequency} {rate_type}ed'
            print('{} interest rate: {:%}'.format(
                rate_type.capitalize(),
                loan.rate
            ))
            if loan.term is not None and loan.payback_type is not None:
                remaining_payments = loan.remaining_payments
                print('Total payments: {} ({})'.format(
                    remaining_payments,
                    str(loan.payback_type)
                ))
            elif loan.payback_type is not None:
                # Can't calculate # of payments, user has to input the term
                print('Payment frequency:', loan.payback_type)

        qualified = loan.check(business)
        if loan.requirements:
            meets = 'meets' if qualified else 'does not meet'
            print(f'Your business {meets} the requirements for this {name}:')
            for req in loan.requirements:
                sign = '+' if req.check(business) else '-'
                print(sign, req)

        if not qualified:
            return

        # Negotiations to be done
        negotiate_term = not loan.is_subsidy and loan.term is None
        negotiate_payback = not loan.is_subsidy and loan.payback_type is None

        if any((negotiate_term, negotiate_payback)) and not input_boolean(
                'Proceed with negotiating terms? (y/n) '):
            return

        loan = loan.copy()

        if negotiate_term:
            loan.term = input_integer(
                'What do you want the loan term to be? (years) ', minimum=1)
            print('Interest due:', utils.format_dollars(loan.interest_due))

            while not input_boolean('Confirm selection: (y/n) '):
                loan.term = input_integer(
                    'What do you want the loan term to be? ', minimum=1)
                print('Interest due:', utils.format_dollars(loan.interest_due))

            # Update remaining_payments to match the term
            loan.reset_remaining_weeks()

        if negotiate_payback:
            payback_types = (LoanPaybackType.MONTHLY, LoanPaybackType.YEARLY)
            loan.payback_type = input_choice(
                'How frequently do you want to pay this loan? ',
                payback_types,
                fuzzy_match=True
            )
            print('Payments: {} x {}'.format(
                loan.remaining_payments,
                utils.format_dollars(loan.normal_payment)
            ))
            while not input_boolean('Confirm selection: (y/n) '):
                loan.payback_type = input_choice(
                    'How frequently do you want to pay this loan? ',
                    payback_types,
                    fuzzy_match=True
                )
                print('Payments: {} x {}'.format(
                    loan.remaining_payments,
                    utils.format_dollars(loan.normal_payment)
                ))

        if input_boolean(
                f'Are you sure you want to apply for this {name}? (y/n) '):
            business.apply_loan(loan, copy=False)
            if loan.is_subsidy:
                loan_menu.remove(loan)
            print(f'You have successfully applied for the {loan}!')
        else:
            return cancel()

    def do_available(self, arg):
        """View the available loans from various banks."""
        business = self.manager.business
        loan_menu = business.metadata['loan_menu']
        for i, loan in enumerate(loan_menu, start=1):
            state = '(qualifying)' if loan.check(business) else '(unavailable)'
            print(f'{i:,}: {loan} {state}')
        print('Note that you can only apply for one loan at a time.')

    def do_list(self, arg):
        """View the business's loans."""
        if not self.manager.business.loans:
            return print('Your business currently has no loans.')

        for i, loan in enumerate(self.manager.business.loans, start=1):
            print(f'{i:,}: {loan}')

    def do_show(self, arg):
        """Show the details on a particular loan.
Usage: show [name_or_index]"""
        if not self.manager.business.loans:
            return print('Your business currently has no loans.')

        arg = arg.strip()

        loan_menu = self.manager.business.loans
        if arg:
            # User supplied argument
            loan = self.manager.get_loan(arg, loan_menu)
            if loan is None:
                return self.print_loan_not_found(arg)
        else:
            loan = self.input_loan(
                loan_menu, "What is the loan you want to show? ",
                cancellable=True
            )
            if loan is None:
                return print('Cancelled.')

        print(loan.name)
        print(self.manager.describe_loan(loan))


class ManagerCLIFinances(ManagerCLISubCMDBase):
    doc_header = 'Finance Management'

    def preloop(self):
        """Display any completed loans."""
        super().preloop()

        completed_loans: List[Loan] = []
        for loan in self.manager.business.loans:
            if loan.remaining_weeks <= 0:
                completed_loans.append(loan)

        if completed_loans:
            print('The following {} has been fully paid off:'.format(
                utils.plural('loan', len(completed_loans))
            ))
            for loan in completed_loans:
                del self.manager.business.loans[loan]
                print(loan, ':', utils.format_dollars(loan.amount + loan.interest_due))

    def update_conditional(self):
        self.set_conditional(
            'do_bankruptcy', self.cond_bankruptcy,
            self.manager.business.balance < 0
        )

    def print_transactions(self, transactions: List[Transaction]):
        if not transactions:
            return

        business = self.manager.business
        weeks = []
        dollars = []

        for t in transactions:
            weeks.append(utils.format_date(t.week))
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
        """View your average expenses, along with the current and last month's expenses.
Your average expenses will only include what you have spent on inventory."""
        business = self.manager.business
        after = business.total_weeks - business.total_weeks % 4 - 4
        transactions = business.get_transactions(after=after, key=lambda t: t.dollars < 0)

        print('Your monthly expenses is:',
              utils.format_dollars(business.get_monthly_expenses()))

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
        ManagerCLIFinancesLoans(self.manager).cmdloop()
        self.cmdqueue.append('help')

    def do_revenue(self, arg):
        """View your average revenue, along with the current and last month's income transactions."""
        business = self.manager.business
        after = business.total_weeks - business.total_weeks % 4 - 4
        transactions = self.manager.business.get_transactions(key=lambda t: t.dollars > 0)

        print('Your monthly revenue is:',
              utils.format_dollars(business.get_monthly_revenue()))

        self.print_transactions(transactions)

    def cond_bankruptcy(self, arg):
        """File for bankruptcy."""
        if input_boolean('Are you sure you want to file for bankruptcy? (y/n) '):
            self.manager.delete_business()
            input('Your business has been liquidated.\n'
                  'Press Enter to close this program.')
            quit()


class ManagerCLIInventory(ManagerCLISubCMDBase):
    doc_header = 'Inventory Management'

    @staticmethod
    def print_item_not_found(arg):
        if is_integer(arg):
            return print('That index does not exist!')
        else:
            return print('Could not find a matching name for that item.')

    def input_item(self, prompt: str, *, cancellable=False) \
            -> Optional[InventoryItem]:
        """Prompt the user for an existing item.

        Args:
            prompt (str): The initial message to show the user.
            cancellable (bool): Whether the user can cancel the prompt or not.

        Returns:
            InventoryItem
            None: if `cancellable` and user inputs nothing.

        """
        if cancellable:
            prompt += '(type nothing to cancel) '

        arg = input(prompt).strip()
        loan = self.manager.get_invitem(arg)
        while loan is None:
            if not arg and cancellable:
                return
            arg = input('Could not find that item: ').strip()
            loan = self.manager.get_invitem(arg)
        return loan

    def update_conditional(self):
        self.set_conditional(
            'do_buy', self.cond_buy,
            self.manager.business.balance > 0
        )

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

    def cond_buy(self, arg):
        """Buy an item using the business's balance."""
        def cancel():
            print('Cancelled purchase.')

        business = self.manager.business
        inv = business.inventory

        name = input('What is the name of the item? ').strip()

        if not name:
            return cancel()

        item = inv.get(name)

        if item is not None:
            unit = item.unit
        else:
            unit = input('What unit is this item measured in? (gram, millilitre, cup...) ').strip()
            if not unit:
                return cancel()

        quantity = input_integer('How much do you want to buy? ', minimum=0, default=0)
        if not quantity:
            return cancel()

        price, is_unit = self.input_money_per(
            'What is the cost of your purchase? (type "per" at the end if '
            f'you are specifying the unit price)\n{self.prompt}$', minimum=0,
            maximum=business.balance
        )
        if is_unit:
            price *= quantity

        # Create the new item and try buying it
        new_item = Item(name, quantity, unit, price)
        success = business.buy_item(new_item)
        if success:
            print(f'{new_item} purchased!')
        else:
            # NOTE: This shouldn't occur since input_money_per sets the
            # maximum but it's best to handle it anyways
            print('Failed to purchase item.')

    def condhidden_buy(self, arg):
        balance = utils.format_dollars(self.manager.business.balance)
        print(f'Cannot use this command with a balance of {balance}.')

    def do_list(self, arg):
        """List the items in your inventory."""
        print('Inventory:')
        for i, item in enumerate(self.manager.business.inventory, start=1):
            print(f'{i:,}: {item}')

    def do_remove(self, arg):
        """Remove some number of an item from inventory.
Usage: remove [name_or_index]"""
        def cancel():
            print('Cancelled removal.')

        business = self.manager.business
        if not business.inventory:
            return print('Your inventory currently has no items.')

        arg = arg.strip()

        if arg:
            # User supplied argument
            item = self.manager.get_invitem(arg)
            if item is None:
                return self.print_item_not_found(arg)
        else:
            item = self.input_item(
                "What is the item you want to remove? ", cancellable=True)
            if item is None:
                return print('Cancelled deletion.')

        maximum = item.quantity
        num = 0
        if maximum != 0:
            num = input_integer(
                f'How much of this item do you want to remove? ({maximum:,} total) ',
                minimum=0, maximum=maximum, default=0
            )
            if not num:
                return cancel()

        prompt = 'Are you sure you want to completely remove this item? (y/n) '
        if maximum == 0:
            prompt = 'Are you sure you want to remove this item entry? (y/n) '
        elif num != maximum:
            prompt = (f'Are you sure you want to remove {num:,} '
                      'of this item? (y/n) ')

        print(item.name)
        if num != 0:
            print('Value of items at your given quantity:',
                  utils.format_dollars(item.cost_of(num)),
                  f'({num / maximum:.0%})')

        if input_boolean(prompt):
            if num == maximum:
                business.inventory.remove(item)
            else:
                item.subtract(num)
            if num == 0:
                print('Removed item!')
            else:
                print('Removed {} {}!'.format(num, utils.plural('item', num)))
        else:
            return cancel()

    def do_show(self, arg):
        """Show the details on an inventory item.
Usage: show [name_or_index]"""
        if not self.manager.business.inventory:
            return print('Your business currently has no items.')

        arg = arg.strip()

        if arg:
            # User supplied argument
            item = self.manager.get_invitem(arg)
            if item is None:
                return self.print_item_not_found(arg)
        else:
            item = self.input_item(
                "What is the item you want to show? ",
                cancellable=True
            )
            if item is None:
                return print('Cancelled.')

        print(item.name)
        print(self.manager.describe_invitem(item))
