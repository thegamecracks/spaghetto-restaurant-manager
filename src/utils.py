def format_cents(cents):
    sign = '-' if cents < 0 else ''
    return '{}${}.{:02d}'.format(sign, abs(cents) // 100, abs(cents) % 100)


def parse_decimal(s: str):
    """Parse a decimal number into its whole and decimal parts.

    Returns:
        Tuple[int, int]

    Raises:
        ValueError

    """
    # Find the decimal point (and assert there aren't multiple points)
    point = s.find('.')
    if point == -1:
        point = len(s)
    elif s.count('.') > 1:
        raise ValueError('Too many decimal points')

    # Separate the whole and decimal part ("3", "14"),
    whole, decimal = s[:point], s[point+1:]
    whole = whole if whole else 0
    decimal = decimal if decimal else 0

    # Parse into integers and return them as a tuple
    return int(whole), int(decimal)


def parse_money(s: str):
    """Parse a decimal number into cents.

    Returns:
        int

    Raises:
        ValueError

    """
    whole, decimal = parse_decimal(s)
    if decimal >= 100:
        raise ValueError('Cannot exceed decimal precision of 2 '
                         '(over 99 cents)')
    cents = whole * 100 + decimal
    return cents
