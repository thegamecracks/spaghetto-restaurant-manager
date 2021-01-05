import PySimpleGUI as sg
from src import winlayouts

from src import utils
from .business import Business
from .restaurant import Restaurant
from .inventory import Inventory
from .item import Item
from .dish import Dish
from .dishmenu import DishMenu
from .manager import Manager, ManagerCLIBase, ManagerCLIMain
from .loan import Loan
from .loanmenu import LoanMenu
from .loanpaybacktype import LoanPaybackType
from .transaction import Transaction

import contextlib
import datetime
import traceback

sg.theme('BluePurple')

# not sure why error popups if i don't do it like this
init_layout = winlayouts.init_layout
main_menu_layout = winlayouts.main_menu_layout
inv_layout = winlayouts.inv_layout
buy_items_layout = winlayouts.buy_items_layout
new_item_layout = winlayouts.new_item_layout
dishes_layout = winlayouts.dishes_layout
add_dish_layout = winlayouts.add_dish_layout
finances_layout = winlayouts.finances_layout
employees_layout = winlayouts.employees_layout
loan_layout = winlayouts.loan_layout

business = Business
restaurant = Restaurant
manager = Manager
inv = Inventory()
loanmenu = LoanMenu()
dishinv = DishMenu()
balance = None
# initial business setup
if Business.balance is None:
    win1 = sg.Window('cool business placeholder', init_layout)
    while True:  # Event Loop
        event, values = win1.read()
        if event == sg.WIN_CLOSED or event == 'Exit':
            break
        if event == 'Enter':
            business.balance = int(utils.parse_dollars(values['-balinput-']))
            balance = int(utils.parse_dollars(values['-balinput-']))
            if business.employee_count is None:
                inputemployee = sg.popup_get_text('Please input the amount of employees in your business:')
                business.employee_count = int(inputemployee)
                if business.inventory is None:
                    inputitem = None
                    itemnum = 1
                    while inputitem != '':
                        inputitem = sg.popup_get_text(f"Lets set up your inventory! Input item {itemnum}'s name below "
                                                      "or nothing to setup later.")
                        if inputitem is '' or inputitem == 'Cancel':
                            break
                        inputquantity = int(sg.popup_get_text("Please input the quantity of the item."))
                        inputunit = sg.popup_get_text("Please input the unit (g,ml,cup) of the item.")
                        inputprice = utils.parse_dollars(
                            str(sg.popup_get_text("Please input the total price of the item. (type 'per' at the "
                                                  "end if you are specifying the unit price. $")))
                        item = Item(inputitem, inputquantity, inputunit, inputprice)
                        inv.add(item)
                        itemnum += 1
                    business.inventory = inv
    Business.generate_metadata(Business())
    loanmenu = LoanMenu.from_random(
                Business().RANDOM_LOAN_COUNT)
    print(loanmenu)
    for loan in loanmenu:
        print(loan.name)
    win1.close()


