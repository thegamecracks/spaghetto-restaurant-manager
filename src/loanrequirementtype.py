import enum

__all__ = ['LoanRequirementType']


class LoanRequirementType(enum.IntEnum):
    """A loan requirement's type."""
    MONTHLY_REVENUE = 1
    MONTHLY_EXPENSE = 2
    EMPLOYEES = 3
