import os
from sys import platform


def isGSI():
    ''' Detect whether we are in klayout's generic scripting interface
        Since pya cannot be imported from outside, try that.
    '''
    try:
        import pya
        return True
    except ImportError:
        return False


def isGUI():
    ''' Klayout can run as a window or in batch mode on command line.
        If it launches in batch (-b) or database-only (-zz) mode, then main_window is None.

        If however it runs in non-GUI mode (-z), it is not None; however,
        it has not been given a title yet. (see layApplication.cc)
    '''
    if isGSI():
        import pya
        main = pya.Application.instance().main_window()
        if main is not None:
            return True
    return False


def klayout_home():
    ''' Figure out the klayout configuration directory.
        Uses exactly the same logic as used in the klayout source.
    '''
    ly_home = os.environ.get('KLAYOUT_HOME', '')
    if ly_home == '':
        ly_home = os.path.join(os.path.expanduser('~'), 'KLayout' if is_windows() else '.klayout')
    if not os.path.exists(ly_home):
        raise FileNotFoundError('The KLayout config directory was not found. KLayout might not be installed.')
    return ly_home


def is_windows():
    if platform == "linux" or platform == "linux2":
        return False
    elif platform == "darwin":
        return False
    elif platform == "win32":
        return True
    else:
        raise ValueError('Unrecognized operating system: {}'.format(platform))


# determine what we will use for pya
if isGSI():
    import pya
else:
    try:
        import klayout.db as pya
    except ImportError as err:
        pya = None
