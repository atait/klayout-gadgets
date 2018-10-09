
def isGSI():
    ''' Detect whether we are in klayout's generic scripting interface
        Since pya cannot be imported from outside, try that.
    '''
    try:
        import pya
        return True
    except ImportError:
        return False


def isGUI(preinitialization=False):
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


# determine what we will use for pya
if isGSI():
    import pya
else:
    try:
        import klayout.db as pya
    except ImportError as err:
        pya = None
