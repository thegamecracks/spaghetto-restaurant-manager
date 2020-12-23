"""This stores all info about the economics and inventory of the business
and provides methods for serializing to JSON and back."""
import json

from src.inventory import Inventory


class Business:
    """
    Args:
        balance (int): The business's balance in cents.
        inventory (Inventory): The inventory of the business.

    """

    def __init__(self, balance=None, inventory=None):
        self.balance = balance
        self.inventory = inventory

    def to_dict(self):
        return {'balance': self.balance, 'inventory': self.inventory.to_list()}

    def to_file(self, f):
        json.dump(self.to_dict(), f)

    @classmethod
    def from_dict(cls, d):
        balance = d.get('balance')
        inventory = d.get('inventory')
        if inventory is not None:
            inventory = Inventory.from_list(inventory)
        return cls(balance=balance, inventory=inventory)

    @classmethod
    def from_file(cls, f):
        return cls.from_dict(json.load(f))
