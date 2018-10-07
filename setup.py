from setuptools import setup
from setuptools.command.install import install

from lygadgets import post_install_factory

def readme():
    with open('README.md', 'r') as fx:
      return fx.read()

setup(name='lygadgets',
      version='0.0.1',
      description='Tools to make klayout and python work together better',
      long_description=readme(),
      author='Alex Tait',
      author_email='alexander.tait@nist.gov',
      license='MIT',
      packages=['lygadgets'],
      install_requires=[],
      entry_points={},
      )
