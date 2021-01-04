from dataclasses import asdict, dataclass, field
import decimal

from . import utils
from .transactiontype import TransactionType

__all__ = ['Transaction']


@dataclass
class Transaction:
    title: str
    dollars: decimal.Decimal
    week: int
    transaction_type: TransactionType = field(default=TransactionType.DEFAULT)

    def __str__(self):
        return 'W{week} : {dollars} : {title}'.format(
            week=self.week,
            dollars=f"{utils.format_dollars(self.dollars)}",
            title=self.title
        )

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def _from_dict_deserialize(d: dict):
        transaction_type = d.get('transaction_type')
        if transaction_type is not None:
            d['transaction_type'] = TransactionType(transaction_type)
        return d

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**cls._from_dict_deserialize(d))
