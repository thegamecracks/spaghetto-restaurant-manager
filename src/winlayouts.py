import PySimpleGUI as sg
# Window layouts to use in gui managers
sg.theme('BluePurple')

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
    [sg.Button('Balance'), sg.Button('Dishes'), sg.Button('Inventory'), sg.Button('Finances'), sg.Button('Step'), sg.Button('Help')],
    [sg.Button('Exit')]]

inv_layout = [
    [sg.Text("Inventory Management")],
    [sg.Text("")],
    [sg.Button('Back'), sg.Button('Buy Items'), sg.Button('List Items')]]

dishes_layout = [
    [sg.Text("Dishes Menu")],
    [sg.Text("")],
    [sg.Button('Add Dish'), sg.Button('List Dishes'), sg.Button('Show Dish'), sg.Button('Help')],
    [sg.Button('Back')]]

finances_layout = [
    [sg.Text("Finances")],
    [sg.Text("")],
    [sg.Button('Employees'), sg.Button('Expenses'), sg.Button('History'), sg.Button('Loans'), sg.Button('Revenue')],
    [sg.Button('Back')]]

# Menu layouts that menu layouts uses

# Main Menu layouts

# Inventory layouts
buy_items_layout = [
    [sg.Text("Purchase an item by name.")],
    [sg.Text("Name:"), sg.Input(key='-itemname-')],
    [sg.Button('Enter')],
    [sg.Button('Cancel')]]

new_item_layout = [
    [sg.Text("Create a new item to purchase.")],
    [sg.Text("Quantity to buy:"), sg.Input(key='-itemquantity-')],
    [sg.Text("Unit of item (gram, millilitre, cup...):"), sg.Input(key='-itemunit-')],
    [sg.Text("Total price in $:"), sg.Input(key='-itemprice-')],
    [sg.Button('Enter')],
    [sg.Button('Cancel')]]

# Dishes layouts
add_dish_layout = [
    [sg.Text("What is the name of your new dish?")],
    [sg.Text("Name:"), sg.Input(key='-dishname-')],
    [sg.Button('Enter')],
    [sg.Button('Cancel')]]

# Finances layouts
employees_layout = [
    [sg.Text("Employees")],
    [sg.Text("")],
    [sg.Button('Add Employees'), sg.Button('Remove Employees'), sg.Button('Employee Count')],
    [sg.Button('Back')]]

loan_layout = [
    [sg.Text("Loan Management")],
    [sg.Text("")],
    [sg.Button('View and Apply'), sg.Button('Current Loans')],
    [sg.Button('Back')]]