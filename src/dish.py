from .item import Item


class Dish:
    """A named dish consisting of items.

    Args:
        name (str)
        items (List[Item])

    """
    def __init__(self, name, items):
        self.name = name
        for i in items:
            i.price = 0
        self.items = items

    def __repr__(self):
        return '{}({!r}, {!r})'.format(
            type(self), self.name, self.items
        )

    def __str__(self):
        return self.name

    def to_dict(self):
        return {'name': self.name, 'items': self.items}

    @classmethod
    def from_dict(cls, d):
        name = d['name']
        items = [Item.from_dict(d) for d in d['items']]
        return cls(name, items)
