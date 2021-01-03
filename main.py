import json
from pathlib import Path

from src import Restaurant, RestaurantManager
from src import InventoryItem, Item
from src import utils

SAVE_BUSINESS = 'business.sav'
ENCRYPTED = True


def main():
    if Path(SAVE_BUSINESS).is_file():
        try:
            manager = RestaurantManager.from_filepath(SAVE_BUSINESS, encrypted=ENCRYPTED)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            input('Error occurred during save file parsing.\n'
                  'Your save file may be corrupted.')
            return
    else:
        manager = RestaurantManager(Restaurant(), filepath=SAVE_BUSINESS,
                                    encrypted=ENCRYPTED)

    with manager.start_transaction():
        manager.run()


if __name__ == '__main__':
    main()
