from dataclasses import asdict, dataclass, field
import decimal
import functools
import math
from typing import List

from . import utils
from .loanpaybacktype import LoanPaybackType
from .loanrequirement import LoanRequirement

__all__ = ['Loan']


@dataclass
class Loan:
    """A loan/subsidy.

    Subsidies are specified by setting the `term` attribute to 0 and
    can be checked using the is_subsidy property (makes intentions clearer).

    """
    name: str
    term: int  # years
    remaining_weeks: int = field(init=False)
    requirements: List[LoanRequirement] = field(default_factory=list)
    amount: decimal.Decimal = decimal.Decimal()
    rate: decimal.Decimal = decimal.Decimal()
    payback_type: LoanPaybackType = LoanPaybackType.MONTHLY

    def __post_init__(self):
        self.remaining_weeks = self.term * 12

    def __str__(self):
        return self.name

    @functools.cached_property
    def balance(self) -> decimal.Decimal:
        """Return the sum of the amount and interest due."""
        return self.amount + self.interest_due

    @functools.cached_property
    def interest_due(self) -> decimal.Decimal:
        return self.amount * self.rate * self.term

    @property
    def is_subsidy(self):
        """If there is no term, this Loan object is a subsidy."""
        return self.term == 0

    @functools.cached_property
    def normal_payment(self) -> decimal.Decimal:
        """The normal amount to be given per payment."""
        if self.is_subsidy:
            return decimal.Decimal()
        num_payments = self.term * 48 // self.payback_type
        return utils.round_dollars(self.balance / num_payments * 100)

    @functools.cached_property
    def final_payment(self) -> decimal.Decimal:
        """The amount to be given on the final payment
        (lower or equal to the normal payment)."""
        if self.is_subsidy:
            return decimal.Decimal()
        payment = self.balance % self.normal_payment
        return payment if payment != 0 else self.normal_payment

    def get_next_payment(self):
        """Return the next payment to be spent (normal_payment or
        final_payment based on remaining payments)."""
        # NOTE: Business will subtract from remaining_weeks before
        # paying the loan, so this should return final_payment for
        # 0 or 1 remaining payments
        if self.remaining_payments <= 1:
            return self.final_payment
        return self.normal_payment

    @property
    def remaining_payments(self):
        if self.is_subsidy:
            return decimal.Decimal()
        return self.remaining_weeks // self.payback_type

    def check(self, business) -> bool:
        """Check if a business can qualify for a loan.

        Args:
            business (Business)

        Returns:
            bool

        """
        return all(req.check(business) for req in self.requirements)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**d)
