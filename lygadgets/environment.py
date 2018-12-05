import os
import sys
from sys import platform

''' Detect whether we are in klayout's generic scripting interface
    Since pya cannot be imported from outside, try that.
'''
try:
    import pya
    _isGSI = True
except ImportError:
    _isGSI = False
isGSI = lambda: _isGSI


''' Klayout can run as a window or in batch mode on command line.
    If it launches in batch (-b) or database-only (-zz) mode, then main_window is None.

    If however it runs in non-GUI mode (-z), it is not None; however,
    it has not been given a title yet. (see layApplication.cc)
'''
if isGSI():
    import pya
    main = pya.Application.instance().main_window()
    if main is not None:
        _isGUI = True
    else:
        _isGUI = False
else:
    _isGUI = False
isGUI = lambda: _isGUI


def klayout_home():
    ''' Figure out the klayout configuration directory.
        Uses exactly the same logic as used in the klayout source.
    '''
    ly_home = os.environ.get('KLAYOUT_HOME', '')
    if ly_home == '':
        ly_home = os.path.join(os.path.expanduser('~'), 'KLayout' if is_windows() else '.klayout')
    if not os.path.exists(ly_home):
        print('The KLayout config directory was not found. KLayout might not be installed.')
        print('Creating it just in case that solves things')
        os.mkdir(ly_home)
        # raise FileNotFoundError('The KLayout config directory was not found. KLayout might not be installed.')
    return ly_home


def klayout_version():
    return '0.25.3'  # TODO: make this not hard coded


def is_windows():
    if platform == "linux" or platform == "linux2":
        return False
    elif platform == "darwin":
        return False
    elif platform == "win32":
        return True
    else:
        raise ValueError('Unrecognized operating system: {}'.format(platform))



### The important stuff happens below ###


''' Determine what we will use for pya.
    Do not override it with the standalone in sys.modules yet
    This statement:
        from lygadgets import pya
    will not error even if you are not in klayout GSI and don't have the klayout.db standalone
'''
if isGSI():
    import pya
    using_standalone = False
else:
    try:
        import klayout.db as pya
        using_standalone = True
    except ImportError as err:
        pya = None
        using_standalone = False


''' Spoof a whole bunch of stuff related to pya GUI.

    The problem this is trying to solve is when layout modules try to import GUI things and call them.
    When you run them in standalone, either those QElements don't exist, or they error for whatever reason.
    Nevertheless, you want to import that module to access its other functionality

    The desired behavior of these GUI things is pretty simple: don't error, do nothing.
    At the same time, we'd like the ability to override our override
    in case there are one or two important things, like instance.version() returning a string
'''

class NS_Catcher(type):
    ''' All this does is override the pya namespace with this class '''
    def __init__(cls, name, bases, dct):
        if pya is not None:
            setattr(pya, name, cls)
        super().__init__(name, bases, dct)

    def __getattr__(cls, attr):
        return PhonyClass()


class PhonyClass(metaclass=NS_Catcher):
    ''' It only ever gives instances of PhonyClass when called or as attributes.
        It is good for stifling those long chained calls like::

            pya.QFormBuilder().load(ui_file, pya.Application.instance().main_window()).findChild('ok').clicked(self.ok)

        That call will do nothing of course, but it also won't error.
    '''
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return PhonyClass()

    def __getattr__(self, attr):
        return PhonyClass()

    def __setattr__(self, attr, value):
        pass

    def __add__(self, other):
        return 0


def patch_environment():
    ''' Run this function, then your old scripts for klayout will work with the standalone.
        That's the idea anyways.

        Now we start changing things in the environment. Afterwards, this statement:
            import pya
        might give you regular pya or klayout.db, depending.

        GUI and Application things are added and/or spoofed.
    '''
    if using_standalone:
        sys.modules['pya'] = pya

    if not isGUI():
        class QMessageBox(PhonyClass): pass

        class QMessageBox_StandardButton(PhonyClass): pass

        class QFile(PhonyClass): pass

        class QIODevice(PhonyClass): pass

        class QFormBuilder(PhonyClass): pass

        class MessageBox(PhonyClass): pass

        class QDialog(PhonyClass): pass

        class Qt(PhonyClass): pass

    if not isGSI():
        ''' This should be present in the standalone but it is not yet '''
        try:
            pya.PCellDeclarationHelper
        except AttributeError:
            print('Warning: PCellDeclarationHelper not found in klayout.db')
            class PCellDeclarationHelper(PhonyClass): pass

        class PhonyInstance(PhonyClass):
            ''' This has to return a string sometimes '''
            def application_data_path(self):
                return klayout_home()

            def version(self):
                return klayout_version()

        class Application(PhonyClass):
            instance = PhonyInstance

        ''' Find the python modules that are present in klayout.
            These get lower import priority than system counterparts, if present
        '''
        if os.path.isdir(klayout_home()):
            for root, dirnames, filenames in os.walk(klayout_home(), followlinks=True):
                for dn in dirnames:
                    if dn == 'python':
                        sys.path.append(os.path.join(root, dn))


