import decimal
from dataclasses import dataclass, asdict
from typing import Tuple, Optional

from . import utils
from .loanrequirementtype import LoanRequirementType

__all__ = ['LoanRequirement']


@dataclass
class LoanRequirement:
    loan_type: LoanRequirementType
    value: Tuple[Optional[decimal.Decimal], Optional[decimal.Decimal]]

    def __str__(self):
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
        if self.loan_type == LoanRequirementType.MONTHLY_REVENUE:
            revenue = business.get_monthly_revenue()
            return self.value[0] < revenue < self.value[1]
        elif self.loan_type == LoanRequirementType.MONTHLY_EXPENSE:
            expense = business.get_monthly_expense()
            return self.value[0] < expense < self.value[1]
        elif self.loan_type < LoanRequirementType.EMPLOYEES:
            return self.value[0] < business.employee_count < self.value[1]
        return False

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**d)
