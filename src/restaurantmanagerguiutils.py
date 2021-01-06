from typing import Optional

import PySimpleGUI as sg

import utils


def input_x(converter, prompt: str, minimum=None,
            error_convert: str = 'Could not understand your input.',
            error_minimum: str = 'Number is too low.'):
    num = sg.popup_get_text(
        prompt,
        no_titlebar=True,
        grab_anywhere=True,
        modal=True
    )
    try:
        num = converter(num)
    except TypeError:
        # User pressed cancel
        return
    except ValueError:
        sg.popup_ok(error_convert)
        return
    if minimum is not None and num < minimum:
        sg.popup_ok(error_minimum)
        return

    return num


def input_integer(prompt: str, minimum=None) -> Optional[int]:
    error_convert = 'Could not understand your number.'
    error_minimum = f'Number must be greater than {minimum}.'
    return input_x(int, prompt, minimum,
                   error_convert=error_convert,
                   error_minimum=error_minimum)


def input_money(prompt: str, minimum=None) -> Optional[int]:
    error_convert = 'Could not understand your amount.'
    error_minimum = None
    if minimum is not None:
        error_minimum = 'Amount must be greater than {}.'.format(
            utils.format_dollars(minimum)
        )

    return input_x(utils.parse_dollars, prompt, minimum,
                   error_convert=error_convert,
                   error_minimum=error_minimum)
