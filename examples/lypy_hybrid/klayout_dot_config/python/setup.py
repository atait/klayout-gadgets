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
    lypackage_dir = os.path.dirname(setup_dir)
    my_postinstall = {'install': postinstall_hook(lypackage_dir)}


setup(name='lybar',
      description='Sample of a python package as part of a hybrid klayout package',
      packages=['lybar'],
      cmdclass=my_postinstall,
      )
