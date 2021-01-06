"""A set of windows built as functions.

Each window can return a stop boolean. If it returns True, the runner
should terminate.

Windows can also request other windows to be opened by returning their function.
Anything that is callable should be called by the runner.

Window functions are expected to clean up their own windows.
"""
import PySimpleGUI as sg

from . import utils
from .manager import Manager
from .restaurantmanager import RestaurantManager

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

    Window functions should return if this returns True.

    """
    if event in (sg.WIN_CLOSED, 'Cancel'):
        return True


def setup_balance(manager: Manager):
    layout = [
        [sg.Text('Welcome to the Spaghetto Restaurant Manager!')],
        [sg.Text("What is your business's current balance? $"), sg.InputText(key='input')],
        [sg.Submit(), sg.Cancel()]
    ]
    win = sg.Window(TITLE, layout, finalize=True)

    while True:
        event, values = win.read()
        if stop := global_event_handler(win, event, values):
            return close_and_return(stop, win)
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
        if stop := global_event_handler(win, event, values):
            return close_and_return(stop, win)
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
            if stop := global_event_handler(win, event, values):
                return stop
            elif stop := menu_event_handler(win, event, values):
                return stop
            elif event == 'dishes':
                win.hide()
                if stop := main_dishes(manager):
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
        while True:
            event, values = win.read()
            stop = global_event_handler(win, event, values)
            if stop := global_event_handler(win, event, values):
                return stop
            elif stop := menu_event_handler(win, event, values):
                return stop
            elif event == 'back':
                return False

    business = manager.business

    layout = [
        create_menu(),
        [sg.Button('Back', key='back')]
    ]

    win = sg.Window(TITLE, layout, finalize=True, resizable=True)
    stop = event_loop()
    win.close()
    return stop
