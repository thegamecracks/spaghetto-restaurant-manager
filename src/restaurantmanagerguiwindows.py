"""A set of windows built as functions.

Each window can return a stop boolean. If it returns True, the runner
should terminate.

Windows can also request other windows to be opened by returning their function.
Anything that is callable should be called by the runner.

Window functions are expected to clean up their own windows.
"""
import decimal
import itertools
from typing import List, Tuple, Optional

import PySimpleGUI as sg

from . import utils, Dish, Item, InventoryItem, Transaction
from .manager import Manager
from .restaurantmanager import RestaurantManager
from .restaurantmanagerguiutils import input_integer, input_money

TITLE = 'Spaghetto Manager 🍝'


def create_menu():
    """Creates a row containing the main menu."""
    menu_def = [
        ['hello', ['hello', ['hello', ['i like turtles']]]]
    ]
    return [sg.Menu(menu_def)]


def menu_event_handler(win, event, values) -> bool:
    """Handles events for the main menu bar."""


def close_and_return(stop, *windows: sg.Window):
    """A helper function for closing windows and returning."""
    for win in windows:
        win.close()
    return stop


def global_event_handler(win, event, values) -> bool:
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
        if (stop := global_event_handler(win, event, values)) is not None:
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
        if (stop := global_event_handler(win, event, values)) is not None:
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
            if (stop := global_event_handler(win, event, values)) is not None:
                return stop
            elif (stop := menu_event_handler(win, event, values)) is not None:
                return stop
            elif event == 'dishes':
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
                win.find_element('date').update(
                    utils.format_date(business.total_weeks))

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
            stop = global_event_handler(win, event, values)
            if (stop := global_event_handler(win, event, values)) is not None:
                return stop
            elif (stop := menu_event_handler(win, event, values)) is not None:
                return stop
            elif event == 'select':
                dish: List[Dish] = values.get(event)
                text: sg.Multiline = win.find('display')
                if dish:
                    selected_dish = dish[0]
                    text.update(manager.describe_dish(selected_dish))
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
                                      str(selected_dish)) == 'Yes':
                    business.dishes.remove(selected_dish)
                    update_dishes()

    def update_dishes():
        nonlocal dishes
        dishes = tuple(d for d in business.dishes)
        selector: sg.Listbox = win.find('select')
        selector.update(dishes)

    business = manager.business

    dishes = tuple(d for d in business.dishes)
    selected_dish = None

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
            stop = global_event_handler(win, event, values)
            if (stop := global_event_handler(win, event, values)) is not None:
                return stop, None
            elif (stop := menu_event_handler(win, event, values)) is not None:
                return stop, None
            elif event == 'add':
                stop, item = input_item(manager)
                if stop:
                    return stop, item
                elif item is not None:
                    items.append(item)
                    update_items()
            elif event == 'remove':
                selector: sg.Listbox = win.find('item')
                item: list = selector.get()
                item: Item = item[0] if item else None
                if item is not None:
                    del items[items.index(item)]
                    update_items()
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

    def update_items():
        selector: sg.Listbox = win.find('item')
        selector.update(items)

    business = manager.business
    items = []

    layout = [
        [sg.Text('Name:'), sg.InputText(key='name')],
        [sg.Listbox(items, size=(30, 5), key='item', tooltip='Ingredients',
                    select_mode=sg.LISTBOX_SELECT_MODE_SINGLE)],
        [sg.Text('Estimated Cost to Produce: N/A')],
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
            stop = global_event_handler(win, event, values)
            if (stop := global_event_handler(win, event, values)) is not None:
                return stop, None
            elif (stop := menu_event_handler(win, event, values)) is not None:
                return stop, None
            elif event == 'new':
                stop, selected_item = create_item(manager)
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


def create_item(manager: Manager) -> Tuple[bool, Optional[Item]]:
    # TODO: create_item
    return False, None


def main_inventory(manager: Manager):
    def event_loop():
        nonlocal selected_item
        while True:
            event, values = win.read()
            stop = global_event_handler(win, event, values)
            if (stop := global_event_handler(win, event, values)) is not None:
                return stop
            elif (stop := menu_event_handler(win, event, values)) is not None:
                return stop
            elif event == 'select':
                item: List[InventoryItem] = values.get(event)
                text: sg.Multiline = win.find('display')
                if item:
                    selected_item = item[0]
                    text.update(manager.describe_invitem(selected_item))
                else:
                    selected_item = None
                    text.update('Nothing selected')
            elif event == 'add':
                stop, item = create_item(manager)
                if stop:
                    return stop
                elif item is not None:
                    price = input_money('What is the cost of your purchase?')
                    if price is not None:
                        business.inventory.add(item)
                        update_items()
            elif event == 'remove':
                if selected_item is None:
                    sg.popup_ok('Please select an item to remove.')
                    continue

                if sg.popup_ok_cancel('Are you sure you want to remove this item:',
                                      str(selected_item)) == 'Yes':
                    business.inventory.remove(selected_item)
                    update_items()

    def update_items():
        nonlocal items
        items = tuple(d for d in business.inventory)
        selector: sg.Listbox = win.find('select')
        selector.update(items)

    business = manager.business

    items = tuple(d for d in business.inventory)
    selected_item = None

    layout = [
        create_menu(),
        [sg.Listbox(
            items, enable_events=True, key='select',
            size=(30, 5), select_mode=sg.LISTBOX_SELECT_MODE_SINGLE),
         sg.Multiline('Nothing selected', size=(30, 5), key='display')],
        [sg.Button('Back', key='back'), sg.Button('Add', key='add'),
         sg.Button('Remove', key='remove')]
    ]

    win = sg.Window(TITLE, layout, finalize=True, resizable=True)
    stop = event_loop()
    win.close()
    return stop


def main_finances(manager: Manager):
    def event_loop():
        while True:
            event, values = win.read()
            stop = global_event_handler(win, event, values)
            if (stop := global_event_handler(win, event, values)) is not None:
                return stop
            elif (stop := menu_event_handler(win, event, values)) is not None:
                return stop
            elif event == 'empadd':
                num = input_integer('How many employees are you adding?',
                                    minimum=0)
                if num is not None and num != 0:
                    business.employee_count += num
                    update_employees()
            elif event == 'empsub':
                num = input_integer('How many employees are you removing?',
                                    minimum=0)
                if num is not None and num != 0:
                    business.employee_count -= num
                    update_employees()

    def update_employees():
        win.find('emp').update(f'Employees: {business.employee_count:,}')

    def format_transactions(transactions: List[Transaction]):
        """Return a string of transactions.
        Transactions occurring in the same week are grouped together."""
        transactions.reverse()
        lines = []
        for week, group in itertools.groupby(transactions, lambda t: t.week):
            lines.append(utils.format_date(week))
            lines.extend(f'{utils.format_dollars(t.dollars)}: {t.title}'
                         for t in transactions)

        return '\n'.join(lines)

    business = manager.business

    employee_layout = [
        [sg.Text(f'Employees: {business.employee_count:,}', key='emp')],
        [sg.Button('Increase', key='empadd')],
        [sg.Button('Decrease', key='empsub')]
    ]
    transactions = format_transactions(business.get_transactions(limit=30))
    # TODO: filter transactions by income/expenses
    transaction_layout = [
        [sg.Multiline(transactions, size=(50, 5))],
        [sg.Text('Monthly revenue: '
                 + utils.format_dollars(business.get_monthly_revenue())),
         sg.Text('Monthly expenses: '
                 + utils.format_dollars(business.get_monthly_expenses()))]
    ]
    layout = [
        create_menu(),
        [sg.Frame('Employee Management', employee_layout),
         sg.Frame('Transactions', transaction_layout)],
        [sg.Button('Back', key='back')]
    ]

    win = sg.Window(TITLE, layout, finalize=True, resizable=True)
    stop = event_loop()
    win.close()
    return stop
