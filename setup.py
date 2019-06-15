from setuptools import setup


def readme():
    with open('README.md', 'r') as fx:
      return fx.read()


setup(name='lygadgets',
      version='0.1.28',
      description='Tools to make klayout, the standalone, and python environments work better together',
      long_description=readme(),
      long_description_content_type='text/markdown',
      author='Alex Tait',
      author_email='alexander.tait@nist.gov',
      license='MIT',
      packages=['lygadgets'],
      install_requires=['future', 'xmltodict'],
      package_data={'': ['*.lym']},
      include_package_data=True,
      entry_points={'console_scripts': ['lygadgets_link=lygadgets.command_line:cm_link_any']},
      )
