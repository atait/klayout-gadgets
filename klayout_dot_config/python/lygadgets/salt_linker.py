import os
import subprocess
from setuptools.command.install import install
from importlib import import_module

from lygadgets.markup import xml_to_dict
from lygadgets.environment import klayout_home, is_windows


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
    ''' Platform independent. Returns the full paths of source and destination if the link was created, otherwise None for both
    '''
    source = os.path.realpath(source)
    dest = os.path.realpath(dest)
    if source == dest:
        # Prevent circular reference
        return None, None
    if os.path.exists(dest):
        if not overwrite:
            return None, None
        else:
            # remove TODO. use shutil
            return None, None
    if not is_windows():
        os.symlink(source, dest)
    else:
        symlink_windows(source, dest)
    return source, dest


def validate_is_lypackage(lypackage_prospective):
    ''' Raises an error with a description if this directory does
        not match the format of a klayout salt package.

        It must have a grain.xml that defines name and NO __init__.py
    '''
    fullpath = os.path.realpath(lypackage_prospective)
    try:
        with open(os.path.join(fullpath, 'grain.xml')) as grain:
            registered_name = xml_to_dict(grain.read())['salt-grain']['name']
    except FileNotFoundError as err:
        err.args = ((lypackage_prospective +
                     ' does not appear to be a klayout package.' +
                     'It must have a grain.xml file.\n' +
                     str(err.args[0])), ) + err.args[1:]
        raise
    except KeyError as err:
        raise FileNotFoundError((lypackage_prospective +
                                 ' : grain.xml does not define a "name" property.'))
    # Make sure not also a pypackage. That would be incorrect
    try:
        validate_is_pypackage(fullpath)
    except:
        pass
    else:
        raise FileNotFoundError((lypackage_prospective +
                                 ' : cannot have a grain.xml AND an __init__.py'))


def link_to_salt(lypackage_dir):
    '''
        Attempts to link the lypackage_dir into salt.
    '''
    # Determine the lypackage name from the grain.xml
    validate_is_lypackage(lypackage_dir)
    with open(os.path.join(lypackage_dir, 'grain.xml')) as grain:
        registered_name = xml_to_dict(grain.read())['salt-grain']['name']

    salt_dir = os.path.join(klayout_home(), 'salt')
    if not os.path.exists(salt_dir):
        os.mkdir(salt_dir)

    salt_link = os.path.join(salt_dir, registered_name)

    # Make the symlink
    return attempt_symlink(lypackage_dir, salt_link, overwrite=False)


def validate_is_pypackage(package_prospective):
    ''' Raises an error with a description if this directory does
        not match the format of a python package

        It must have __init__.py and NO grain.xml

        Also accepts module files ending with .py
    '''
    if os.path.isfile(package_prospective):
        if os.path.splitext(package_prospective)[1] != '.py':
            raise FileNotFoundError(package_prospective + ' not a python file')
        else:
            return

    if not os.path.exists(os.path.join(package_prospective, '__init__.py')):
        raise FileNotFoundError(package_prospective + ' does not appear to be a python package.')
    # Make sure not also a lypackage. That would be incorrect
    try:
        validate_is_lypackage(package_prospective)
    except:
        pass
    else:
        raise FileNotFoundError(package_prospective + ' cannot have a grain.xml AND an __init__.py')


def link_to_user_python(package_dir):
    '''
        Attempts to link the package_dir into klayout's standalone python directory.
    '''
    validate_is_pypackage(package_dir)
    python_dir = os.path.join(klayout_home(), 'python')
    if not os.path.exists(python_dir):
        os.mkdir(python_dir)
    package_name = os.path.splitext(os.path.basename(package_dir))[0]
    link = os.path.join(python_dir, package_name)
    return attempt_symlink(package_dir, link, overwrite=False)


from types import ModuleType
def link_installed_python(module):
    if type(module) is str:
        module = import_module(module)
    elif type(module) is not ModuleType:
        raise TypeError(module + ' must be either string or ModuleType')
    source_dir = module.__path__[0]
    return link_to_user_python(source_dir)


def link_any(any_source):
    ''' Directories take precedence over installed python module
    '''
    # Check this first because we can only call exists on strings
    if type(any_source) is ModuleType:
        return link_installed_python(any_source)

    if os.path.exists(any_source):
        try:
            return link_to_salt(any_source)
        except: pass
        try:
            return link_to_user_python(any_source)
        except: pass
    else:
        try:
            return link_installed_python(any_source)
        except: pass
    raise FileNotFoundError(any_source + ' is neither a klayout salt package nor a python module/package.')


def postinstall_hook(source):
    ''' Generates a class that subclasses install.
        It attempts to link the lypackage_dir into salt.

        It can be run by setup.py with the argument::

            cmdclass={'install': post_install_factory(some_directory)},

        If you use pip, this sript will be blocked. So this method is no longer recommended.
        Instead, inform the user that they should run

            lygadgets_link yourpackage

        on the command line, after installing via pip
    '''
    class PostInstall(install):
        def run(self):
            install.run(self)
            try:
                the_link = link_any(source)
                if the_link is not None:
                    print('\nAutoinstall into klayout succeeded!\n{}\n'.format(the_link))
                else:
                    print('Folder already present. Not overwriting.')
            except Exception as err:
                print('Autoinstall into klayout failed with the following\n')
                print(err)
                print('\nYou must perform a manual install as described in a README.')
    return PostInstall
