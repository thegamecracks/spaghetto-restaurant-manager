import enum

__all__ = ['LoanInterestType']


class LoanInterestType(enum.IntEnum):
    """The type of interest a loan uses."""
    SIMPLE = 0
    COMPOUND_ANNUALLY = 1
    COMPOUND_MONTHLY = 12
    COMPOUND_BIWEEKLY = 24
    COMPOUND_WEEKLY = 48

    def __str__(self):
        name = self.name
        if name.startswith('COMPOUND'):
            return 'compound'
        return name.lower()

    @property
    def frequency(self):
        name = self.name
        if name.startswith('COMPOUND'):
            _, frequency = name.split('_')
            return frequency.lower()
        return ''
