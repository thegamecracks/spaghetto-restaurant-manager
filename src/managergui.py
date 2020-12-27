import PySimpleGUI as sg
import cmd
import contextlib
import datetime
import traceback

from . import utils
from .business import Business
from .inventory import Inventory
from .item import Item

sg.theme('BluePurple')

layout2 = [
          [sg.Text('Updating Text', key='-UPDATE-'), sg.In(key='-Input-')],
          [sg.Button('Show'), sg.Button('Exit')]]
window = sg.Window('Pattern 2B', layout2)

while True:  # Event Loop
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    if event == 'Show':
        print(values['-Input-'])


window.close()