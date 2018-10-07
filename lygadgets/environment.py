
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
    ''' Klayout can run as a window or in batch mode on command line
    '''
    if isGSI():
        import pya
        if pya.Application.instance().main_window() is not None:
            return True
    return False


# determine what we will use for pya
if isGSI():
    import pya
else:
    try:
        import klayout.db as pya
    except ImportError as err:
        # err.args = ('klayout standalone is needed for non-GUI mode. It is not installed', ) + err.args[1:]
        print('Attempt to import pya and klayout.db failed')
        pya = None
