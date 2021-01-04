import decimal
from dataclasses import dataclass, asdict
from typing import Tuple, Optional

from . import utils
from .loanrequirementtype import LoanRequirementType

__all__ = ['LoanRequirement']


@dataclass(frozen=True)
class LoanRequirement:
    loan_type: LoanRequirementType
    value: Tuple[Optional[decimal.Decimal], Optional[decimal.Decimal]]
    description: str = None

    def __str__(self):
        if self.description is not None:
            return self.description

        v = self._format_value()
        if self.loan_type == LoanRequirementType.MONTHLY_REVENUE:
            return f'{v} in average revenue per month'
        elif self.loan_type == LoanRequirementType.MONTHLY_EXPENSE:
            return f'{v} in average expenses per month'
        elif self.loan_type == LoanRequirementType.EMPLOYEES:
            return f"employs {v} {utils.plural('person', v, 'people')}"
        return 'None'

    def _format_value(self):
        def format(v):
            if self.loan_type in (LoanRequirementType.MONTHLY_REVENUE,
                                  LoanRequirementType.MONTHLY_EXPENSE):
                return utils.format_dollars(v)
            return str(v)

        lower, upper = self.value
        if lower is not None:
            if upper is not None:
                return f'{format(lower)}-{format(upper)}'
            else:
                return f'at least {format(lower)}'
        elif upper is not None:
            return f'at most {format(upper)}'
        return 'None'

    def check(self, business) -> bool:
        """Check if a business meets this requirement.

        Args:
            business (Business)

        Returns:
            bool

        """
        def check_bounds(num):
            return ((self.value[0] is None or num >= self.value[0])
                    and (self.value[1] is None or num <= self.value[1]))

        if self.loan_type == LoanRequirementType.MONTHLY_REVENUE:
            return check_bounds(business.get_monthly_revenue())
        elif self.loan_type == LoanRequirementType.MONTHLY_EXPENSE:
            return check_bounds(business.get_monthly_expenses())
        elif self.loan_type == LoanRequirementType.EMPLOYEES:
            return check_bounds(business.employee_count)
        return False

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def _from_dict_deserialize(d: dict):
        loan_type = d.get('loan_type')
        if loan_type is not None:
            d['loan_type'] = LoanRequirementType(loan_type)
        value = d.get('value')
        if value is not None:
            d['value'] = tuple(value)
        return d

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**cls._from_dict_deserialize(d))
