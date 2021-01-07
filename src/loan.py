from dataclasses import asdict, dataclass, field, replace
import decimal
from typing import List, Optional

from . import utils
from .loaninteresttype import LoanInterestType
from .loanpaybacktype import LoanPaybackType
from .loanrequirement import LoanRequirement

__all__ = ['Loan']


@dataclass
class Loan:
    """A loan/subsidy.

    Subsidies are specified by setting the `term` attribute to 0 and
    can be checked using the is_subsidy property (makes intentions clearer).

    The term and payback_type can be set to None, in which case the user
    interface should allow those attributes to be manually provided.

    """
    name: str
    term: Optional[int] = None  # years
    requirements: List[LoanRequirement] = field(default_factory=list)
    amount: decimal.Decimal = decimal.Decimal()
    rate: decimal.Decimal = decimal.Decimal()
    interest_type: LoanInterestType = LoanInterestType.SIMPLE
    payback_type: LoanPaybackType = None
    remaining_weeks: int = field(default=None, compare=False)

    def __post_init__(self):
        if self.remaining_weeks is None:
            self.reset_remaining_weeks()

    def __str__(self):
        return self.name

    @property
    def balance(self) -> decimal.Decimal:
        """Return the sum of the amount and interest due."""
        return self.amount + self.interest_due

    @property
    def interest_due(self) -> decimal.Decimal:
        return self.calculate_interest(
            self.amount,
            self.rate,
            self.interest_type,
            self.term
        )

    @property
    def is_subsidy(self):
        """If there is no term, this Loan object is a subsidy."""
        return self.term == 0

    @property
    def normal_payment(self) -> decimal.Decimal:
        """The normal amount to be given per payment."""
        if self.is_subsidy:
            return decimal.Decimal()
        num_payments = self.term * 48 // self.payback_type
        return utils.round_dollars(self.balance / num_payments)

    @property
    def final_payment(self) -> decimal.Decimal:
        """The amount to be given on the final payment
        (lower or equal to the normal payment)."""
        if self.is_subsidy:
            return decimal.Decimal()
        payment = self.balance % self.normal_payment
        return payment if payment != 0 else self.normal_payment

    @staticmethod
    def calculate_interest(principal: decimal.Decimal,
                           rate: decimal.Decimal,
                           rate_type: LoanInterestType,
                           term: int) -> decimal.Decimal:
        """Calculate the interest due for a principal value.

        Args:
            principal (decimal.Decimal): The amount of money borrowed.
            rate (decimal.Decimal): The interest rate as a decimal.
                Ex: 5% -> decimal.Decimal('0.05')
            rate_type (LoanInterestType): The amount of times the interest
                is compounded in a year. This is compatible with the
                LoanInterestType enum.
            term (int): The number of years.

        Returns:
            decimal.Decimal: The amount of interest to be added onto
                the principal.

        """
        if rate_type == LoanInterestType.SIMPLE:
            return principal * rate * term
        elif rate_type >= LoanInterestType.COMPOUND_ANNUALLY:
            n = rate_type
            return (principal * (1 + rate / n) ** (n * term)
                    ) - principal
        raise ValueError(f'Unknown interest type: {rate_type!r}')

    def get_next_payment(self, *, after_step=False) -> decimal.Decimal:
        """Return the next payment to be spent (normal_payment or
        final_payment based on remaining payments).

        By default, this is assumed to be after the business has stepped,
        and therefore remaining_weeks would have decremented. In this case,
        the final payment should be returned when remaining_payments is 0.

        However in the case that you are calculating this before time has
        stepped, you should set after_step to False so the final payment
        is returned when remaining_payments is 1.

        Args:
            after_step (bool): If True, the final payment is returned
                when remaining_payments == 0. Otherwise it is returned
                when it equals 1.

        Returns:
            decimal.Decimal

        """
        if self.remaining_payments < 2 - after_step:
            return self.final_payment
        return self.normal_payment

    @property
    def remaining_payments(self) -> decimal.Decimal:
        if self.is_subsidy:
            return decimal.Decimal()
        return self.remaining_weeks // self.payback_type

    def reset_remaining_weeks(self):
        """Reset the loan's remaining weeks back to the loan's term.

        If term is None, this is a no-op.

        """
        if self.term is not None:
            self.remaining_weeks = self.term * 48

    def check(self, business) -> bool:
        """Check if a business can qualify for this loan.

        Args:
            business (Business)

        Returns:
            bool

        """
        return all(req.check(business) for req in self.requirements)

    def copy(self, **kwargs):
        return replace(self, **kwargs)

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def _from_dict_deserialize(d: dict):
        requirements = d.get('requirements')
        if requirements is not None:
            d['requirements'] = [LoanRequirement.from_dict(req) for req in requirements]
        interest_type = d.get('interest_type')
        if interest_type is not None:
            d['interest_type'] = LoanInterestType(interest_type)
        payback_type = d.get('payback_type')
        if payback_type is not None:
            d['payback_type'] = LoanPaybackType(payback_type)
        return d

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**cls._from_dict_deserialize(d))
