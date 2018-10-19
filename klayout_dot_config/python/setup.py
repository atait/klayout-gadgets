from setuptools import setup


def readme():
    with open('README.md', 'r') as fx:
      return fx.read()


setup(name='lygadgets',
      version='0.0.11',
      description='Tools to make klayout and python work better together',
      long_description=readme(),
      author='Alex Tait',
      author_email='alexander.tait@nist.gov',
      license='MIT',
      packages=['lygadgets'],
      install_requires=[],
      entry_points={'console_scripts': ['lygadget_link=lygadgets.command_line:cm_link_any']},
      )
