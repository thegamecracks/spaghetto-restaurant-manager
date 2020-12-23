from src import Item
from src import utils


def get_total_cost(inventory):
    """Get the total cost of a collection of Items.

    This could be put into its own class which holds the items.

    """
    return sum(item.price for item in inventory)


def main():
    ice_cream = Item('Vanilla Ice Cream', 4, 'cup', 480)
    cheese = Item('Cheese', 300, 'gram', 400)

    inventory = {
        ice_cream,
        cheese
    }

    total_cost = get_total_cost(inventory)
    print(utils.cents_string(total_cost))

    # Add another cup of ice cream
    ice_cream += Item('Vanilla Ice Cream', 1, 'cup', 120)

    total_cost = get_total_cost(inventory)
    print(utils.cents_string(total_cost))


if __name__ == '__main__':
    main()
