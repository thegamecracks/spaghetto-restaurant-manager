def cents_string(cents):
    return '${}.{:02d}'.format(cents // 100, cents % 100)
