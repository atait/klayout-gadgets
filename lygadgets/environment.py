
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
        pya = None
