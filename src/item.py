from dataclasses import asdict, dataclass, field, replace
import decimal

from .utils import plural, round_dollars

__all__ = ['Item']


@dataclass
class Item:
    """A general purpose item, consisting of a name, quantity, unit,
    and total price.

    This data type uses the hash of its name, allowing it to work in sets
    and remain unique based on name.

    Items with the same name and unit can be added or subtracted from each
    other as such:
        >>> x = Item('Foo', 1, 'gram', '0.50')
        >>> y = Item('Foo', 1000, 'gram', '10')
        >>> x + y
        Item('Foo', 1001, 'gram', Decimal('10.50'))
        >>> y -= x
        >>> y
        Item('Foo', 999, 'gram', Decimal('9.50'))

    Args:
        name (str)
        quantity (int)
        unit (str): The unit that the quantity represents.
        price (decimal.Decimal):
            The cost of the entire item at its quantity in dollars.
            This field is automatically casted into decimal.Decimal.

    """
    name: str
    quantity: int = field(compare=False)
    unit: str = field(compare=False)
    price: decimal.Decimal = field(default_factory=decimal.Decimal, compare=False)

    def __post_init__(self):
        self.price = round_dollars(decimal.Decimal(self.price))

    def __str__(self):
        return '{q:,} {u} of {n}'.format(
            q=self.quantity,
            u=plural(self.unit, self.quantity),
            n=self.name
        )

    def __hash__(self):
        return hash((self.__class__, self.name))

    def __add__(self, other):
        if isinstance(other, self.__class__):
            if self.name != other.name:
                raise ValueError(f'Cannot add {other.name!r} to {self.name!r}')
            elif self.unit != other.unit:
                raise ValueError(
                    f'Cannot add item using {other.unit!r} units '
                    f'to another in {self.unit!r} units')
            return self.__class__(
                self.name,
                self.quantity + other.quantity,
                self.unit,
                self.price + other.price
            )
        return NotImplemented

    def __iadd__(self, other):
        if isinstance(other, self.__class__):
            if self.name != other.name:
                raise ValueError(f'Cannot add {other.name!r} to {self.name!r}')
            elif self.unit != other.unit:
                raise ValueError(
                    f'Cannot add item using {other.unit!r} units '
                    f'to another in {self.unit!r} units')
            self.quantity += other.quantity
            self.price += other.price
        else:
            raise TypeError(
                'Cannot add a {0.__name__} to an {1.__name__}'.format(
                    type(other), type(self)
                )
            )
        return self

    def __sub__(self, other):
        if isinstance(other, self.__class__):
            if self.name != other.name:
                raise ValueError(
                    f'Cannot subtract {other.name!r} from {self.name!r}')
            elif self.unit != other.unit:
                raise ValueError(
                    f'Cannot subtract item using {other.unit!r} units '
                    f'from another in {self.unit!r} units')
            return self.__class__(
                self.name,
                self.quantity - other.quantity,
                self.unit,
                self.price - other.price
            )
        return NotImplemented

    def __isub__(self, other):
        if isinstance(other, self.__class__):
            if self.name != other.name:
                raise ValueError(
                    f'Cannot subtract {other.name!r} from {self.name!r}')
            elif self.unit != other.unit:
                raise ValueError(
                    f'Cannot subtract item using {other.unit!r} units '
                    f'from another in {self.unit!r} units')
            self.quantity -= other.quantity
            self.price -= other.price
        else:
            raise TypeError(
                'Cannot subtract a {0.__name__} from an {1.__name__}'.format(
                    type(other), type(self)
                )
            )
        return self

    def copy(self, **kwargs):
        return replace(self, **kwargs)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**d)
