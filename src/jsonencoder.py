"""This provides subclasses of JSONEncoder and JSONDecoder to support
de/serializing more objects."""
import decimal
import functools
import json


__all__ = ['JSONDecoder', 'JSONEncoder']


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        # if isinstance(o, (datetime.datetime, datetime.date)):
        #     return o.isoformat()
        if isinstance(o, decimal.Decimal):
            return str(o)
        elif hasattr(o, 'to_dict'):
            return o.to_dict()
        elif hasattr(o, 'to_list'):
            return o.to_list()
        return super().default(o)


def object_hook(d: dict):
    def to_decimal(v):
        if isinstance(v, (int, float)):
            raise ValueError('tried converting a non-string into a decimal')
        return decimal.Decimal(v)
    casts = (
        # datetime.date.fromisoformat,
        # datetime.datetime.fromisoformat,
        to_decimal,
    )
    for k, v in d.items():
        for c in casts:
            try:
                d[k] = c(v)
            except (TypeError, ValueError, decimal.InvalidOperation):
                pass
            else:
                break

    return d


JSONDecoder = functools.partial(json.JSONDecoder, object_hook=object_hook)
