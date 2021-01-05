"""Compile this script using --windowed mode."""
import json
from pathlib import Path

from src import Restaurant
from src.restaurantmanagergui import RestaurantManagerGUI

SAVE_BUSINESS = 'business.sav'
COMPRESSED = True


def main():
    if Path(SAVE_BUSINESS).is_file():
        try:
            manager = RestaurantManagerGUI.from_filepath(
                SAVE_BUSINESS, compressed=COMPRESSED)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            input('Error occurred during save file parsing.\n'
                  'Your save file may be corrupted.')
            return
    else:
        manager = RestaurantManagerGUI(Restaurant(), filepath=SAVE_BUSINESS,
                                       compressed=COMPRESSED)

    with manager.start_transaction():
        manager.run()


if __name__ == '__main__':
    main()
