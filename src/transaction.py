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

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**d)
