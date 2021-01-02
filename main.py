import json
from pathlib import Path

from src import Restaurant, RestaurantManager
from src import InventoryItem, Item
from src import utils

SAVE_BUSINESS = 'business.json'


def main():
    if Path(SAVE_BUSINESS).is_file():
        try:
            manager = RestaurantManager.from_filepath(SAVE_BUSINESS)
        except json.JSONDecodeError as e:
            print('Failed to load save file:\n error during parsing at '
                  f'line {e.lineno}, column {e.colno}')
            input('Your save file may be corrupted. Please '
                  'correct any manual changes you have done if so.\n')
            return
    else:
        manager = RestaurantManager(Restaurant(), filepath=SAVE_BUSINESS)

    with manager.start_transaction():
        manager.run()


if __name__ == '__main__':
    main()
