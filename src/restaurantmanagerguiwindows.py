"""A set of windows built as functions.

Each window can return a stop boolean. If it returns True, the runner
should terminate.

Windows can also request other windows to be opened by returning their function.
Anything that is callable should be called by the runner.

Window functions are expected to clean up their own windows.
"""
import binascii
import decimal
import itertools
import json
import pathlib
from typing import List, Tuple, Optional
import zlib

import PySimpleGUI as sg

from . import utils
from .dish import Dish
from .manager import Manager
from .inventory import InventoryItem
from .item import Item
from .restaurantmanager import RestaurantManager
from .restaurantmanagerguiutils import input_integer, input_money
from .transaction import Transaction
from .transactiontype import TransactionType

TITLE = 'Spaghetto Manager 🍝'


def create_menu():
    """Creates a row containing the main menu.

    Since the manager's settings are not saved, the options provided
    for File are limited.

    """
    menu_def = [
        # ['File', ['Open...', 'Save', 'Save As...']]
        ['File', ['Reload', 'Save']]
    ]
    return [sg.Menu(menu_def)]


def close_and_return(stop, *windows: sg.Window):
    """A helper function for closing windows and returning."""
    for win in windows:
        win.close()
    return stop


def menu_event_handler(manager: Manager, win, event, values) \
        -> Tuple[Optional[bool], bool]:
    """Handles events for the main menu bar.

    :return: The stop condition and a reload condition.
        If the reload condition is true, the window should refresh its info.
    :rtype: tuple[bool, bool]

    """
    # if event == 'Open...':
    #     path = sg.popup_get_file(
    #         'Select the save file to open',
    #         default_path=pathlib.Path(manager.filepath).resolve(),
    #         default_extension='.sav',
    #         file_types=(('Save files', '.sav'),)
    #     )
    #     if path is not None:
    #         try:
    #             manager.reload_business(path)
    #         except (binascii.Error, UnicodeDecodeError,
    #                 json.JSONDecodeError, zlib.error) as e:
    #             sg.popup_error('Could not read the given save file.')
    #         else:
    #             manager.filepath = path
    if event == 'Reload':
        try:
            manager.reload_business()
        except (binascii.Error, UnicodeDecodeError,
                json.JSONDecodeError, zlib.error) as e:
            sg.popup_error('Could not read the save file.')
        else:
            sg.popup_ok('Successfully reloaded!')
            return None, True
    elif event == 'Save':
        try:
            manager.save_business()
        except PermissionError:
            sg.popup_error('Missing permissions to save!')
        else:
            sg.popup_ok('Successfully saved!')
    return None, False


def global_event_handler(manager: Manager, win, event, values) -> bool:
    """An event handler to fire for all windows.

    Window functions should return if this does not return None.

    """
    if event == sg.WIN_CLOSED:
        return True
    elif event.lower() in ('back', 'cancel'):
        return False


def setup_balance(manager: Manager):
    layout = [
        [sg.Text('Welcome to the Spaghetto Restaurant Manager!')],
        [sg.Text("What is your business's current balance? $"), sg.InputText(key='input')],
        [sg.Submit(), sg.Cancel()]
    ]
    win = sg.Window(TITLE, layout, finalize=True)

    while True:
        event, values = win.read()
        if (stop := global_event_handler(manager, win, event, values)) is not None:
            return stop
        elif event == 'Submit':
            try:
                balance = utils.parse_dollars(values['input'])
            except ValueError:
                continue

            manager.business.balance = balance
            return close_and_return(False, win)


def setup_employees(manager: Manager):
    layout = [
        [sg.Text("How many employees do you have? "), sg.InputText(key='input')],
        [sg.Submit(), sg.Cancel()]
    ]
    win = sg.Window(TITLE, layout, finalize=True)

    while True:
        event, values = win.read()
        if (stop := global_event_handler(manager, win, event, values)) is not None:
            return stop
        elif event == 'Submit':
            try:
                employees = int(values['input'])
            except ValueError:
                continue

            if employees > 0:
                manager.business.employee_count = employees
                return close_and_return(False, win)


