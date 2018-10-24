from setuptools import setup
import os


try:
    from lygadgets import postinstall_hook
except (ImportError, ModuleNotFoundError):
    print('\033[95mlygadgets not found, so klayout package not linked.')
    print('Please download lygadgets from the klayout Package Manager\033[0m')
    my_postinstall = dict()
else:
    setup_dir = os.path.dirname(os.path.realpath(__file__))
    pkg_dir = os.path.join(setup_dir, 'lyfoo')
    my_postinstall = {'install': postinstall_hook(pkg_dir)}


setup(name='lyfoo',
      description='Sample of a pure python package to be linked to klayout',
      packages=['lyfoo'],
      cmdclass=my_postinstall,
      )
