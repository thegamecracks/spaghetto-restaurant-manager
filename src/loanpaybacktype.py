import enum

__all__ = ['LoanPaybackType']


class LoanPaybackType(enum.IntEnum):
    """Specifies how a loan should be paid back.

    The enum values correspond to the number of weeks.

    """
    WEEKLY = 1
    BIWEEKLY = 2
    MONTHLY = 4
    ANNUALLY = 48

    def __str__(self):
        return self.name.lower()
