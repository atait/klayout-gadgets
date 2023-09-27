from __future__ import print_function
try:  # python 2 does not have FileNotFoundError. Check it
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

import os
import ast
import subprocess
from importlib import import_module
from shutil import rmtree, copytree
from types import ModuleType
import xmltodict

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
            grain_dict = xmltodict.parse(grain.read(), process_namespaces=True)
        return grain_dict['salt-grain']['name']
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
    ''' In this case the "source" is the full tech directory or the .lyt file
        It always returns the tech directory path
    '''
    if os.path.isfile(source):
        if source.endswith('.lyt'):
            source = os.path.dirname(source)
        else:
            return False
    else:
        for file_obj in os.listdir(source):
            if file_obj.endswith('.lyt'):
                return source
        else:
            return False


def is_lymacro(source):
    if not os.path.isfile(source):
        return False
    if not source.endswith('.lym'):
        return False
    return True


def is_pymacro(source):
    if not is_lymacro(source):
        return False
    with open(source) as macro:
        grain_dict = xmltodict.parse(macro.read(), process_namespaces=True)
    interpreter = grain_dict['klayout-macro']['interpreter']
    return interpreter.lower() == 'python'


def is_rubymacro(source):
    return is_lymacro(source) and not is_pymacro(source)


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
    try:
        if os.path.exists(source):
            return os.path.realpath(source)
    except TypeError:
        pass
    if is_installed_python(source):
        module = module_from_str(source)
        # now figure out if it is a package or a non-packaged module
        try:
            return module.__path__[0]
        except (AttributeError, IndexError):
            return module.__file__
    else:
        raise FileNotFoundError('{} does not exist'.format(source))


def dest_from_srcdir(source, exclude_python_types=False):
    if is_lypackage(source):
        link_name = lypackage_name(source)
        link_dir = os.path.join(klayout_home(), 'salt')
    elif is_lytech(source) != False:
        enclosing_dir = is_lytech(source)
        link_dir = os.path.join(klayout_home(), 'tech')
        link_name = os.path.splitext(os.path.basename(enclosing_dir))[0]
    elif is_lymacro(source):
        link_dir = os.path.join(klayout_home(), 'pymacros' if is_pymacro(source) else 'macros')
        link_name = os.path.basename(source)
    elif is_pypackage(source) or is_pymodule(source):
        if not exclude_python_types:
            link_dir = os.path.join(klayout_home(), 'python')
            link_name = os.path.basename(source)
        else:
            # return None
            raise TypeError('Python code found but it is being excluded: ' + source)
    else:
        raise TypeError('Did not recognize the klayout relevance of {}'.format(source))

    if not os.path.exists(link_dir):
        os.mkdir(link_dir)
    link = os.path.join(link_dir, link_name)
    return link


def link_any(any_source, overwrite=False, hard_copy=False, keep_links=False, exclude_python_types=False):
    ''' Directories take precedence over installed python module

        Platform independent.

        If keep_links=False, overwrites existing symbolic links.

        Returns the full paths of source and destination if the link was created, otherwise None for both.

        If you have given it a python package or an installed module with .lym's in it, klayout will automatically find them.
        Note to make sure they come along with the pip distro, use "package_data" in setup.py
    '''
    src = srcdir_from_any(any_source)
    try:
        dest = dest_from_srcdir(src, exclude_python_types=exclude_python_types)
    except TypeError as err:
        print(err)
        return None, None

    if src == dest:
        # Prevent circular reference
        print('Circular reference')
        print(src)
        return None, None
    if os.path.islink(dest):
        if not keep_links:
            os.remove(dest)
        else:
            print(any_source, 'already installed')
            return None, None
    if os.path.exists(dest):
        if overwrite:
            rmtree(dest)
        else:
            print('Not linking. Destination has a non-symlink item present that would be overwritten.')
            print('Use -f command line option to overwrite, or use lygadgets_unlink to remove it first')
            print(dest)
            return None, None

    if hard_copy:
        copytree(src, dest)
        print('Successfully created a hard copy')
    else:
        if not is_windows():
            os.symlink(src, dest)
        else:
            symlink_windows(src, dest)
        print('Successfully created a symbolic link')
    print('From:', src)
    print('To:  ', dest)

    # __lygadget_link__ is the special top package attribute that triggers more linking.
    # A list of strings/modules that must be installed or discoverable by import_module
    others_to_link = []
    if is_installed_python(any_source):
        module = module_from_str(any_source)
        try:
            others_to_link = module.__lygadget_link__
        except AttributeError:
            pass
    elif is_pypackage(any_source) or is_pymodule(any_source):
        # Find that assignment, but don't import the module
        if is_pypackage(any_source):
            code_file = os.path.join(any_source, '__init__.py')
        else:
            code_file = any_source
        with open(code_file) as fx:
            code_text = fx.read()

        for line in code_text.split('\n'):
            if '__lygadget_link__' in line:
                code_ast = ast.parse(line)
                try:
                    assign_ast = code_ast.body[0]
                    assert isinstance(assign_ast, ast.Assign)
                    assert assign_ast.targets[0].id == '__lygadget_link__'
                    if isinstance(assign_ast.value, ast.Constant):
                        others_to_link = [assign_ast.value.value]
                    elif isinstance(assign_ast.value, (ast.List, ast.Tuple)):
                        others_to_link = [e.value for e in assign_ast.value.elts]
                    else:
                        raise TypeError('__lygadget_link__ needs to be found in simple assignment')
                except (AttributeError, TypeError, AssertionError):
                    # something went wrong
                    print('Something went wrong linking lygadget dependencies in this line')
                    print(line)
                break

    # Do dependency linking
    for other in others_to_link:
        subsrc, subdest = link_any(other, keep_links=True)
        if subsrc is not None:
            print('Dependency linked:', any_source, '->', other)

    return src, dest


def unlink_any(installed_name, force=False):
    matches = []
    search_relpaths = ['python', 'tech', 'salt']
    for relpath in search_relpaths:
        search_dir = os.path.join(klayout_home(), relpath)
        for fname in os.listdir(search_dir):
            if fname == installed_name:
                matches.append(os.path.join(search_dir, fname))
    if len(matches) == 0:
        print('Did not find matching installed package for "{}"'.format(installed_name))
    elif len(matches) > 1:
        print('Multiple matches found. Delete manually')
        print('\n'.join(matches))
    else:
        match = matches[0]
        if os.path.islink(match):
            os.remove(match)
            print('Removed symlink', match)
        elif force:
            rmtree(match)
            print('Removed directory', match)
        else:
            print(match, 'is a directory, not a symlink.')
            print('Use the -f option if you are sure you want to permanently delete.')
