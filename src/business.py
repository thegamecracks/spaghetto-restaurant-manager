"""This stores all info about the economics and inventory of the business
and provides methods for serializing to JSON and back."""
from dataclasses import asdict, dataclass, field
import decimal
import io
import json
from typing import List

from .inventory import Inventory
from .jsonencoder import *
from .transaction import Transaction
from .utils import round_dollars


@dataclass(order=False)
class Business:
    """
    Args:
        balance (Optional[decimal.Decimal]): The business's balance in dollars.
        inventory (Optional[Inventory]): The inventory of the business.
        transactions (Optional[List[Transaction]]):
            The list of transactions the business has done.
        employee_count (Optional[int]): The number of employees.
        metadata (Optional[dict]): Some info about the business itself
            used for under the hood calculations.

    """
    balance: decimal.Decimal = None
    inventory: Inventory = None
    transactions: List[Transaction] = field(default_factory=list)
    employee_count: int = None
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

    def add_transaction(self, title: str, dollars: int):
        """Record a transaction.

        Args:
            title (str)
            dollars (numbers.Rational): The change in balance in dollars.
                For expenses, use negative values.

        """
        self.transactions.append(
            Transaction(
                title=title,
                dollars=round_dollars(dollars),
                week=self.total_weeks
            )
        )

    def buy_item(self, item):
        """Buy an item using the business's balance and update the inventory."""
        self.add_transaction(f'{item}', -item.price)
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

    def get_transactions(self, limit: int = None, after: int = None, key=None) \
            -> List[Transaction]:
        """Get x transactions sorted by time.

        Args:
            limit (Optional[int]):
                The number of transactions to obtain at most.
                If not specified, returns all transactions.
            after (int): Get transactions past a given week.
            key (Optional[Function]): An optional function with one
                parameter, transaction, that returns a boolean whether
                the transaction should be included or not.

        """
        transactions = sorted(self.transactions, key=lambda t: t.week)

        query = []
        for t in transactions:
            if after is not None and t.week < after:
                continue
            if key is not None and not key(t):
                continue
            query.append(t)

        skip = 0
        if limit is not None:
            skip = len(query) - min(len(query), limit)

        return query[skip:]

    def step(self, *, weeks: int):
        """Step the business by N weeks."""
        self.total_weeks += weeks

    def to_dict(self):
        return asdict(self)

    def to_file(self, f):
        """Save the business data to a file-like object or filepath.

        Note that it is recommended to provide a filepath instead of manually
        opening the file in write mode because that erases the file's contents.
        If an error occurs during serialization, the save file will be
        permanently lost.

        """
        if isinstance(f, io.BufferedReader):
            raise ValueError('Cannot write to file in binary mode')

        text = json.dumps(self.to_dict(), cls=JSONEncoder, indent=4)
        # TODO: encode in base64

        if isinstance(f, str):
            with open(f, 'w', encoding='utf-8') as f:
                f.write(text)
        else:
            # File-like object
            f.write(text)

    @staticmethod
    def _from_dict_deserialize(d: dict):
        balance = d.get('balance')
        inventory = d.get('inventory')
        if inventory is not None:
            d['inventory'] = Inventory.from_list(inventory)
        transactions = d.get('transactions')
        if transactions is not None:
            d['transactions'] = [Transaction.from_dict(d) for d in transactions]
        return d

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**cls._from_dict_deserialize(d))

    @classmethod
    def from_file(cls, f):
        return cls.from_dict(json.load(f, cls=JSONDecoder))