def main(manager: RestaurantManager):
    def event_loop():
        while True:
            event, values = win.read()
            if (stop := global_event_handler(manager, win, event, values)) is not None:
                return stop
            stop, reload = menu_event_handler(manager, win, event, values)
            if stop is not None:
                return stop
            elif reload:
                update_date()
            if event == 'dishes':
                win.hide()
                if stop := main_dishes(manager):
                    return stop
                win.un_hide()
            elif event == 'finances':
                win.hide()
                if stop := main_finances(manager):
                    return stop
                win.un_hide()
            elif event == 'inventory':
                win.hide()
                if stop := main_inventory(manager):
                    return stop
                win.un_hide()
            elif event == 'step':
                business.step(weeks=4)
                update_date()

    def update_date():
        win.find_element('date').update(utils.format_date(business.total_weeks))

    business = manager.business

    menu_def = [
        ['hello', ['hello', ['hello', ['i like turtles']]]]
    ]
    layout = [
        create_menu(),
        [sg.Text(utils.format_date(business.total_weeks), key='date')],
        [sg.Button('Dishes', key='dishes'), sg.Button('Finances', key='finances')],
        [sg.Button('Inventory', key='inventory'), sg.Button('Next Month', key='step')]
    ]

    win = sg.Window(TITLE, layout, finalize=True, resizable=True)
    stop = event_loop()
    win.close()
    return stop


def main_dishes(manager: RestaurantManager):
    def event_loop():
        nonlocal dishes, selected_dish
        while True:
            event, values = win.read()
            if (stop := global_event_handler(manager, win, event, values)) is not None:
                return stop
            stop, reload = menu_event_handler(manager, win, event, values)
            if stop is not None:
                return stop
            elif reload:
                update_dishes()
            elif event == 'select':
                dish: List[Dish] = values.get(event)
                text: sg.Multiline = win.find('display')
                if dish:
                    selected_dish = dish[0]
                    text.update('{}\n{}'.format(
                        selected_dish.name, manager.describe_dish(selected_dish)
                    ))
                else:
                    selected_dish = None
                    text.update('Nothing selected')
            elif event == 'add':
                stop, dish = input_dish(manager)
                if stop:
                    return stop
                elif dish is not None:
                    business.dishes.add(dish)
                    update_dishes()
            elif event == 'remove':
                if selected_dish is None:
                    sg.popup_ok('Please select a dish to remove.')
                    continue

                if sg.popup_ok_cancel('Are you sure you want to remove this dish:',
                                      str(selected_dish)) == 'OK':
                    business.dishes.remove(selected_dish)
                    update_dishes()

    def update_dishes():
        nonlocal dishes
        dishes = tuple(d for d in business.dishes)
        selector: sg.Listbox = win.find('select')
        selector.update(dishes)

    business = manager.business

    dishes = tuple(d for d in business.dishes)
    selected_dish: Optional[Dish] = None

    layout = [
        create_menu(),
        [sg.Listbox(
            dishes, enable_events=True, key='select',
            size=(30, 5), select_mode=sg.LISTBOX_SELECT_MODE_SINGLE),
         sg.Multiline('Nothing selected', size=(30, 5), key='display')],
        [sg.Button('Back', key='back'), sg.Button('Add', key='add'),
         sg.Button('Remove', key='remove')]
    ]

    win = sg.Window(TITLE, layout, finalize=True, resizable=True)
    stop = event_loop()
    win.close()
    return stop


