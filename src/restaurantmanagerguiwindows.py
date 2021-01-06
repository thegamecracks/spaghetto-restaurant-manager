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

TITLE = 'Spaghetto Manager 🍝'


def close_and_return(retval, *windows: sg.Window):
    """A helper function for closing windows and returning."""
    for win in windows:
        win.close()
    return retval


def global_event_handler(win, event, values) -> bool:
    """An event handler to fire for all windows.

    Window functions should return whatever this returns
    if it is not None.

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
        stop = global_event_handler(win, event, values)
        if stop is not None:
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
        stop = global_event_handler(win, event, values)
        if stop is not None:
            return close_and_return(stop, win)
        elif event == 'Submit':
            try:
                employees = int(values['input'])
            except ValueError:
                continue

            if employees > 0:
                manager.business.employee_count = employees
                return close_and_return(False, win)


def main(manager: Manager):
    layout = sg.Submit

