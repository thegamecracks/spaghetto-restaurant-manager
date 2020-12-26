"""This provides subclasses of JSONEncoder and JSONDecoder to support
de/serializing datetimes."""
import datetime
import functools
import json


__all__ = ['JSONDecoder', 'JSONEncoder']


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        else:
            return super().default(o)


def object_hook(d: dict):
    for k, v in d.items():
        try:
            d[k] = datetime.datetime.fromisoformat(v)
        except (TypeError, ValueError):
            pass
    return d


JSONDecoder = functools.partial(json.JSONDecoder, object_hook=object_hook)
