"""This GUI code is Spaghetto-certified, and by that
we mean this code is actual spaghetti"""
import PySimpleGUI as sg

from .guiutils import *
from .item import Item
from .manager import Manager
from .restaurant import Restaurant
from .restaurantmanager import RestaurantManager
from .winlayouts import *

sg.theme('BluePurple')


def rungui(manager: RestaurantManager):
  business = manager.business

  win1 = sg.Window('Spaghetto Manager 🍝', main_menu_layout)
  win2 = sg.Window('Spaghetto Manager 🍝 Inventory', inv_layout)
  win2_1 = sg.Window('Spaghetto Manager 🍝 Inventory', buy_items_layout)
  win2_2 = sg.Window('Spaghetto Manager 🍝 Inventory', new_item_layout)
  win3 = sg.Window('Spaghetto Manager 🍝 Dishes', dishes_layout)
  win3_1 = sg.Window('Spaghetto Manager 🍝 Dishes', add_dish_layout)
  win4 = sg.Window('Spaghetto Manager 🍝 Finances', finances_layout)
  win4_1 = sg.Window('Spaghetto Manager 🍝 Employees', employees_layout)
  win5 = sg.Window('Spaghetto Manager 🍝 Loans', loan_layout)

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
        [sg.Text(f"Your business's balance is : {utils.format_dollars(business.balance)}")],
        [sg.Button('Back'), sg.Button('Add Balance')],
      ]
      winbal = sg.Window('Spaghetto Manager 🍝', balance_layout, finalize=True)
      winbal_active = True
      win1.Hide()
      winbal.UnHide()
      while True:
        eventbal, valuesbal = winbal.read()
        if eventbal == sg.WIN_CLOSED or eventbal == 'Back':
          winbal.close()
          winbal_active = False
          win1.UnHide()
          break
        elif eventbal == 'Add Balance':
          money = input_money('Please input the amount you would like to add:', minimum=0)
          if money is None:
            winbal.close()
            winbal_active = False
            win1.UnHide()
            break
          elif money != 0:
            business.deposit("Owner Deposit", money)
            balance_layout[0][0].update(
              f"Your business's balance is : "
              f"{utils.format_dollars(business.balance)}"
            )

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
                  business.buy_item(Item(itemname, itemquantity, itemunit, itemprice))
                  win2_2['-itemquantity-'].update('')
                  win2_2['-itemunit-'].update('')
                  win2_2['-itemprice-'].update('')
                  win2_2_active = False
                  win2_2.Hide()
                  win2_1.UnHide()
                  break

        if event2 == 'List Items':
          listboxitemvalues = []
          for item in business.inventory:
            listboxitemvalues.append(item.name)
          item_list_layout = [
            [sg.Text('Inventory')],
            [sg.Listbox(listboxitemvalues, size=(30, 6), enable_events=True, key=('-listboxselect-')),
             sg.Text("Click on an item to view it's quantity, unit, and price.")],
            [sg.Button('Back'), sg.Button('Show')]
          ]
          winlist = sg.Window('Spaghetto Manager 🍝 Inventory', item_list_layout)
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
              item = business.inventory[str(valueslist['-listboxselect-']).strip("'[]")]
              print(valueslist['-listboxselect-'])
              sg.popup("You have {} {} of {} in stock.".format(
                 item.quantity,
                 utils.plural(item.unit, item.quantity),
                 item.name
              ))

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
                if business.inventory.get(dishitem) is not None:
                  unit = business.inventory[dishitem].unit
                  dishamount = int(sg.popup_get_text(
                    f"What is the amount of {dishitem} needed? ({business.inventory[dishitem].unit})"))
                  dishrequirement.append(Item(dishitem, dishamount, unit, 0))
                dishitemnum += 1
              dishprice = utils.parse_dollars(
                str(sg.popup_get_text("What should the price of the dish be? $")))
              manager.add_dish(dishname, dishrequirement, dishprice)

        if event3 == 'List Dishes':
          listboxdishvalues = []
          for dish in business.dishes:
            print(dish)
            print(dish.price)
            listboxdishvalues.append(dish.name)
          dish_menu_layout = [
            [sg.Text('Dish Menu')],
            [sg.Listbox(listboxdishvalues, size=(30, 6), enable_events=True, key=('-dishlistboxselect-')),
             sg.Text("Click on a dish to view it's name, ingredients, and price.")],
            [sg.Button('Back'), sg.Button('Show')]
          ]
          windishlist = sg.Window('Spaghetto Manager 🍝 Dishes', dish_menu_layout)
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
              selectdish = business.dishes[str(valuesdishlist['-dishlistboxselect-']).strip("'[]")]
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
            if event4_1 == 'Employee Count':
                sg.popup('Your business has {} {}.'.format(
                    business.employee_count,
                    utils.plural('employee', business.employee_count)
                ))

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
              for loan in business.metadata['loan_menu']:
                listboxloanvalues.append(loan.name)
              loan_menu_layout = [
                [sg.Text('Loan Menu')],
                [sg.Listbox(listboxloanvalues, size=(30, 8), enable_events=True,
                      key=('-loanlistboxselect-')),
                 sg.Text("Click on a loan to view it's requirements, interest rate, and amount.")],
                [sg.Button('Back'), sg.Button('Show')]
              ]
              winloanlist = sg.Window('Spaghetto Manager 🍝 Loans', loan_menu_layout)
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
                  loan = business.metadata['loan_menu'][str(valuesloanlist['-loanlistboxselect-']).strip("'[]")]
                  loandetails = ''

                  name = 'subsidy' if loan.is_subsidy else 'loan'

                  loandetails += f'Amount: {utils.format_dollars(loan.amount)}\n'
                  if not loan.is_subsidy:
                      rate_type = str(loan.interest_type)
                      rate_frequency = loan.interest_type.frequency
                      if rate_frequency:
                          rate_type = f'{rate_frequency} {rate_type}ed'
                      loandetails += '{} interest rate: {:%}\n'.format(
                          rate_type.capitalize(),
                          loan.rate
                      )
                      if loan.term is not None and loan.payback_type is not None:
                          remaining_payments = loan.remaining_payments
                          loandetails += 'Total payments: {} ({})\n'.format(
                              remaining_payments,
                              str(loan.payback_type)
                          )
                      elif loan.payback_type is not None:
                          # Can't calculate # of payments, user has to input the term
                          loandetails += f'Payment frequency: {loan.payback_type}\n'

                  qualified = loan.check(business)
                  if loan.requirements:
                      meets = 'meets' if qualified else 'does not meet'
                      loandetails += f'Your business {meets} the requirements for this {name}:\n'
                      for req in loan.requirements:
                        sign = '+' if req.check(business) else '-'
                        loandetails += f'{sign}, {req}'

                  loaninfo = sg.popup_scrolled(*loandetails.strip().split('\n'))


        if event4 == 'Revenue' and not win4_1_active:
          print(business.dishes)
          sg.popup(f" Your monthly revenue is {utils.format_dollars(business.get_monthly_revenue())}")

    if event1 == 'Step' :
      business.step(weeks=4)
      sg.popup(utils.format_date(business.total_weeks))

  win1.close()
