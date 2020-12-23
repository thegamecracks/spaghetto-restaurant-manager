from pathlib import Path

from src import Business, Manager

SAVE_BUSINESS = 'business.json'


def get_total_cost(inventory):
    """Get the total cost of a collection of Items.

    This could be put into its own class which holds the items.

    """
    return sum(item.price for item in inventory)


def main():
    if Path(SAVE_BUSINESS).is_file():
        manager = Manager.from_filepath(SAVE_BUSINESS)
    else:
        manager = Manager(Business(), filepath=SAVE_BUSINESS)

    manager.run()


if __name__ == '__main__':
    main()
