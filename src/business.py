"""This stores all info about the economics and inventory of the business
and provides methods for serializing to JSON and back."""
import base64
import zlib
from dataclasses import asdict, dataclass, field
import decimal
import json
from typing import List, ClassVar

from .inventory import Inventory
from .item import Item
from .jsonencoder import *
from .loan import Loan
from .loanmenu import LoanMenu
from .loanpaybacktype import LoanPaybackType
from .transaction import Transaction
from .transactiontype import TransactionType
from .utils import round_dollars

__all__ = ['Business']


@dataclass(order=False)
class Business:
    """
    Args:
        balance (Optional[decimal.Decimal]): The business's balance in dollars.
        inventory (Optional[Inventory]): The inventory of the business.
        transactions (Optional[List[Transaction]]):
            The list of transactions the business has done.
        employee_count (Optional[int]): The number of employees.
        loans (LoanMenu): A list of loans the business is currently under.
        metadata (Optional[dict]): Some info about the business itself
            used for under the hood calculations.

    """
    balance: decimal.Decimal = None
    inventory: Inventory = None
    transactions: List[Transaction] = field(default_factory=list)
    employee_count: int = None
    loans: LoanMenu = field(default_factory=LoanMenu)
    total_weeks: int = 0
    metadata: dict = field(default_factory=dict)

    RANDOM_LOAN_COUNT: ClassVar[int] = 8
    NSF_FEE: ClassVar[decimal.Decimal] = decimal.Decimal('45')

    @property
    def month(self):
        return self.total_weeks // 4 % 12

    @property
    def week(self):
        return self.total_weeks % 4

    @property
    def year(self):
        return self.total_weeks // 48

    def add_transaction(self, title: str, dollars: decimal.Decimal,
                        type_=TransactionType.DEFAULT):
        """Record a transaction.

        Args:
            title (str)
            dollars (decimal.Decimal): The change in balance in dollars.
                For expenses, use negative values.
            type_ (TransactionType): The type of transaction.

        Returns:
            Transaction

        """
        t = Transaction(
            title=title,
            dollars=round_dollars(dollars),
            week=self.total_weeks,
            transaction_type=type_
        )
        self.transactions.append(t)
        return t

    def apply_loan(self, loan: Loan, copy=True):
        """Apply for a loan."""
        if loan in self.loans:
            raise ValueError(f'Already applied for loan {loan!r}')

        if not loan.is_subsidy:
            self.loans.add(loan.copy() if copy else loan)
        self.deposit(str(loan), loan.amount, TransactionType.LOAN)

    def buy_item(self, item: Item) -> bool:
        """Buy an item using the business's balance and update the inventory.
        If it fails to withdraw, nothing is added and instead returns False.

        Args:
            item (Item)

        Returns:
            bool: The withdrawal's success.

        """
        success = self.withdraw(f'{item}', -item.price, type_=TransactionType.PURCHASE)

        if success:
            inv_item = self.inventory.get(item.name)
            if inv_item is not None:
                # Update item
                inv_item += item
            else:
                # Add new item
                self.inventory.add(item)

        return success

    def deposit(self, title: str, dollars: decimal.Decimal,
                type_: TransactionType = None, log=True) -> bool:
        """Deposit some amount of money to the business.

        This returns a boolean whether the deposit was successful or not
        (which at the moment, is always True).

        Args:
            title (str): The title of the transaction.
            dollars (decimal.Decimal): The amount to deposit as
                a positive value.
            type_ (Optional[TransactionType]): The type of transaction.
            log (bool): If True, the transaction will be logged.

        Returns:
            bool: The deposit's success.

        """
        dollars = abs(dollars)

        if self.balance is None:
            self.balance = decimal.Decimal()
        self.balance += dollars

        if log:
            self.add_transaction(title, dollars, type_)

        return True

    def generate_metadata(self):
        """Generate some metadata for the business based on its current info.
        This can be extended by subclasses."""
        self.metadata.setdefault('total_loans', 0)
        if 'loan_menu' not in self.metadata:
            self.metadata['loan_menu'] = LoanMenu.from_random(
                self.RANDOM_LOAN_COUNT)

    def get_monthly_expenses(self) -> decimal.Decimal:
        """Calculate the average monthly expenses using purchases
        within one year.

        The returned expenses will be a positive number unless there
        was a positive transaction marked as an expense somehow, in which case
        that could make this return negative.

        """
        after = max(0, self.total_weeks - 48)
        transactions = self.get_transactions(
            after=after, type_=TransactionType.PURCHASE)

        if not transactions:
            return decimal.Decimal()
        return sum(-t.dollars for t in transactions) / max(1, decimal.Decimal(after) / 4)

    def get_monthly_revenue(self) -> decimal.Decimal:
        """Calculate the average monthly revenue using sales
        within one year."""
        after = max(0, self.total_weeks - 48)
        transactions = self.get_transactions(
            after=after, type_=TransactionType.SALES)

        if not transactions:
            return decimal.Decimal()
        time_span = decimal.Decimal(self.total_weeks - after)
        return sum(t.dollars for t in transactions) / max(1, time_span / 4)

    def get_transactions(self, limit: int = None, after: int = None,
                         type_=None, key=None) \
            -> List[Transaction]:
        """Get x transactions sorted by time.

        Args:
            limit (Optional[int]):
                The number of transactions to obtain at most.
                If not specified, returns all transactions.
            after (Optional[int]): Get transactions past a given week
                (inclusive).
            type_ (Optional[TransactionType]):
                Get transactions matching the specified TransactionType.
                If None, this check is not executed.
            key (Optional[Function]): An optional function with one
                parameter, transaction, that returns a boolean whether
                the transaction should be included or not.

        """
        transactions = sorted(self.transactions, key=lambda t: t.week)

        query = []
        for t in transactions:
            if after is not None and t.week < after:
                continue
            elif type_ is not None and t.transaction_type != type_:
                continue
            elif key is not None and not key(t):
                continue
            query.append(t)

        skip = 0
        if limit is not None:
            skip = len(query) - min(len(query), limit)

        return query[skip:]

    def on_next_month(self):
        """Called by step() when a new month occurs."""
        for loan in self.loans:
            if loan.payback_type == LoanPaybackType.MONTHLY:
                self.pay_loan(loan, in_inventory=True)

    def on_next_week(self):
        """Called by step() when a new week occurs."""
        for loan in self.loans:
            loan.remaining_weeks -= 1

            if (loan.payback_type == LoanPaybackType.WEEKLY
                    or loan.payback_type == LoanPaybackType.BIWEEKLY
                    and self.total_weeks % 2 == 0):
                self.pay_loan(loan, in_inventory=True)

    def on_next_year(self):
        """Called by step() when a new year occurs."""
        for loan in self.loans:
            if loan.payback_type == LoanPaybackType.YEARLY:
                self.pay_loan(loan, in_inventory=True)

    def pay_loan(self, loan: Loan, *, in_inventory=False) -> bool:
        """Pay a given loan according to its remaining weeks.

        Args:
            loan (Loan)
            in_inventory (bool): If True, the loan will only be paid if
                the remaining payments is 0 or greater. This is done as
                loans are not automatically deleted, which allows interfaces
                to display what loans have been paid off.

        Returns:
            bool: Whether the loan could be paid or not.

        """
        if loan.remaining_payments < 0 and in_inventory:
            return True

        payment = loan.get_next_payment(after_step=True)

        title = '{} payment for {}'.format(
            str(loan.payback_type).capitalize(),
            loan
        )

        success = self.withdraw(title, payment, type_=TransactionType.LOAN)

        if not success:
            # Prolong the loan
            loan.remaining_weeks += loan.payback_type

        return success

    def step(self, *, weeks: int):
        """Step the business by N weeks.

        This calls on_next_week(), on_next_month(), and on_next_year()
        correspondingly in that order.

        """
        if weeks < 0:
            raise ValueError(f'weeks ({weeks}) cannot be negative')

        for _ in range(weeks):
            self.total_weeks += 1
            self.on_next_week()
            if self.total_weeks % 4 == 0:
                self.on_next_month()
            if self.total_weeks % 48 == 0:
                self.on_next_year()

    def withdraw(self, title: str, dollars: decimal.Decimal,
                 type_: TransactionType = None, force=False, log=True) -> bool:
        """Attempt withdrawing some amount of money from the business.

        If the balance is in the negative and `force` is False, the business's
        bank will decline the withdrawal and tack on an NSF fee.

        This returns a boolean whether the withdrawal was successful or not.

        Args:
            title (str): The title of the transaction.
            dollars (decimal.Decimal): The amount to withdraw as
                a positive value.
            type_ (Optional[TransactionType]): The type of transaction.
            force (bool): If True, the withdrawal will always succeed
                regardless if there are insufficient funds.
            log (bool): If True, the transaction will be logged, either
                for successfully purchasing or for the NSF fee.
                Otherwise no transaction is included.

        Returns:
            bool: The withdrawal's success.

        """
        dollars = abs(dollars)
        if force or self.balance >= dollars:
            self.balance -= dollars
            if log:
                self.add_transaction(title, -dollars, type_)
            return True
        self.balance -= self.NSF_FEE
        if log:
            self.add_transaction(f'Declined transaction with NSF fee: {title}',
                                 -self.NSF_FEE, type_)
        return False

    def to_dict(self):
        return asdict(self)

    def to_file(self, f, *, compressed=False):
        """Save the business data to a file-like object or filepath.

        Note that it is recommended to provide a filepath instead of manually
        opening the file in write mode because that erases the file's contents.
        If an error occurs during serialization, the save file will be
        permanently lost.

        """
        text = json.dumps(self.to_dict(), cls=JSONEncoder,
                          indent=None if compressed else 4)
        if compressed:
            text = base64.b64encode(text.encode('utf-8'))
            text = zlib.compress(text)

        if isinstance(f, str):
            mode = 'wb' if compressed else 'w'
            encoding = None if compressed else 'utf-8'
            with open(f, mode, encoding=encoding) as file:
                file.write(text)
        else:
            # File-like object
            f.write(text)

    @staticmethod
    def _from_dict_deserialize(d: dict):
        inventory = d.get('inventory')
        if inventory is not None:
            d['inventory'] = Inventory.from_list(inventory)
        transactions = d.get('transactions')
        if transactions is not None:
            d['transactions'] = [Transaction.from_dict(d) for d in transactions]
        loans = d.get('loans')
        if loans is not None:
            d['loans'] = LoanMenu.from_list(loans)
        metadata = d.get('metadata')
        if metadata is None:
            metadata = d['metadata'] = {}
        loan_menu = metadata.get('loan_menu')
        if loan_menu is not None:
            metadata['loan_menu'] = LoanMenu.from_list(loan_menu)
        return d

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**cls._from_dict_deserialize(d))

    @classmethod
    def from_file(cls, f):
        """Create a business from either a file or filepath."""
        def decrypt(encoded):
            encoded = zlib.decompress(encoded)
            text = base64.b64decode(encoded).decode('utf-8')
            return cls.from_dict(json.loads(text, cls=JSONDecoder))

        if isinstance(f, str):
            try:
                with open(f, encoding='utf-8') as file:
                    text = file.read()
            except UnicodeDecodeError:
                with open(f, 'rb') as file:
                    text = file.read()

            try:
                return cls.from_dict(json.loads(text, cls=JSONDecoder))
            except Exception:
                return decrypt(text)

        text = f.read()
        try:
            return cls.from_dict(json.loads(text, cls=JSONDecoder))
        except Exception:
            return decrypt(text)
