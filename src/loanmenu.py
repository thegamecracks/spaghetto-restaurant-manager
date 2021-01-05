import decimal
import random
from typing import Dict, Iterable

from .loaninteresttype import LoanInterestType
from .loanpaybacktype import LoanPaybackType
from .loanrequirement import LoanRequirement
from .loanrequirementtype import LoanRequirementType
from .inventory import Inventory
from .loan import Loan

__all__ = ['LoanMenu']


class LoanMenu(Inventory):
    """A subclass of Inventory designed for loans."""
    BANKS = ['RBC', 'TD', 'Scotiabank', 'BMO', 'CIBC']
    LOAN_NAMES = {
        'startup': ('Start Up', 'Entrepreneurship', 'Foundational'),
        'small business': ('Small Business', 'Small Businesses',
                           'Small Business Financing', 'Ontario Business'),
        'financial need': ('Financial Need', 'Financial Aid', 'Financial Relief',
                           'Extreme Relief')
    }
    _MISSING = object()
    _INV_TYPE = Loan
    _items: Dict[str, Loan]

    def __init__(self, items: Iterable[_INV_TYPE] = ()):
        super().__init__(items)

    def add(self, item: _INV_TYPE):
        return super().add(item)

    def discard(self, key: str):
        return super().discard(key)

    def find(self, key: str, default=None) -> _INV_TYPE:
        """Find an item that fuzzy matches the given name. Similar to get()."""
        return super().find(key, default)

    def get(self, key: str, default=None) -> _INV_TYPE:
        return super().get(key, default)

    def pop(self, key: str, default=_MISSING) -> _INV_TYPE:
        # Can't use super for this; _MISSING is unique to this class
        if default is self._MISSING:
            return self._items.pop(key)
        return self._items.pop(key, default)

    @classmethod
    def cast_to_inv_type(cls, obj) -> _INV_TYPE:
        if isinstance(obj, cls._INV_TYPE):
            return obj
        raise TypeError(
            f'Expected object of type {cls._INV_TYPE.__name__} '
            f'but received {obj!r} of type {type(obj).__name__}'
        )

    @classmethod
    def from_random(cls, length: int):
        """Create a LoanMenu with randomly generated loans."""
        def can_use_bound(bound: str, type_, rank):
            if bound == 'lower':
                return not any(type_ == t and rank in rank_req
                               for t, rank_req in no_lower_bound)
            elif bound == 'upper':
                return not any(type_ == t and rank in rank_req
                               for t, rank_req in no_upper_bound)
        bank_list = cls.BANKS.copy()
        bank_ranks = {bank: [] for bank in bank_list}
        loan_names = cls.LOAN_NAMES.copy()

        no_lower_bound = ((LoanRequirementType.MONTHLY_EXPENSE, ('startup',)),
                          (LoanRequirementType.MONTHLY_REVENUE, ('startup',)))
        no_upper_bound = ((LoanRequirementType.EMPLOYEES, ('startup',)),)

        loans = []
        while length:
            random.shuffle(bank_list)
            for bank in bank_list:
                # Pick between subsidy and loan (user decides term)
                kwargs = {'term': random.choice((0, None))}
                loan_type = 'Loan' if kwargs['term'] is None else 'Subsidy'

                # Pick rank and name that hasn't been used by the bank before
                rank, names = random.choice([
                    item for item in loan_names.items()
                    if item[0] not in bank_ranks[bank]
                ])
                bank_ranks[bank].append(rank)
                n = random.choice(names)
                if random.random() < 0.3:
                    # Surround with quotes
                    n = f'"{n}"'
                kwargs['name'] = f'{bank} {n} {loan_type}'

                amount = (2, 20)
                rate = (10, 39)
                if rank == 'startup' and kwargs['term'] is not None:
                    # Subsidy for startups
                    amount = (1, 4)
                elif kwargs['term'] is not None:
                    # Subsidy
                    amount = (2, 7)
                elif rank == 'financial need':
                    amount = (4, 14)
                    rate = (10, 30)

                kwargs['amount'] = decimal.Decimal(random.randint(*amount) * 5000)
                if kwargs['term'] is None:
                    kwargs['rate'] = decimal.Decimal(random.randint(*rate)) / 1000
                    # Use annual compound interest
                    kwargs['interest_type'] = LoanInterestType.COMPOUND_ANNUALLY
                    # User can decide how frequently to pay

                # Create random requirements
                requirements = []
                req_total = random.randint(1, len(LoanRequirementType))
                if rank == 'financial need':
                    # Always check revenue
                    req_types = [LoanRequirementType.MONTHLY_REVENUE]
                else:
                    # Always have at least one economic requirement
                    req_types_economic = [t for t in LoanRequirementType
                                          if t != LoanRequirementType.EMPLOYEES]
                    number = len(req_types_economic)
                    if rank != 'financial need':
                        number = random.randint(1, min(2, len(req_types_economic)))
                    req_types = random.sample(req_types_economic, number)
                # Always have employee requirement for small business rank
                if rank == 'small business' or random.randint(0, 1) and not rank == 'startup':
                    req_types.append(LoanRequirementType.EMPLOYEES)

                for type_ in req_types:
                    # Get the corresponding bound to generate values
                    # NOTE: these probabilities are hardcoded to the current
                    # requirement types available, so adding more types should
                    # also mean reworking this to continue giving realistic results
                    lower = upper = None
                    if type_ == LoanRequirementType.EMPLOYEES:
                        minimum, maximum = 1, 20
                    elif type_ == LoanRequirementType.MONTHLY_EXPENSE or rank == 'startup':
                        minimum, maximum = 1, 3
                    elif rank == 'financial need' and type_ == LoanRequirementType.MONTHLY_REVENUE:
                        minimum, maximum = 1, 3
                    else:
                        minimum, maximum = 2, 8

                    if can_use_bound('lower', type_, rank) and random.randint(0, 1):
                        # Add a lower bound
                        lower = random.randint(minimum, maximum)
                    if (lower is None or can_use_bound('upper', type_, rank)
                            and random.randint(0, 1)):
                        # Add an upper bound
                        if lower is not None:
                            if maximum - lower >= 10:
                                upper = random.randint(lower + 1, maximum)
                        else:
                            upper = random.randint(
                                minimum + maximum // 2, maximum)

                    if type_ != LoanRequirementType.EMPLOYEES:
                        if lower is not None:
                            lower *= 1000
                            if random.random() < 0.2:
                                lower -= 500
                        if upper is not None:
                            upper *= 1000
                            if random.random() < 0.2:
                                upper -= 500

                    if lower is not None:
                        lower = decimal.Decimal(lower)
                    if upper is not None:
                        upper = decimal.Decimal(upper)

                    # Create requirement
                    requirements.append({
                        'loan_type': type_.value,
                        'value': (lower, upper)
                    })
                    req_total -= 1
                    if req_total <= 0:
                        break

                kwargs['requirements'] = requirements

                # Create loan
                loans.append(Loan.from_dict(kwargs))
                length -= 1
                if length <= 0:
                    break

        # Sort loans by name
        loans.sort(key=lambda loan: loan.name)

        return cls(loans)
