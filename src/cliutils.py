import decimal

from . import utils


def input_boolean(prompt):
    def parse(s):
        if s in ('yes', 'y'):
            return True
        elif s in ('no', 'n'):
            return False
        return None

    ans = input(prompt).lower().strip()
    meaning = parse(ans)

    while meaning is None:
        ans = input('Unknown answer: ').lower().strip()
        meaning = parse(ans)

    return meaning


def input_integer(prompt, minimum=None, maximum=None):
    """

    Args:
        prompt (str): The initial message to prompt the user.
        minimum (Optional[int]): The minimum value (inclusive).
        maximum (Optional[int]): The maximum value (inclusive).

    """
    def parse(s):
        try:
            s = int(s)
        except ValueError:
            return 'Unknown integer: '
        if minimum is not None and s < minimum:
            return f'Must be above {minimum:,}: '
        elif maximum is not None and s > maximum:
            return f'Must be below {maximum:,}: '
        return s

    result = parse(input(prompt))
    while isinstance(result, str):
        result = parse(input(result))
    return result


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
        try:
            dollars = utils.parse_dollars(s)
        except ValueError:
            return 'Could not parse your amount: $'
        if minimum is not None and dollars < minimum:
            return f'Must be above {minimum:,}: $'
        elif maximum is not None and dollars > maximum:
            return f'Must be below {maximum:,}: $'
        return dollars

    if minimum is not None:
        minimum = decimal.Decimal(minimum)
    if maximum is not None:
        maximum = decimal.Decimal(maximum)

    result = parse(input(prompt))
    while isinstance(result, str):
        result = parse(input(result))
    return result
