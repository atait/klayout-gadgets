try:
    import lyfoo
    print('lyfoo found')
except ImportError:
    print('lyfoo not found in system')

try:
    import lybar
    print('lybar found')
except ImportError:
    print('lybar not found in system')
