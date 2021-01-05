import PySimpleGUI as sg

from .inventory import Inventory
from .managergui import rungui
from .restaurantmanager import RestaurantManager
from . import restaurantmanagerguilayouts as layouts
from . import utils

__all__ = ['RestaurantManagerGUI']


class RestaurantManagerGUI(RestaurantManager):
    def run(self):
        sg.theme('BluePurple')
        app = GUI(self)
        app.run()


class GUI:
    def __init__(self, manager: RestaurantManagerGUI):
        self.manager = manager

    def setup_business(self) -> bool:
        def setup_balance_handler():
            if event == 'Enter':
                try:
                    balance = utils.parse_dollars(values['input'])
                except ValueError:
                    return

                business.balance = balance
                return True

        def setup_employees_handler():
            if event == 'Enter':
                try:
                    employees = int(values['input'])
                except ValueError:
                    return

                if employees > 0:
                    business.employee_count = employees
                    return True

        business = self.manager.business
        prompts = []

        if business.balance is None:
            prompts.append((layouts.setup_balance, setup_balance_handler))
        if business.employee_count is None:
            prompts.append((layouts.setup_employees, setup_employees_handler))
        if business.inventory is None:
            business.inventory = Inventory()

        for layout, handler in prompts:
            win = sg.Window('Business Setup', layout, finalize=True)
            while True:
                event, values = win.read()
                if event in (sg.WIN_CLOSED, 'Exit'):
                    return True
                stop = handler()
                if stop:
                    win.close()
                    break

        return False

    def run(self):
        stop = self.setup_business()
        if stop:
            return
        rungui(self.manager)


class WindowSetup:
    def __init__(self):
        pass
