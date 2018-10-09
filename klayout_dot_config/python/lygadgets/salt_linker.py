import os
from sys import platform
import subprocess
from setuptools.command.install import install

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


def attempt_symlink(source, dest, overwrite=False):
    ''' Platform independent. Returns the destination if the link was created, otherwise None
    '''
    if source == dest:
        # Prevent circular reference
        return None
    if os.path.exists(dest):
        if not overwrite:
            return None
        else:
            # remove
            return None
    if not is_windows():
        os.symlink(source, dest)
    else:
        symlink_windows(source, dest)
    return dest


def link_to_salt(lypackage_dir):
    '''
        Attempts to link the lypackage_dir into salt.
    '''
    salt_dir = os.path.join(klayout_home(), 'salt')
    if not os.path.exists(salt_dir):
        os.mkdir(salt_dir)

    # Determine the lypackage name from the grain.xml
    with open(os.path.join(lypackage_dir, 'grain.xml')) as grain:
        registered_name = xml_to_dict(grain.read())['salt-grain']['name']
    salt_link = os.path.join(salt_dir, registered_name)

    # Make the symlink
    return attempt_symlink(lypackage_dir, salt_link, overwrite=False)


def link_to_user_python(package_dir):
    '''
        Attempts to link the package_dir into klayout's standalone python directory.
    '''
    python_dir = os.path.join(klayout_home(), 'python')
    if not os.path.exists(python_dir):
        os.mkdir(python_dir)
    package_name = os.path.basename(package_dir)
    link = os.path.join(python_dir, package_name)
    return attempt_symlink(package_dir, link, overwrite=False)


def postinstall_factory(source, linker_function):
    ''' Generates a class that subclasses install.
        It attempts to link the lypackage_dir into salt.
        It can be run by setup.py with the argument::

            cmdclass={'install': post_install_factory(some_directory)},
    '''
    class PostInstall(install):
        def run(self):
            install.run(self)
            try:
                the_link = linker_function(source)
                if the_link is not None:
                    print('\nAutoinstall into klayout succeeded!\n{}\n'.format(the_link))
                else:
                    print('Folder already present. Not overwriting.')
            except Exception as err:
                print('Autoinstall into klayout failed with the following\n')
                print(err)
                print('\nYou must perform a manual install as described in a README.')
    return PostInstall


def postinstall_lypackage(lypackage_dir):
    return postinstall_factory(lypackage_dir, link_to_salt)


def postinstall_pure(package_dir):
    return postinstall_factory(package_dir, link_to_user_python)