def input_dish(manager: RestaurantManager) -> Tuple[bool, Optional[Dish]]:
    """Prompt the user for a dish."""
    def event_loop():
        while True:
            event, values = win.read()
            if (stop := global_event_handler(manager, win, event, values)) is not None:
                return stop, None
            stop, reload = menu_event_handler(manager, win, event, values)
            if stop is not None:
                return stop, None
            elif reload:
                update_cost()
            elif event == 'add':
                stop, item = input_item(manager)
                if stop:
                    return stop, item
                elif item is not None:
                    items.append(item)
                    update_items()
                    update_cost()
            elif event == 'remove':
                selector: sg.Listbox = win.find('item')
                item: list = selector.get()
                item: Item = item[0] if item else None
                if item is not None:
                    del items[items.index(item)]
                    update_items()
                    update_cost()
            elif event == 'Submit':
                name: str = win.find('name').get().strip()
                if not name:
                    sg.popup_ok('Please input the name of your dish.')
                    continue
                elif name in business.dishes:
                    sg.popup_ok('A dish already exists with that name.')
                    continue

                if not items:
                    sg.popup_ok('Your dish must have at least one ingredient.')
                    continue

                price: str = win.find('price').get()
                try:
                    price: decimal.Decimal = utils.parse_dollars(price)
                except ValueError:
                    sg.popup_ok('Could not understand your price.')
                    continue
                if price < 0:
                    sg.popup_ok('Please price the dish at a positive value.')
                    continue

                return False, Dish(name, items, price)

    def update_cost():
        dish = Dish('Temp dish', items)
        cost = business.cost_of_dish(dish, 1, average=True, default=None)
        display: sg.Text = win.find('cost')
        if cost is not None:
            display.update(f'Estimated Cost to Produce: '
                           f'{utils.format_dollars(cost)}')
        else:
            display.update('Estimated Cost to Produce: N/A')

    def update_items():
        selector: sg.Listbox = win.find('item')
        selector.update(items)

    business = manager.business
    items = []

    layout = [
        [sg.Text('Name:'), sg.InputText(key='name')],
        [sg.Listbox(items, size=(30, 5), key='item', tooltip='Ingredients',
                    select_mode=sg.LISTBOX_SELECT_MODE_SINGLE)],
        [sg.Text('Estimated Cost to Produce: N/A', size=(40, 1), key='cost')],
        [sg.Text('Price: $'), sg.InputText(key='price')],
        [sg.Submit(), sg.Cancel(), sg.Button('Add Ingredient', key='add'),
         sg.Button('Remove Ingredient', key='remove')]
    ]

    win = sg.Window('Input dish', layout, finalize=True, resizable=True)
    stop, dish = event_loop()
    win.close()
    return stop, dish


def input_item(manager: Manager) -> Tuple[bool, Optional[Item]]:
    def event_loop() -> Tuple[bool, Optional[Item]]:
        nonlocal selected_item
        while True:
            event, values = win.read()
            if (stop := global_event_handler(manager, win, event, values)) is not None:
                return stop, None
            stop, reload = menu_event_handler(manager, win, event, values)
            if stop is not None:
                return stop, None
            elif reload:
                update_items()
            elif event == 'new':
                stop, selected_item = create_item(manager, no_cost=True)
                if stop:
                    return stop, selected_item
                elif selected_item is not None:
                    return False, selected_item
            elif event == 'select':
                selector: sg.Listbox = win.find('select')
                quantity_text: sg.Text = win.find('quantity_text')
                selected_item = selector.get()
                if selected_item:
                    selected_item = business.inventory[
                        selected_item[0]]
                    quantity_text.update(
                        f'{utils.plural(selected_item.unit).title()}:')
                else:
                    selected_item = None
                    quantity_text.update('Quantity:')
            elif event == 'Submit':
                if selected_item is None:
                    sg.popup_ok('Please select an item from the inventory.')
                    continue

                quantity_input: sg.InputText = win.find('quantity_input')
                try:
                    quantity = int(quantity_input.get())
                except ValueError:
                    sg.popup_ok('Quantity must be a positive integer.')
                    continue
                if quantity <= 0:
                    sg.popup_ok('Quantity must be at least 1.')
                    continue

                return False, Item(selected_item.name, quantity, selected_item.unit)

    def update_items():
        nonlocal items
        items = tuple(i.name for i in business.inventory)
        display: sg.Listbox = win.find('select')
        display.update(items)

    business = manager.business

    items = tuple(i.name for i in business.inventory)
    selected_item = None

    inv_layout = [
        [sg.Listbox(items, size=(30, 5), enable_events=True, key='select',
                    select_mode=sg.LISTBOX_SELECT_MODE_SINGLE)],
        [sg.Text('Quantity:', auto_size_text=True, key='quantity_text'),
         sg.InputText(size=(8, 1), key='quantity_input')]
    ]
    button_layout = [
        [sg.Button('Create New...', key='new')],
        [sg.Submit(), sg.Cancel()]
    ]
    layout = [
        [sg.Frame('Inventory', inv_layout), sg.Frame('', button_layout)]
    ]

    win = sg.Window('Input Item', layout, finalize=True, resizable=True)
    stop, item = event_loop()
    win.close()
    return stop, item


