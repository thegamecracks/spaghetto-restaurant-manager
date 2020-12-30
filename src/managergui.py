import PySimpleGUI as sg
from src import winlayouts

from . import utils
from .business import Business
from .inventory import Inventory
from .item import Item

from . import utils, parse_money
from .business import Business

import contextlib
import datetime
import traceback

sg.theme('BluePurple')

init_layout = winlayouts.init_layout
main_menu_layout = winlayouts.main_menu_layout
inv_layout = winlayouts.inv_layout
buy_items_layout = winlayouts.buy_items_layout
new_item_layout = winlayouts.new_item_layout
balance_layout = []

if Business.balance is None:
    win1 = sg.Window('cool business placeholder', init_layout)
    while True:  # Event Loop
        event, values = win1.read()
        if event == sg.WIN_CLOSED or event == 'Exit':
            break
        if event == 'Enter':
            print(values['-balinput-'])
            Business.balance = int(parse_money(values['-balinput-']))
            print(Business.balance)
            break
    win1.close()


def menuloop():
    win1 = sg.Window('cool business placeholder', main_menu_layout)
    win2 = sg.Window('cool business placeholder', inv_layout)
    win3 = sg.Window('cool business placeholder', buy_items_layout)
    balance = Business.balance
    balance_layout = [
        [sg.Text(f"Your business's balance is : {utils.format_cents(balance)}", )],
        [sg.Button('Back')],
    ]
    winbal = sg.Window('cool business placeholder', balance_layout)
    winbal_active = False
    winbal.finalize()
    winbal.Hide()

    win2_active = False
    while True:

        event1, values1 = win1.read(timeout=100)
        if event1 == sg.WIN_CLOSED or event1 == 'Exit':
            break

        if event1 == 'Balance' and not winbal_active:
            win1.Hide()
            winbal.UnHide()
            while True:
                winbal_active = True
                eventbal, valuesbal = winbal.read()
                if eventbal == sg.WIN_CLOSED or eventbal == 'Back':
                    winbal.Hide()
                    winbal_active = False
                    win1.UnHide()
                    break

        if event1 == 'Inventory' and not win2_active:
            win2_active = True
            win2.finalize()
            win1.Hide()
            win2.UnHide()
            while True:
                event2, values2 = win2.read()
                if event2 == sg.WIN_CLOSED or event2 == 'Back':
                    win2.Hide()
                    win2_active = False
                    win1.UnHide()
                    break
                if event1 == 'Buy Items' and not win2_active:
                    win2_active = True
                    win2.finalize()
                    win1.Hide()
                    win2.UnHide()
                    while True:
                        event2, values2 = win2.read()
                        if event2 == sg.WIN_CLOSED or event2 == 'Back':
                            win2.Hide()
                            win2_active = False
                            win1.UnHide()
                            break

    win1.close()


menuloop()
