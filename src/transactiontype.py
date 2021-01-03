import enum

__all__ = ['TransactionType']


class TransactionType(enum.IntEnum):
    DEFAULT = 1
    PURCHASE = 2  # stocking inventory
    SALES = 3  # revenue made from sales
    LOAN = 4  # income or expense by loan
    SUBSIDY = 5  # income from subsidy
