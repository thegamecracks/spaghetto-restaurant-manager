import decimal

import PySimpleGUI as sg

from . import utils


def input_money(prompt, minimum=None, maximum=None) -> decimal.Decimal:
    """Accurately parse a decimal number in dollars into a Decimal.

    Args:
        prompt (str)
        minimum (Optional[numbers.Rational]):
            The minimum value in dollars (inclusive).
        maximum (Optional[numbers.Rational]):
            The maximum value in dollars (inclusive).

    Returns:
        decimal.Decimal

    """
    def parse(s):
        if s is None:
            return None
        try:
            dollars = utils.parse_dollars(s)
        except ValueError:
            return 'Could not parse your amount:'
        if minimum is not None and dollars < minimum:
            return f'Must be above {minimum:,}:'
        elif maximum is not None and dollars > maximum:
            return f'Must be below {maximum:,}:'
        return dollars

    if minimum is not None:
        minimum = decimal.Decimal(minimum)
    if maximum is not None:
        maximum = decimal.Decimal(maximum)

    result = parse(sg.popup_get_text(prompt))
    while isinstance(result, str):
        result = parse(sg.popup_get_text(result))
    return result
