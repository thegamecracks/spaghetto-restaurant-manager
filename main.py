import json
from pathlib import Path

from src import Business, Manager

SAVE_BUSINESS = 'business.json'


def main():
    if Path(SAVE_BUSINESS).is_file():
        try:
            manager = Manager.from_filepath(SAVE_BUSINESS)
        except json.JSONDecodeError as e:
            print('Failed to load save file:\n error during parsing at '
                  f'line {e.lineno}, column {e.colno}')
            input('Your save file may be improperly modified. Please '
                  'correct any manual changes you have done if so.\n')
            return
    else:
        manager = Manager(Business(), filepath=SAVE_BUSINESS)

    with manager.start_transaction():
        manager.run()


if __name__ == '__main__':
    main()
