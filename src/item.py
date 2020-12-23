class Item:
    """An inventory item.

    This data type uses the hash of its name, allowing it to work in sets
    and remain unique based on name.

    Items with the same name and unit can be added or subtracted from each
    other as such:
        >>> x = Item('Foo', 1, 'gram', 50)
        >>> y = Item('Foo', 1000, 'gram', 1000)
        >>> x + y
        Item('Foo', 1001, 'gram', 1050)
        >>> y -= x
        >>> y
        Item('Foo', 999, 'gram', 950)

    Args:
        name (str)
        quantity (int)
        unit (str): The unit that the quantity represents.
        price (int): The cost of the entire item at its quantity.

    """

    name = None  # this class variable's here just to make the linter stop complaining

    def __init__(self, name, quantity, unit, price):
        super().__setattr__('name', name)
        self.quantity = quantity
        self.unit = unit
        self.price = price

    def __repr__(self):
        return '{}({!r}, {!r}, {!r}, {!r})'.format(
            self.__class__.__name__, self.name, self.quantity,
            self.unit, self.price
        )

    def __str__(self):
        return f'{self.quantity} {self.name}'

    def __hash__(self):
        return hash((self.__class__, self.name))

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name
        return NotImplemented

    def __setattr__(self, key, value):
        if key == 'name':
            raise AttributeError('name cannot be changed after instantiation')
        elif key in ('quantity', 'price') and not isinstance(value, int):
            raise AttributeError(
                f'expected type int for {key} but received a {type(value)}')
        else:
            super().__setattr__(key, value)

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

    def to_dict(self):
        return {'name': self.name, 'quantity': self.quantity,
                'unit': self.unit, 'price': self.price}

    @classmethod
    def from_dict(cls, d):
        return cls(d['name'], d['quantity'], d['unit'], d['price'])
