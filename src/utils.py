def format_cents(cents):
    sign = '-' if cents < 0 else ''
    return '{}${}.{:02d}'.format(sign, abs(cents) // 100, abs(cents) % 100)