def create_item(manager: Manager, quantity_minimum=0, no_cost=False,
                add_to_inventory=True) \
        -> Tuple[bool, Optional[Item]]:
    """Prompt the user to create an item.

    :param Manager manager:
    :param quantity_minimum: The optional minimum quantity allowed (inclusive).
    :type quantity_minimum: int or None
    :param bool no_cost: If True, the item's price will not be queried.
    :param bool add_to_inventory: Adds the item to the business's inventory.
    :return: The stop and the Item if they successfully submitted.
    :rtype: tuple[bool, Item or None]

    """
    def event_loop() -> Tuple[bool, Optional[Item]]:
        while True:
            event, values = win.read()
            if (stop := global_event_handler(manager, win, event, values)) is not None:
                return stop, None
            stop, reload = menu_event_handler(manager, win, event, values)
            if stop is not None:
                return stop, None
            elif reload:
                update_existing()
            elif event == 'Submit':
                name_input: sg.InputText = win.find('name')
                name = name_input.get().strip()
                if not name:
                    sg.popup_ok('Please input the name of your new item.')
                    continue
                elif name.lower() in existing_names:
                    sg.popup_ok(f'"{name}" already exists in the inventory.')
                    continue

                quantity_input: sg.InputText = win.find('quantity')
                quantity = quantity_input.get()
                try:
                    quantity = int(quantity)
                    if quantity_minimum is not None and quantity < quantity_minimum:
                        raise ValueError('quantity is below minimum')
                except ValueError:
                    sg.popup_ok(f'Quantity must be an integer greater than '
                                f'{quantity_minimum:,}.')
                    continue

                unit_input: sg.InputText = win.find('unit')
                unit = unit_input.get().strip()

                if not unit:
                    sg.popup_ok('Please input the unit the item is measured in.')
                    continue

                if no_cost:
                    price = decimal.Decimal()
                else:
                    price_input: sg.InputText = win.find('price')
                    price = price_input.get()

                    try:
                        price = utils.parse_dollars(price, round_to_cent=False)
                    except ValueError:
                        sg.popup_ok('Could not understand the cost given.')
                        continue

                    if price > business.balance or price < 0:
                        sg.popup_ok("Your purchase will exceed the business's balance.")
                        continue
                    elif values['priceunit']:
                        # Price is per unit; multiply to get total
                        price *= quantity

                item = Item(name, quantity, unit, price)
                if add_to_inventory:
                    if price != 0:
                        if not business.buy_item(item):
                            sg.popup_ok('Failed to purchase the item.')
                            continue
                    else:
                        business.inventory.add(item)

                return False, item

    def update_existing():
        nonlocal existing_names
        existing_names = frozenset(i.name.lower() for i in business.inventory)

    business = manager.business
    existing_names = frozenset(i.name.lower() for i in business.inventory)

    layout = [
        [sg.Text('Item name:'), sg.InputText(key='name')],
        [sg.Text('Quantity:'), sg.InputText(key='quantity')],
        [sg.Text('Unit of quantity (gram, millilitre, cup...):'),
         sg.InputText(key='unit')]
    ]
    if not no_cost:
        layout.extend([
            [sg.Text('Cost: $'), sg.InputText(key='price')],
            [sg.Text('Cost type:'), sg.Radio('Total', 'pricetype', default=True, key='pricetotal'),
             sg.Radio('Per Unit', 'pricetype', key='priceunit')]
        ])
    layout.append([sg.Submit(), sg.Cancel()])

    win = sg.Window('Create Item', layout, finalize=True, resizable=True)
    stop, item = event_loop()
    win.close()
    return stop, item