def menuloop():
    global balance
    # creates the windows to be used for the gui
    win1 = sg.Window('cool business placeholder', main_menu_layout)
    win2 = sg.Window('cool business placeholder', inv_layout)
    win2_1 = sg.Window('cool business placeholder', buy_items_layout)
    win2_2 = sg.Window('cool business placeholder', new_item_layout)
    win3 = sg.Window('cool business placeholder', dishes_layout)
    win3_1 = sg.Window('cool business placeholder', add_dish_layout)
    win4 = sg.Window('cool business placeholder', finances_layout)
    win4_1 = sg.Window('cool business placeholder', employees_layout)
    win5 = sg.Window('cool business placeholder', loan_layout)

    winbal_active = False
    win2_active = False
    win3_active = False
    win2_2_active = False
    win3_active = False
    win4_active = False
    win4_1_active = False
    win5_active = False
    # window event loop
    while True:
        event1, values1 = win1.read(timeout=100)
        if event1 == sg.WIN_CLOSED or event1 == 'Exit':
            break

        # check if button pressed was balance
        if event1 == 'Balance' and not winbal_active:
            balance_layout = [
                [sg.Text(f"Your business's balance is : {utils.format_dollars(Business.balance)}", )],
                [sg.Button('Back'), sg.Button('Add Balance')],
            ]
            winbal = sg.Window('cool business placeholder', balance_layout)
            winbal_active = True
            winbal.finalize()
            win1.Hide()
            winbal.UnHide()
            while True:
                eventbal, valuesbal = winbal.read()
                if eventbal == sg.WIN_CLOSED or eventbal == 'Back':
                    winbal.close()
                    winbal_active = False
                    win1.UnHide()
                    break
                if eventbal == 'Add Balance':
                    inputbal = sg.popup_get_text('Please input the amount you would like to add. $')
                    Business.balance += utils.parse_dollars(inputbal)
                    balance += utils.parse_dollars(inputbal)
                    winbal.close()
                    balance_layout = [
                        [sg.Text(f"Your business's balance is : {utils.format_dollars(Business.balance)}", )],
                        [sg.Button('Back'), sg.Button('Add Balance')],
                    ]
                    winbal = sg.Window('cool business placeholder', balance_layout)
                    winbal.finalize()

        # check if button pressed was inventory
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
                if event2 == 'Buy Items' and not win3_active:
                    win3_active = True
                    win2_1.finalize()
                    win2.Hide()
                    win2_1.UnHide()
                    while True:
                        event2_1, values2_1 = win2_1.read()
                        if event2_1 == sg.WIN_CLOSED or event2_1 == 'Cancel':
                            win2_1.Hide()
                            win3_active = False
                            win2.UnHide()
                            break
                        if event2_1 == 'Enter' and not win2_2_active and values2_1['-itemname-'] != '':
                            win2_2_active = True
                            win2_2.finalize()
                            win2_1.Hide()
                            itemname = values2_1['-itemname-']
                            win2_1['-itemname-'].update('')
                            win2_2.UnHide()
                            while True:
                                event2_2, values2_2 = win2_2.read()
                                if event2_2 == sg.WIN_CLOSED or event2_2 == 'Cancel':
                                    win2_2.Hide()
                                    win2_2_active = False
                                    win2_1.UnHide()
                                    win2_2_active = False
                                    break
                                if event2_2 == 'Enter' and values2_2['-itemquantity-'] != "" and values2_2[
                                    '-itemunit-'] != "" and values2_2['-itemprice-'] != None:
                                    itemquantity = int(values2_2['-itemquantity-'])
                                    itemunit = str(values2_2['-itemunit-'])
                                    itemprice = utils.parse_dollars(values2_2['-itemprice-'])
                                    item = Item(itemname, itemquantity, itemunit, itemprice)
                                    business.balance = balance
                                    business.buy_item(Business(), Item(itemname, itemquantity, itemunit, itemprice))
                                    inv.add(item)
                                    business.inv = inv
                                    win2_2['-itemquantity-'].update('')
                                    win2_2['-itemunit-'].update('')
                                    win2_2['-itemprice-'].update('')
                                    win2_2_active = False
                                    win2_2.Hide()
                                    win2_1.UnHide()
                                    break

                if event2 == 'List Items':
                    listboxitemvalues = []
                    for item in inv:
                        listboxitemvalues.append(item.name)
                    item_list_layout = [
                        [sg.Text('Inventory')],
                        [sg.Listbox(listboxitemvalues, size=(30, 6), enable_events=True, key=('-listboxselect-')),
                         sg.Text("Click on an item to view it's quantity, unit, and price.")],
                        [sg.Button('Back'), sg.Button('Show')]
                    ]
                    winlist = sg.Window('super cool business placeholder', item_list_layout)
                    win2.Hide()
                    winlist.finalize()
                    winlist.UnHide()
                    while True:
                        eventlist, valueslist = winlist.read()
                        if eventlist == sg.WIN_CLOSED or eventlist == 'Back':
                            winlist.Hide()
                            win2_active = True
                            win2.UnHide()
                            break
                        if eventlist is not None:
                            selectitem = inv[str(valueslist['-listboxselect-']).strip("'[]")]
                            print(valueslist['-listboxselect-'])
                            showitem = sg.popup(
                                f"You have {selectitem.quantity}{selectitem.unit}s of {selectitem.name} in stock.")

        if event1 == 'Dishes' and win3_active is False:
            win3.finalize()
            win3.UnHide()
            win3_active = True
            win1.active = False
            win1.Hide()
            while True:
                event3, values2_1 = win3.read()
                if event3 == sg.WIN_CLOSED or event3 == 'Back':
                    win3.Hide()
                    win3_active = False
                    win1_active = True
                    win1.UnHide()
                    break
                if event3 == 'Add Dish':
                    win3_1.finalize()
                    win3_1.UnHide()
                    win3.Hide()
                    while True:
                        event3_1, values3_1 = win3_1.read()
                        if event3_1 == sg.WIN_CLOSED or event3_1 == 'Cancel':
                            win3_1.Hide()
                            win3_active = True
                            win3.UnHide()
                            break
                        if event3_1 == 'Enter' and '-dishname-' is not '':
                            dishname = values3_1['-dishname-']
                            dishitemnum = 1
                            dishitem = None
                            dishrequirement = []
                            while dishitem != '':
                                dishitem = str(
                                    sg.popup_get_text(f"What is Item #{dishitemnum} (enter nothing to finish)"))
                                if inv.get(dishitem) is not None:
                                    unit = inv[dishitem].unit
                                    dishamount = int(sg.popup_get_text(
                                        f"What is the amount of {dishitem} needed? ({inv[dishitem].unit})"))
                                    dishrequirement.append(Item(dishitem, dishamount, unit, 0))
                                dishitemnum += 1
                            dishprice = utils.parse_dollars(
                                str(sg.popup_get_text("What should the price of the dish be? $")))
                            dish = Dish(dishname, dishrequirement, dishprice)
                            dishinv.add(dish)
                            restaurant.dishes = dishinv

                if event3 == 'List Dishes':
                    listboxdishvalues = []
                    for dish in dishinv:
                        print(dish)
                        print(dish.price)
                        listboxdishvalues.append(dish.name)
                    dish_menu_layout = [
                        [sg.Text('Dish Menu')],
                        [sg.Listbox(listboxdishvalues, size=(30, 6), enable_events=True, key=('-dishlistboxselect-')),
                         sg.Text("Click on a dish to view it's name, ingredients, and price.")],
                        [sg.Button('Back'), sg.Button('Show')]
                    ]
                    windishlist = sg.Window('super cool business placeholder', dish_menu_layout)
                    win3.Hide()
                    win3_active = False
                    windishlist.finalize()
                    windishlist.UnHide()
                    while True:
                        eventdishlist, valuesdishlist = windishlist.read()
                        if eventdishlist == sg.WIN_CLOSED or eventdishlist == 'Back':
                            windishlist.Hide()
                            win3_active = True
                            win3.UnHide()
                            break
                        if eventdishlist is not None:
                            selectdish = dishinv[str(valuesdishlist['-dishlistboxselect-']).strip("'[]")]
                            print(valuesdishlist['-dishlistboxselect-'])
                            ingredients = ""
                            dishcost = 0
                            for item in selectdish.items:
                                print(item)
                                if item.quantity > 1:
                                    plural = "s"
                                else:
                                    plural = ""
                                ingredients += f" {item.quantity} {item.unit}{plural} of {item.name},"
                                dishcost += Restaurant.cost_of_dish(Restaurant(), selectdish, 1, average=True)
                            showitem = sg.popup_scrolled(
                                f"Dish Name: {selectdish.name} ",
                                f"Ingredients: {ingredients}",
                                f"Price: ${selectdish.price}.",
                                f"Cost to produce: {utils.format_dollars(dishcost)}")

        if event1 == 'Finances' and win4_active is False:
            win4.finalize()
            win4.UnHide()
            win4_active = True
            win1.active = False
            win1.Hide()
            while True:
                event4, values4 = win4.read()
                if event4 == sg.WIN_CLOSED or event4 == 'Back':
                    win4.Hide()
                    win1_active = True
                    win4_active = False
                    win1.UnHide()
                    break
                if event4 == 'Employees' and not win4_1_active:
                    win4_1.finalize()
                    win4_1.UnHide()
                    win4.Hide()
                    win4_active = False
                    win4_1_active = True
                    while True:
                        event4_1, values4_1 = win4_1.read()
                        if event4_1 == sg.WIN_CLOSED or event4_1 == 'Back':
                            win4_1.Hide()
                            win1_active = True
                            win1.UnHide()
                            break
                        if event4_1 == 'Add Employees':
                            addemployee = int(sg.popup_get_text('How many employees would you like to add?'))
                            if addemployee != '':
                                business.employee_count += addemployee
                        if event4_1 == 'Remove Employees':
                            removeemployee = int(sg.popup_get_text('How many employees would you like to remove?'))
                            if removeemployee != '':
                                business.employee_count -= removeemployee

                if event4 == 'Loans' and not win5_active:
                    win5.finalize()
                    win5.UnHide()
                    win4.Hide()
                    win4_active = False
                    win5_active = True
                    while True:
                        event5, values5 = win5.read()
                        if event5 == sg.WIN_CLOSED or event5 == 'Back':
                            win5.Hide()
                            win4_active = True
                            win4.UnHide()
                            break
                        if event5 == 'View and Apply':
                            listboxloanvalues = []
                            for loan in loanmenu:
                                listboxloanvalues.append(loan.name)
                            loan_menu_layout = [
                                [sg.Text('Loan Menu')],
                                [sg.Listbox(listboxloanvalues, size=(30, 8), enable_events=True,
                                            key=('-loanlistboxselect-')),
                                 sg.Text("Click on a loan to view it's requirements, interest rate, and amount.")],
                                [sg.Button('Back'), sg.Button('Show')]
                            ]
                            winloanlist = sg.Window('super cool business placeholder', loan_menu_layout)
                            win5.Hide()
                            win5_active = False
                            winloanlist.finalize()
                            winloanlist.UnHide()
                            while True:
                                eventloanlist, valuesloanlist = winloanlist.read()
                                if eventloanlist == sg.WIN_CLOSED or eventloanlist == 'Back':
                                    winloanlist.Hide()
                                    win5_active = True
                                    win5.UnHide()
                                    winloanlist.Hide()
                                    break
                                if eventloanlist is not None:
                                    selectloan = loanmenu[str(valuesloanlist['-loanlistboxselect-']).strip("'[]")]

                                    rate_type = str(selectloan.interest_type)
                                    rate_frequency = selectloan.interest_type.frequency
                                    if rate_frequency:
                                        rate_type = f'{rate_frequency} {rate_type}ed'
                                    interestrate = '{} interest rate: {:%}'.format(
                                        rate_type.capitalize(),
                                        selectloan.rate
                                    )

                                    loanpayments = ('Payment frequency:', selectloan.payback_type)
                                    if selectloan.term is not None and selectloan.payback_type is not None:
                                        remaining_payments = selectloan.remaining_payments
                                        loanpayments = 'Total payments: {} ({})'.format(
                                            remaining_payments,
                                            str(selectloan.payback_type)
                                        )

                                    loaninfo = sg.popup_scrolled(
                                        f"{selectloan}",
                                        f"Amount: {utils.format_dollars(selectloan.amount)}",
                                        f"{interestrate}",
                                        f"{loanpayments}"
                                        f"{selectloan.requirements}"
                                    )


                if event4 == 'Revenue' and not win4_1_active:
                    beforebalance = balance
                    restaurant.update_sales(Restaurant())
                    restaurant.update_expenses(Restaurant())
                    print(restaurant.dishes)
                    displayrevenue = sg.popup(f" Your monthly revenue is {business.balance - beforebalance}")

        if event1 == 'Step' :
            businessdate = ManagerCLIMain.do_step(ManagerCLIMain(Manager(Business())), "d")
            datepopup = sg.popup(business.format_date(Business.total_weeks))
            print(business.total_weeks)





    win1.close()


menuloop()
