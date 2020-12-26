"""This stores all info about the economics and inventory of the business
and provides methods for serializing to JSON and back."""
from dataclasses import dataclass
import datetime
import json

from src.inventory import Inventory
from src.jsonencoder import *


@dataclass
class Transaction:
    title: str
    cents: int
    timestamp: datetime.datetime

    def to_dict(self):
        return {'title': self.title, 'cents': self.cents,
                'timestamp': self.timestamp}

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


class Business:
    """
    Args:
        balance (Optional[int]): The business's balance in cents.
        inventory (Optional[Inventory]): The inventory of the business.
        transactions (Optional[List[Dictionary]]):
            The list of transactions the business has done.

    """

    def __init__(self, balance=None, inventory=None, transactions=None):
        self.balance = balance
        self.inventory = inventory
        if transactions is None:
            transactions = []
        self.transactions = transactions

    def add_transaction(self, title: str, cents: int):
        """Record a transaction.

        Args:
            title (str)
            cents (int): The change in balance in cents.
                For expenses, use negative values.

        """
        self.transactions.append(
            Transaction(
                title=title,
                cents=cents,
                timestamp=datetime.datetime.utcnow()
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

    def get_transactions(self, limit: int, after=None):
        """Get x transactions sorted by time.

        Args:
            limit (int): The number of transactions to obtain at most.
            after (Union[datetime.datetime, datetime.timedelta]):
                Get transactions either past a given datetime.

        """
        ordered_transactions = sorted(
            self.transactions, key=lambda t: t.timestamp)

        now = datetime.datetime.utcnow()
        if isinstance(after, datetime.timedelta):
            # Convert to datetime
            after = now - after

        if after is not None:
            query = [t for t in ordered_transactions if t.timestamp >= after]
        else:
            skip = len(ordered_transactions) - min(
                len(ordered_transactions), limit)
            query = ordered_transactions[skip:]

        return query

    def to_dict(self):
        return {'balance': self.balance, 'inventory': self.inventory.to_list(),
                'transactions': [t.to_dict() for t in self.transactions]}

    def to_file(self, f):
        json.dump(self.to_dict(), f, cls=JSONEncoder, indent=4)

    @classmethod
    def from_dict(cls, d):
        balance = d.get('balance')
        inventory = d.get('inventory')
        if inventory is not None:
            inventory = Inventory.from_list(inventory)
        transactions = d.get('transactions')
        if transactions is not None:
            transactions = [Transaction.from_dict(d) for d in transactions]

        return cls(balance, inventory, transactions)

    @classmethod
    def from_file(cls, f):
        return cls.from_dict(json.load(f, cls=JSONDecoder))