def buy_existing_item(manager: Manager, invitem: InventoryItem, quantity_minimum=0) \
        -> Tuple[bool, Optional[Item]]:
    """

    :param manager:
    :param invitem:
    :param quantity_minimum: The optional minimum quantity allowed (inclusive).
    :type quantity_minimum: int or None
    :return: The stop and optional item that was added to invitem.
        You do not need to interact with the item.
    :rtype: tuple[bool, Item or None]

    """
    def event_loop() -> Tuple[bool, Optional[Item]]:
        while True:
            event, values = win.read()
            if (stop := global_event_handler(manager, win, event, values)) is not None:
                return stop, None
            stop, reload = menu_event_handler(manager, win, event, values)
            if stop is not None:
                return stop, None
            elif event == 'Submit':
                quantity_input: sg.InputText = win.find('quantity')
                quantity = quantity_input.get()
                try:
                    quantity = int(quantity)
                    if quantity_minimum is not None and quantity < quantity_minimum:
                        raise ValueError('quantity is below minimum')
                except ValueError:
                    sg.popup_ok(f'Quantity must be an integer greater than '
                                f'{quantity_minimum:,}.')
                    continue

                price_input: sg.InputText = win.find('price')
                price = price_input.get()
                try:
                    price = utils.parse_dollars(price, round_to_cent=False)
                except ValueError:
                    sg.popup_ok('Could not understand the cost given.')
                    continue

                if price > business.balance:
                    sg.popup_ok("Your purchase will exceed the business's balance.")
                    continue
                elif values['priceunit']:
                    # Price is per unit; multiply to get total
                    price *= quantity

                item = Item(invitem.name, quantity, invitem.unit, price)
                if not business.buy_item(item):
                    sg.popup_ok('Failed to purchase the item.')
                    return False, None
                else:
                    return False, item

    business = manager.business
    layout = [
        [sg.Text(f'{utils.plural(invitem.unit).capitalize()}:'), sg.InputText(key='quantity')],
        [sg.Text('Cost: $'), sg.InputText(key='price')],
        [sg.Text('Cost type:'), sg.Radio('Total', 'pricetype', default=True, key='pricetotal'),
         sg.Radio('Per Unit', 'pricetype', key='priceunit')],
        [sg.Submit(), sg.Cancel()]
    ]

    win = sg.Window('Buy Item', layout, finalize=True, resizable=True)
    stop, item = event_loop()
    win.close()
    return stop, item


def main_inventory(manager: Manager):
    def event_loop():
        nonlocal selected_item
        while True:
            event, values = win.read()
            if (stop := global_event_handler(manager, win, event, values)) is not None:
                return stop
            stop, reload = menu_event_handler(manager, win, event, values)
            if stop is not None:
                return stop
            elif reload:
                update_items()
            elif event == 'select':
                item: List[InventoryItem] = values.get(event)
                text: sg.Multiline = win.find('display')
                if item:
                    selected_item = item[0]
                    text.update('{}\n{}'.format(
                        selected_item.name, manager.describe_invitem(selected_item)
                    ))
                else:
                    selected_item = None
                    text.update('Nothing selected')
            elif event == 'buy':
                # Buy an existing item
                if selected_item is None:
                    sg.popup_ok('Please select an item.')
                    continue

                stop, item = buy_existing_item(manager, selected_item)
                if stop:
                    return stop
                elif item is not None:
                    update_items()
            elif event == 'buynew':
                stop, item = create_item(manager)
                if stop:
                    return stop
                elif item is not None:
                    business.inventory.add(item)
                    update_items()
            elif event == 'remove':
                if selected_item is None:
                    sg.popup_ok('Please select an item to remove.')
                    continue

                if sg.popup_ok_cancel(
                        'Are you sure you want to remove all of this item:',
                        str(selected_item)) == 'OK':
                    business.inventory.remove(selected_item)
                    update_items()

    def update_items():
        nonlocal items
        items = tuple(d for d in business.inventory)
        selector: sg.Listbox = win.find('select')
        selector.update(items)

    business = manager.business

    items = tuple(d for d in business.inventory)
    selected_item: Optional[InventoryItem] = None

    layout = [
        create_menu(),
        [sg.Listbox(
            items, enable_events=True, key='select',
            size=(30, 5), select_mode=sg.LISTBOX_SELECT_MODE_SINGLE),
         sg.Multiline('Nothing selected', size=(30, 5), key='display')],
        [sg.Button('Back', key='back'), sg.Button('Buy More...', key='buy'),
         sg.Button('Buy New...', key='buynew'), sg.Button('Remove', key='remove')]
    ]

    win = sg.Window(TITLE, layout, finalize=True, resizable=True)
    stop = event_loop()
    win.close()
    return stop


