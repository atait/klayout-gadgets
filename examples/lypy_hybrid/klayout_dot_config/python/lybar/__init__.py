__version__ = '0.0.1'

from lygadgets import pya, isGSI, isGUI, message_loud


def use_lyfoo():
    from lyfoo import add_one
    result = add_one(1)
    message_loud('lybar: According to lyfoo, 1 + 1 is {}.'.format(result))
    return result


def get_technologies():
    if isGSI() and True:
        return pya.Technology.technology_names()
    else:
        raise RuntimeError('Not in GSI')


def use_gui():
    if isGUI() and True:
        main = pya.Application.instance().main_window()
        main.create_layout(1)
    else:
        raise RuntimeError('Not in GUI')