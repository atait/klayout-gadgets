from __future__ import print_function
from lygadgets import pya, isGUI

if isGUI():
    main_window = pya.Application.instance().main_window()
    message = lambda msg: main_window.message(msg, 5000)
    message_loud = lambda msg: pya.MessageBox.info('Message for you', msg, pya.MessageBox.Ok)
else:
    PINK = '\033[95m'
    NORMAL_COLOR = '\033[0m'
    message = print
    message_loud = lambda msg: print(PINK + str(msg), NORMAL_COLOR)