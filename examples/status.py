try:
    import lygadgets
except ImportError:
    raise ImportError('you need lygadgets installed to do this demo')


try:
    import lyfoo
    print('lyfoo ({}) installed'.format(lyfoo.__version__))
except ImportError:
    print('lyfoo not found in system')

try:
    import lybar
    print('lybar ({}) installed'.format(lybar.__version__))
except ImportError:
    print('lybar not found in system')


try:
    from lybar import use_lyfoo
    lybar.use_lyfoo()
except:
    print('lybar failed to use lyfoo')

try:
    from lybar import get_technologies
    print('lybar says these technologies are installed' + str(get_technologies()))
except:
    print('lybar cannot get technologies')

try:
    from lybar import use_gui
    lybar.use_gui()
except:
    print('lybar cannot use GUI')
