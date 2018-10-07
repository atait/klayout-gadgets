import os
from sys import platform
import subprocess
from lygadgets.markup import xml_to_dict


def is_windows():
    if platform == "linux" or platform == "linux2":
        return False
    elif platform == "darwin":
        return False
    elif platform == "win32":
        return True
    else:
        raise ValueError('Unrecognized operating system: {}'.format(platform))


def symlink_windows(source, destination):
    # API based. The easy way
    try:
        os.symlink(source, destination)
        return
    except AttributeError:
        pass

    # Command line shell
    try:
        retval = subprocess.call(['ln', '-s', source, destination])
        assert retval == 0
        return
    except (subprocess.CalledProcessError, WindowsError, AssertionError):
        pass

    # Big magic with windows-specific package
    # From https://stackoverflow.com/questions/1447575/symlinks-on-windows
    try:
        import ctypes
        csl = ctypes.windll.kernel32.CreateSymbolicLinkW
        csl.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32)
        csl.restype = ctypes.c_ubyte
        flags = 0
        if source is not None and os.path.isdir(source):
            flags = 1
        if csl(destination, source, flags) == 0:
            raise ctypes.WinError('You do not have the permission to create a symbolic link.\nTry running as administrator')
        return
    except WindowsError:
        pass

    # Otherwise it didn't work
    raise WindowsError('Failed to find a way to link to a file in windows')


def link_to_salt(lypackage_dir):
    # Figure out the klayout configuration directory
    klayout_home = os.path.join(os.path.expanduser('~'), 'KLayout' if is_windows() else '.klayout')
    if not os.path.exists(klayout_home):
        raise FileNotFoundError('The KLayout config directory was not found. KLayout might not be installed.')

    salt_dir = os.path.join(klayout_home, 'salt')
    if not os.path.exists(salt_dir):
        os.mkdir(salt_dir)

    # Determine the lypackage name from the grain.xml
    with open(os.path.join(lypackage_dir, 'grain.xml')) as grain:
        registered_name = xml_to_dict(grain)['salt-grain']['name']
    salt_link = os.path.join(salt_dir, registered_name)

    # Make the symlink
    if not is_windows():
        os.symlink(lypackage_dir, salt_link)
    else:
        symlink_windows(lypackage_dir, salt_link)

    return salt_link


def post_install_factory(klayout_dot_config_dir):
    ''' Generates a class that subclasses install.
        It attempts to link the klayout_dot_config_dir into salt.
        It can be run by setup.py with the argument::

            cmdclass={'install': post_install_factory(some_directory)},
    '''
    class PostInstall(install):
        def run(self):
            install.run(self)
            try:
                the_link = link_to_salt(klayout_dot_config_dir)
                print('\n Autoinstall into klayout salt succeeded!\n{}\n'.format(the_link))
            except Exception as err:
                print('Autoinstall into klayout salt failed with the following\n')
                print(err)
                print('\nYou must perform a manual install as described in the README.')
    return PostInstall
