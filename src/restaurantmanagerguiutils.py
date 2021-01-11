import decimal
from typing import Optional

import PySimpleGUI as sg

from . import utils


def input_x(converter, prompt: str, minimum=None, maximum=None, default='',
            error_convert: str = 'Could not understand your input.',
            error_minimum: str = 'Number is too low.',
            error_maximum: str = 'Number is too high.'):
    num = sg.popup_get_text(
        prompt,
        default_text=default,
        no_titlebar=True,
        grab_anywhere=True,
        modal=True
    )

    if num is None:
        # User pressed cancel
        return

    try:
        num = converter(num)
    except ValueError:
        sg.popup_ok(error_convert)
        return

    if minimum is not None and num < minimum:
        sg.popup_ok(error_minimum)
    elif maximum is not None and num > maximum:
        sg.popup_ok(error_maximum)
    else:
        return num


def input_integer(prompt: str, minimum=None, maximum=None) -> Optional[int]:
    error_convert = 'Could not understand your number.'
    error_minimum = f'Number must be at least {minimum}.'
    error_maximum = f'Number must be at most {maximum}.'
    return input_x(
        int, prompt, minimum, maximum,
        error_convert=error_convert, error_minimum=error_minimum,
        error_maximum=error_maximum
    )


def input_money(prompt: str, minimum=None, maximum=None) -> Optional[decimal.Decimal]:
    error_convert = 'Could not understand your amount.'
    error_minimum = None
    error_maximum = None
    if minimum is not None:
        error_minimum = 'Amount must be at least {}.'.format(
            utils.format_dollars(minimum)
        )
    if maximum is not None:
        error_maximum = 'Amount must be at most {}.'.format(
            utils.format_dollars(maximum)
        )

    return input_x(
        utils.parse_dollars, prompt, minimum, maximum,
        error_convert=error_convert, error_minimum=error_minimum,
        error_maximum=error_maximum
    )
