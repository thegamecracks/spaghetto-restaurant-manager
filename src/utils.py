import decimal

__all__ = [
    'case_preserving_replace', 'format_cents', 'format_dollars',
    'fuzzy_match_word', 'parse_cents', 'parse_decimal', 'parse_dollars',
    'plural', 'round_dollars'
]


def case_preserving_replace(text, target, replacement, count=None):
    """A variant of str.replace that retains casing."""
    i = text.find(target)
    while i != -1 and (count is None or count > 0):
        capitalized = [c.isupper() for c in text[i:i + len(target)]]
        capitalized.extend([None for _ in range(
            len(replacement) - len(capitalized))])
        replacement = ''.join([
            char.upper() if capital else char
            for char, capital in zip(replacement, capitalized)
        ])
        text = text.replace(target, replacement, 1)
        i = text.find(target)
        if count is not None:
            count -= 1
    return text


def format_cents(cents: int):
    sign = '-' if cents < 0 else ''
    return '{}${}.{:02d}'.format(sign, abs(cents) // 100, abs(cents) % 100)


def format_dollars(dollars: decimal.Decimal):
    dollars = round_dollars(dollars)
    sign = '-' if dollars < 0 else ''
    dollar_part = abs(int(dollars))
    cent_part = abs(int(dollars % 1 * 100))
    return '{}${}.{:02d}'.format(sign, dollar_part, cent_part)


def fuzzy_match_word(s: str, choices: list, return_possible=False) -> str:
    """Matches a string to given choices by token (case-insensitive).

    Args:
        s (str)
        choices (Iterable[str])
        return_possible (bool): If this is True and there are multiple matches,
            a list of those matches will be returned.

    Returns:
        None: Returned if there are multiple matches and
              `return_possible` is False.
        str
        List[str]: Returned if there are multiple matches and
                   `return_possible` is True.

    """
    possible = choices
    possible_lower = [s.lower() for s in possible]

    # See if the phrase already exists
    try:
        i = possible_lower.index(s.lower())
        return possible[i]
    except ValueError:
        pass

    length = len(s)
    for word in s.lower().split():
        new = []

        for p, pl in zip(possible, possible_lower):
            if word in pl:
                new.append(p)

        possible = new

        count = len(possible)
        if count == 0:
            return
        elif count == 1:
            return possible[0]

        possible_lower = [s.lower() for s in possible]

    return possible if return_possible and possible else None


def parse_cents(s: str) -> int:
    """Parse a decimal number into cents.

    Returns:
        int

    Raises:
        ValueError

    """
    whole, rational = parse_decimal(s)
    if rational >= 100:
        raise ValueError('Cannot exceed decimal precision of 2 '
                         '(over 99 cents)')
    cents = whole * 100 + rational
    return cents


def parse_decimal(s: str) -> tuple:
    """Parse a decimal number into its whole and decimal parts.

    Returns:
        Tuple[int, int]

    Raises:
        ValueError

    """
    s = s.replace(',', '')
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


def parse_dollars(s: str) -> decimal.Decimal:
    """Parse a decimal number into Decimal."""
    whole, rational = parse_decimal(s)
    if rational >= 100:
        raise ValueError('Cannot exceed decimal precision of 2 '
                         '(over 99 cents)')
    # Pad with trailing zeros
    return decimal.Decimal(f'{whole}.{rational:<02d}')


def plural(s: str, n: int = 2, plural_version=None):
    """Pluralize a word using general rules.
    Reference:
        https://www.grammarly.com/blog/plural-nouns/

    """
    if n == 1:
        return s
    elif plural_version is not None:
        return plural_version

    vowels = frozenset('aeiou')
    fully_upper = s.isupper()
    if fully_upper:
        uppercases = [True for _ in s]
    else:
        uppercases = [c.isupper() for c in s]
    caseless = s.lower()

    suffix = 's'
    if caseless.endswith(('s', 'ss', 'sh', 'ch', 'x', 'z', 'o')):
        suffix = 'es'
    # elif caseless.endswith(('f', 'fe')):
    #     s = s[:-2] if caseless.endswith('fe') else s[:-1]
    #     s += 've'
    #     suffix = 's'
    elif caseless.endswith('y'):
        if caseless[-2] in vowels:
            suffix = 's'
        else:
            s = s[:-1]
            suffix = 'ies'
    elif caseless.endswith('us'):
        s = s[:-2]
        suffix = 'i'
    elif caseless.endswith('is'):
        s = s[:-2]
        suffix = 'es'
    elif caseless.endswith('on'):
        s = s[:-2]
        suffix = 'a'

    rough_join = s + suffix

    uppercases.extend([True if fully_upper else False
                       for _ in range(len(rough_join) - len(uppercases))])

    chars = []
    for c, uppercase in zip(rough_join, uppercases):
        chars.append(c.upper() if uppercase else c)

    return ''.join(chars)


def round_dollars(d) -> decimal.Decimal:
    """Round a number-like object to the nearest cent."""
    cent = decimal.Decimal('0.01')
    return decimal.Decimal(d).quantize(cent, rounding=decimal.ROUND_HALF_UP)
