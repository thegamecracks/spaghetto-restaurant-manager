import PySimpleGUI as sg
from src import business
# Window layouts to use in gui managers
sg.theme('BluePurple')

balance = business.Business.balance

# First launch layouts
init_layout = [
              [sg.Text("What is your business's current balance? $"), sg.InputText(key='-balinput-')],
              [sg.Button('Enter'), sg.Button('Exit')]]

item_num = 0
init_inv_layout = [
              [sg.Text("Let's set up your business's current inventory!")],
              [sg.Text("(if you intend to buy new items using your balance, skip this part)")],
              [sg.Text(f'Item # {item_num} name (type nothing to finish)'), sg.In(key='item_input')],
              [sg.Button('Show'), sg.Button('Exit')]]

# Menu layouts
main_menu_layout = [
    [sg.Text("Main Menu")],
    [sg.Text("")],
    [sg.Button('Balance'), sg.Button('Dishes'), sg.Button('Inventory'), sg.Button('Help')],
    [sg.Button('Exit')]]

inv_layout = [
    [sg.Text("Inventory Management")],
    [sg.Text("")],
    [sg.Button('Back'), sg.Button('Buy Items'), sg.Button('List Items'), sg.Button('Transaction History')]]

dishes_layout = [
    [sg.Text("Dishes Menu")],
    [sg.Text("")],
    [sg.Button('Add Dish'), sg.Button('List Dishes'), sg.Button('Show Dish'), sg.Button('Remove Dish'), sg.Button('Help')],
    [sg.Button('Exit')]]

# Menu layouts that menu layouts uses

# Main Menu layouts

# Inventory layouts
buy_items_layout = [
    [sg.Text("Purchase an item by name.")],
    [sg.Text("Name:"), sg.Input(key='itemname')],
    [sg.Button('Enter')],
    [sg.Button('Cancel')]]

new_item_layout = [
    [sg.Text("Create a new item to purchase.")],
    [sg.Text("Quantity to buy:"), sg.Input(key='-itemquantity-')],
    [sg.Text("Unit of item (g, ml):"), sg.Input(key='-itemunit-')],
    [sg.Text("Price in $:"), sg.Input(key='-itemprice-')],
    [sg.Button('Enter')],
    [sg.Button('Cancel')]]
