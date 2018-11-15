from __future__ import print_function
try:  # python 2 does not have FileNotFoundError. Check it
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

import os
import subprocess
from setuptools.command.install import install
from importlib import import_module
from shutil import rmtree, copytree
from types import ModuleType

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


def lypackage_name(source):
    try:
        with open(os.path.join(source, 'grain.xml')) as grain:
            return xml_to_dict(grain.read())['salt-grain']['name']
    except FileNotFoundError as err:
        err.args = ((source +
                     ' does not appear to be a klayout package.' +
                     'It must have a grain.xml file.\n' +
                     str(err.args[0])), ) + err.args[1:]
        raise
    except KeyError as err:
        raise FileNotFoundError((source +
                                 ' : grain.xml does not define a "name" property.'))


def is_lypackage(source):
    if not os.path.isdir(source):
        return False
    try:
        lypackage_name(source)
        return True
    except (FileNotFoundError, KeyError):
        return False


def is_pypackage(source):
    if not os.path.isdir(source):
        return False
    return os.path.exists(os.path.join(source, '__init__.py'))


def is_pymodule(source):
    if not os.path.isfile(source):
        return False
    return os.path.splitext(source)[1] == '.py'


def is_lytech(source):
    for file_obj in os.listdir(source):
        if file_obj.endswith('.lyt'):
            return True
    else:
        return False


def module_from_str(module):
    if type(module) is ModuleType:
        return module
    elif type(module) is str:
        return import_module(module)
    else:
        raise TypeError('Argument must either be a module or a string')


def is_installed_python(module):
    try:
        module_from_str(module)
        return True
    except:
        return False


def srcdir_from_any(source):
    if os.path.exists(source):
        return source
    elif is_installed_python(source):
        module = module_from_str(source)
        return module.__path__[0]
    else:
        raise FileNotFoundError('{} does not exist'.format(source))


def dest_from_srcdir(source):
    if is_lypackage(source):
        link_name = lypackage_name(source)
        link_dir = os.path.join(klayout_home(), 'salt')
    elif is_pypackage(source) or is_pymodule(source):
        link_dir = os.path.join(klayout_home(), 'python')
        link_name = os.path.splitext(os.path.basename(source))[0]
    elif is_lytech(source):
        link_dir = os.path.join(klayout_home(), 'tech')
        link_name = os.path.splitext(os.path.basename(source))[0]

    if not os.path.exists(link_dir):
        os.mkdir(link_dir)
    link = os.path.join(link_dir, link_name)
    return link


def link_any(any_source, overwrite=False, hard_copy=False):
    ''' Directories take precedence over installed python module

        Platform independent.

        Always overwrites existing symbolic links.

        Returns the full paths of source and destination if the link was created, otherwise None for both

    '''
    any_source = os.path.realpath(any_source)
    src = srcdir_from_any(any_source)
    dest = dest_from_srcdir(src)

    if src == dest:
        # Prevent circular reference
        return None, None
    if os.path.islink(dest):
        os.remove(dest)
    if os.path.exists(dest):
        if overwrite:
            rmtree(dest)
        else:
            return None, None

    if hard_copy:
        copytree(src, dest)
    else:
        if not is_windows():
            os.symlink(src, dest)
        else:
            symlink_windows(src, dest)

    return src, dest


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