def main_finances(manager: Manager):
    def event_loop():
        while True:
            event, values = win.read()
            if (stop := global_event_handler(manager, win, event, values)) is not None:
                return stop
            stop, reload = menu_event_handler(manager, win, event, values)
            if stop is not None:
                return stop
            elif reload:
                update_employees()
                update_transactions('')
            elif event == 'empadd':
                num = input_integer('How many employees are you adding?',
                                    minimum=0)
                if num is not None and num != 0:
                    business.employee_count += num
                    update_employees()
            elif event == 'empsub':
                if business.employee_count <= 1:
                    sg.popup_ok('There are no more employees to remove.')
                    continue

                num = input_integer('How many employees are you removing?',
                                    minimum=0, maximum=business.employee_count - 1)
                if num is not None and num != 0:
                    business.employee_count -= num
                    update_employees()
            elif event.startswith('tranview'):
                update_transactions(event)

    def update_employees():
        frame: sg.Frame = win.find('emp')
        frame.update(f'Employees: {business.employee_count:,}')

    def format_transactions(transactions: List[Transaction]):
        """Return a string of transactions.
        Transactions occurring in the same week are grouped together."""
        transactions.reverse()
        lines = []
        for week, group in itertools.groupby(transactions, lambda t: t.week):
            lines.append(utils.format_date(week))
            lines.extend(f'{utils.format_dollars(t.dollars)}: {t.title}'
                         for t in group)

        return '\n'.join(lines)

    def update_transactions(event: str):
        nonlocal transactions
        type_ = None
        key = None
        if event == 'tranviewrev':
            type_ = TransactionType.SALES
        elif event == 'tranviewexp':
            key = lambda t: t.dollars < 0

        transactions = format_transactions(business.get_transactions(
            limit=30, type_=type_, key=key
        ))
        display: sg.Multiline = win.find('tran')
        display.update(transactions)

    business = manager.business

    employee_layout = [
        [sg.Button('Increase', key='empadd'), sg.Button('Decrease', key='empsub')]
    ]
    transactions = format_transactions(business.get_transactions(limit=30))
    transaction_layout = [
        [sg.Multiline(transactions, size=(50, 5), key='tran')],
        [sg.Text('Monthly revenue: '
                 + utils.format_dollars(business.get_monthly_revenue())),
         sg.Text('Monthly expenses: '
                 + utils.format_dollars(business.get_monthly_expenses()))],
        [sg.Radio('All', 'tranview', key='tranviewall', default=True, enable_events=True),
         sg.Radio('Revenue', 'tranview', key='tranviewrev', enable_events=True),
         sg.Radio('Expenses', 'tranview', key='tranviewexp', enable_events=True)]
    ]
    layout = [
        create_menu(),
        [sg.Frame(f'Employees: {business.employee_count:,}', employee_layout, key='emp'),
         sg.Frame('Transactions', transaction_layout)],
        [sg.Button('Back', key='back')]
    ]

    win = sg.Window(TITLE, layout, finalize=True, resizable=True)
    stop = event_loop()
    win.close()
    return stop
