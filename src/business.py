"""This stores all info about the economics and inventory of the business
and provides methods for serializing to JSON and back."""
import base64
from dataclasses import asdict, dataclass, field
import decimal
import json
from typing import List

from .inventory import Inventory
from .jsonencoder import *
from .loan import Loan
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
        loans (List[Loan]): A list of loans the business is currently under.
        metadata (Optional[dict]): Some info about the business itself
            used for under the hood calculations.

    """
    balance: decimal.Decimal = None
    inventory: Inventory = None
    transactions: List[Transaction] = field(default_factory=list)
    employee_count: int = None
    loans: List[Loan] = field(default_factory=list)
    total_weeks: int = 0
    metadata: dict = field(default_factory=dict)

    @property
    def month(self):
        return self.total_weeks // 4 % 12

    @property
    def week(self):
        return self.total_weeks % 4

    @property
    def year(self):
        return self.total_weeks // 48

    def add_transaction(self, title: str, dollars: int,
                        type_=TransactionType.DEFAULT):
        """Record a transaction.

        Args:
            title (str)
            dollars (numbers.Rational): The change in balance in dollars.
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

    def buy_item(self, item):
        """Buy an item using the business's balance and update the inventory."""
        self.add_transaction(f'{item}', -item.price, type_=TransactionType.PURCHASE)
        self.balance -= item.price

        inv_item = self.inventory.get(item.name)
        if inv_item is not None:
            # Update item
            inv_item += item
        else:
            # Add new item
            self.inventory.add(item)

    @staticmethod
    def format_date(week: int) -> str:
        """Format a week or date as "Y1 M1 W1"."""
        month = week // 4 % 12
        year = week // 48
        week %= 4

        return f'Y{year + 1} M{month + 1} W{week + 1}'

    def generate_metadata(self):
        """Generate some metadata for the business
        based on its current info. Meant to be overridden by subclasses."""

    def get_monthly_expense(self):
        """Calculate the average monthly expenses using purchases
        within one year.

        The returned expenses will be a positive number.

        """
        transactions = self.get_transactions(
            after=self.total_weeks - 48, type_=TransactionType.PURCHASE)

        return sum(abs(t.dollars) for t in transactions) / len(transactions)

    def get_monthly_revenue(self):
        """Calculate the average monthly revenue using sales
        within one year."""
        transactions = self.get_transactions(
            after=self.total_weeks - 48, type_=TransactionType.SALES)

        return sum(abs(t.dollars) for t in transactions) / len(transactions)

    def get_transactions(self, limit: int = None, after: int = None,
                         type_=None, key=None) \
            -> List[Transaction]:
        """Get x transactions sorted by time.

        Args:
            limit (Optional[int]):
                The number of transactions to obtain at most.
                If not specified, returns all transactions.
            after (Optional[int]): Get transactions past a given week.
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
                self.pay_loan(loan)

    def on_next_week(self):
        """Called by step() when a new week occurs."""
        for loan in self.loans:
            loan.remaining_weeks -= 1

            if (loan.payback_type == LoanPaybackType.WEEKLY
                    or loan.payback_type == LoanPaybackType.BIWEEKLY
                    and self.total_weeks % 2 == 0):
                self.pay_loan(loan)

    def on_next_year(self):
        """Called by step() when a new year occurs."""
        for loan in self.loans:
            if loan.payback_type == LoanPaybackType.YEARLY:
                self.pay_loan(loan)

    def pay_loan(self, loan: Loan):
        """Pay a given loan according to its remaining weeks."""
        payment = loan.get_next_payment()

        title = '{} payment for {}'.format(
            str(loan.payback_type).capitalize(),
            loan
        )

        self.balance -= payment
        self.add_transaction(title, -payment, type_=TransactionType.LOAN)

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

    def to_dict(self):
        return asdict(self)

    def to_file(self, f, *, encrypted=False):
        """Save the business data to a file-like object or filepath.

        Note that it is recommended to provide a filepath instead of manually
        opening the file in write mode because that erases the file's contents.
        If an error occurs during serialization, the save file will be
        permanently lost.

        """
        text = json.dumps(self.to_dict(), cls=JSONEncoder,
                          indent=None if encrypted else 4)
        if encrypted:
            text = base64.b64encode(text.encode('utf-8'))

        if isinstance(f, str):
            mode = 'wb' if encrypted else 'w'
            encoding = None if encrypted else 'utf-8'
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
            d['loans'] = [Loan.from_dict(d) for d in loans]
        return d

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**cls._from_dict_deserialize(d))

    @classmethod
    def from_file(cls, f):
        """Create a business from either a file or filepath."""
        def decrypt(encoded):
            text = base64.b64decode(encoded).decode('utf-8')
            return cls.from_dict(json.loads(text, cls=JSONDecoder))

        if isinstance(f, str):
            with open(f, encoding='utf-8') as file:
                text = file.read()
                try:
                    return cls.from_dict(json.loads(text, cls=JSONDecoder))
                except json.JSONDecodeError:
                    return decrypt(text)

        text = f.read()
        try:
            return cls.from_dict(json.loads(text, cls=JSONDecoder))
        except json.JSONDecodeError:
            return decrypt(text)
