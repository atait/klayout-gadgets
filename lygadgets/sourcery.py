import os
import subprocess
import importlib.util
from importlib import import_module

from . import message, message_loud

pypackage = None

# klayout's version
def get_klayout_version():
    klayouts_pypackage = import_module(pypackage)
    try:
        return klayouts_pypackage.__version__
    except AttributeError as err:
        err.args = ('The package {} does not define a __version__ in its __init__.py'.format(pypackage), ) + err.args[:1]
        raise


def system_python():
    retraw = subprocess.check_output(['which', 'python'])
    return retraw.decode().strip("'").strip('\n')


# System version
def get_system_version():
    check_program = ('import {}; '.format(pypackage) +
                     'print({}.__version__)'.format(pypackage))
    try:
        retraw = subprocess.check_output([system_python(), '-c', check_program])
        return retraw.decode().strip("'").strip('\n')
    except (ImportError, ModuleNotFoundError, subprocess.CalledProcessError):
        # It's not installed at all
        return '-1'
    except AttributeError as err:
        err.args = ('The package {} does not define a __version__ in its __init__.py'.format(pypackage), ) + err.args[:1]
        raise


# Source version
def get_source_version(pypackage_dir):
    version_file = os.path.join(pypackage_dir, pypackage, '__init__.py')
    spec = importlib.util.spec_from_file_location(pypackage, version_file)
    source_version_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(source_version_module)
    try:
        return source_version_module.__version__
    except AttributeError as err:
        err.args = ('The package {} does not define a __version__ in its __init__.py'.format(pypackage), ) + err.args[:1]
        raise


def install_from_source(source_dir):
    install_call = [system_python(), 'setup.py', 'install']
    try:
        subprocess.check_call(install_call, cwd=source_dir)
        message('Success')
    except Exception as err:
        message_loud('Error installing {}!\n\n{}'.format(pypackage, err))


def synchronize_package(pypackage_name, lypackage_dir):
    global pypackage
    pypackage = pypackage_name
    pypackage_dir = os.path.join(lypackage_dir, 'python')
    source_version = get_source_version(pypackage_dir)

    if source_version == get_klayout_version() and source_version == get_system_version():
        message('{} {} already installed'.format(pypackage, source_version))
    else:
        message(('{} ({}) '.format(pypackage, get_klayout_version()) +
                 'is desynchronized from source ({})'.format(source_version)))
        install_from_source(pypackage_dir)

