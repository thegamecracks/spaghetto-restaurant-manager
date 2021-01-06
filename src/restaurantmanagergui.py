import PySimpleGUI as sg

from .inventory import Inventory
from .restaurantmanager import RestaurantManager
from . import restaurantmanagerguiwindows as windows
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
        business = self.manager.business
        prompts = []

        if business.balance is None:
            prompts.append(windows.setup_balance)
        if business.employee_count is None:
            prompts.append(windows.setup_employees)
        if business.inventory is None:
            business.inventory = Inventory()

        for window in prompts:
            stop = window(self.manager)
            if stop:
                return stop

        return False

    def run(self):
        """Run the GUI."""
        sg.theme('Topanga')
        stop = self.setup_business()
        if stop:
            return
        win = windows.main(self.manager)

        while callable(win):
            win = win(self.manager)
