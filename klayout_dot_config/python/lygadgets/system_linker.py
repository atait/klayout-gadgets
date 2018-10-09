import os
import subprocess
import importlib.util
from importlib import import_module

from lygadgets.messaging import message, message_loud
from lygadgets.environment import is_windows

pypackage = None

# klayout's version
def get_klayout_version():
    klayouts_pypackage = import_module(pypackage)
    try:
        return klayouts_pypackage.__version__
    except AttributeError as err:
        err.args = ('The package {} does not define a __version__ in its __init__.py'.format(pypackage), ) + err.args[:1]
        raise


_system_python = None
def system_python():
    ''' Fix the PATH to prioritize /usr/local/bin

        This is no longer windows compatible.
        If we are running in windows, it always raises a
    '''
    if is_windows():
        raise RuntimeError('finding system_python on Windows not supported.')
    global _system_python
    if _system_python is None:
        # Fix the PATH to prioritize /usr/local/bin
        # This is no longer windows compatible

        # def shell_call(commands, env=None, shell=False):
        #     if env is None:
        #         env = os.environ
        #     retraw = subprocess.check_output(commands, env=env, shell=shell)
        #     return retraw.decode().strip("'").strip()

        def is_py3(pyexecutable):
            retraw = subprocess.call([pyexecutable, '-c', '"import sys; assert sys.version_info >= (3, 1)"'])
            return retraw == 0

        # def interactive_bash_call(bash_commands):
        #     full_command = ['/bin/bash', '-i', '-c']
        #     full_command.append('"{}"'.format('; '.join(bash_commands)))
        #     return shell_call(full_command, env=None, shell=False)

        # def as_true_user(bash_commands):
        #     full_bash_commands = []
        #     config_files = ['.bash_profile', '.bashrc', '.bash_aliases']
        #     user_home = os.environ['HOME']
        #     for cf in config_files:
        #         full_file = os.path.join(user_home, cf)
        #         full_bash_commands.append('source ' + full_file)
        #     full_bash_commands.extend(bash_commands)
        #     return interactive_bash_call(full_bash_commands)

        # are we dealing with an alias?
        # THIS CAUSES HANG. REMOVING
        # ret = as_true_user(['type python'])
        # if 'aliased to' in ret:
        #     raise FileNotFoundError('You have aliased python. This is not supported. Please change it to a symlink')
        #     # start_ind = ret.find('aliased to')
        #     # resolved_proto = ret[start_ind+11:]
        #     # resolved = resolved_proto.strip("`'").strip()
        # else:
        #     resolved = 'python'
        resolved = 'python'

        for search_path in ['/usr/local/bin', '/usr/local/python', '/usr/local/opt']:
            my_env = os.environ.copy()
            my_env['PATH'] = search_path + ':' + my_env['PATH']
            retraw = subprocess.check_output(['which', resolved], env=my_env)
            pyexecutable = retraw.decode().strip("'").strip()
            if is_py3(pyexecutable):
                _system_python = pyexecutable
                break
        else:
            raise FileNotFoundError('python version 3 was not found in any of the normal places. Make sure it is installed.')
    return _system_python


# System version
def get_system_version():
    check_program = ('import {}; '.format(pypackage) +
                     'print({}.__version__)'.format(pypackage))
    try:
        retraw = subprocess.check_output([system_python(), '-c', check_program])
        all_talking = retraw.decode().strip("'").strip('\n')
        printed_lines = all_talking.split('\n')
        return printed_lines[-1]
    except AttributeError as err:
        err.args = ('The package {} does not define a __version__ in its __init__.py'.format(pypackage), ) + err.args[:1]
        raise
    except (ImportError, ModuleNotFoundError, subprocess.CalledProcessError, RuntimeError):
        # It's not installed at all
        return '-1'


# Source version
def get_source_version(pypackage_dir):
    version_file = os.path.join(pypackage_dir, pypackage, '__init__.py')
    spec = importlib.util.spec_from_file_location(pypackage, version_file)
    source_version_module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(source_version_module)
    except Exception as err:
        message_loud(('Error loading {}!\n\n{}\n\n'.format(pypackage, err) +
                      'Get the traceback by launching klayout from command line'))
        raise
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
        message_loud(('Error installing {}!\n\n{}\n\n'.format(pypackage, err) +
                      'Get the traceback by launching klayout from command line (verified)'))
        import traceback
        message_loud(traceback.extract_stack())
        raise


def export_to_system(pypackage_name, lypackage_dir):
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

