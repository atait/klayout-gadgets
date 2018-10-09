from lygadgets import pya, isGUI, isGSI

global message, message_loud

PINK = '\033[95m'
NORMAL_COLOR = '\033[0m'

def commandline_message_funcs():
    message = print
    message_loud = lambda msg: print(PINK + str(msg), NORMAL_COLOR)
    return message, message_loud

message, message_loud = commandline_message_funcs()  # default. always safe

def fix_messaging():
    ''' This is called early by an auto-run lym. It makes sure.
    '''
    global message, message_loud
    if isGUI(preinitialization=True) and True:
        main_window = pya.Application.instance().main_window()
        message = lambda msg: main_window.message(msg, 5000)
        message_loud = lambda msg: pya.MessageBox.info('Message for you', msg, pya.MessageBox.Ok)
    else:
        pass
        # Fix it up so other programs' messages will redirect where we want
        # if isGSI():
        #     def fake_messageBox(title, msg, *args, **kwargs):
        #         message_loud(msg)
        #     pya.MessageBox.info = fake_messageBox

        #     instance_class = type(pya.Application.instance())
        #     class FakeMainMessager(object):
        #         def __init__(self):
        #             self.windowTitle = ''

        #         def message(self, msg, *args, **kwargs):
        #             message(msg)
        #     instance_class.main_window = lambda self: FakeMainMessager()
