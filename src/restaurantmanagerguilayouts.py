import PySimpleGUI as sg


setup_balance = [
    [sg.Text('Welcome to the Spaghetto Restaurant Manager!')],
    [sg.Text("What is your business's current balance? $"), sg.InputText(key='input')],
    [sg.Button('Enter'), sg.Button('Exit')]
]

setup_employees = [
    [sg.Text("How many employees do you have? "), sg.InputText(key='input')],
    [sg.Button('Enter'), sg.Button('Exit')]
]
