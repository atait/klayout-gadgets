# klayout-gadgets

Tools to make klayout, the standalone, and python environments work better together.

Particular focus on script-based layout of integrated circuits. There are some python-driven scripters and others that use the klayout language. Both can use tools to get certain simple information about klayout. The problem is that their environments and even execution engines are extremely different.

The purpose of this package is to provide simple klayout-related tools in a way that is highly robust to the environment in which it is being interpreted.

- No import errors when you are trying to test/debug a pure python aspect of an otherwise klayout GSI script.
- No inconsistencies between GSI and system namespace.

![](icons/lygadgets.png?raw=true)


## Installation

### Step 1: install the python package
From PyPI

```bash
pip install lygadgets
```

or from source

```bash
git clone git@github.com:atait/klayout-gadgets.git
pip install klayout-gadgets/klayout_dot_config/python
```

### Step 2: link to klayout
Hey, you have a new terminal script that can link all kinds of stuff to the proper places in the klayout configuration directories.

```bash
lygadgets_link lygadgets
```

## Installation (alternative)
This one is based on the klayout salt Package Manager and is not really recommended unless you know what you are doing. You have to go into the GUI application to use it - no command line installation. It automatically takes care of putting lygadgets into your system namespace.


## Definition of terms
**lypackage (or salt package)**: handled by the klayout Package Manager. It includes a `grain.xml`. These can define macros, DRC, python packages, etc.

**pypackage**: python package included as part of the lypackage. It will now be auto-installed to both klayout and system, if desired.

**system python**: the interpreter that runs when you type `python xxx.py` in the command line.

**system namespace**: the modules that are visisble to system python

**GSI (generic scripting interface)**: an interpreter than can run python and Ruby within the special namespace available to klayout.

**GSI/klayout namespace** modules visible in GSI. This includes regular python builtins, Pypackages located in salt packages. And *sometimes* the system namespace, but only if you launch klayout from the command line.

**GUI mode**: running scripts when there an open application window. In this mode, GSI is the primary interpreter.


## Here are the rules for this package

- no reference to particular technologies or specific types of properties (e.g. "WAVEGUIDES.xml")
- no calling `subprocess.call('klayout -r foo.py')`
- no phidl in the implementation. Of course phidl packages will use this one.
- `klayout.db` is allowed if it speeds it up, but it cannot be required


## See the example
I think it's a pretty decent way to see what happens when namespaces get desynchronized, how to use lygadgets, what happens when you call klayout from the command line.


## Features: simple stuff everybody uses for script-based layout

### Environment
Detects the interpreter in which code is being run. Provides a `pya` that is safe to import. In system interpreter, this will break

```python
import pya
```

but this will never break:

```python
from lygadgets import pya
```

however, of course, you then cannot try to use the GUI features of `pya`. You can't use it at all if you are running system python.

If you have the klayout python standalone, that is what you will get as "pya". Then, its layout database features will be available, just like the regular GSI version of `pya` in batch mode.

### Markup reading
This will, in the future, expand into technology component access, which are just XML files. Outside of GSI, `pya.Technology` breaks, and `klayout.db.Technology` has not loaded the technology list.

Also includes the `yaml` package, so you can just `import yaml` within the GSI.

### Messaging
`message` and `message_loud` will detect the best way to report to the user, either in or out of GUI mode.


## Major feature: namespace linkage, autoinstall hooks
These are technical notes, worth understanding if you are developing new klayout packages with hybrid GSI/system aspects.

**If you are a user, all you need to know is that `lygadgets_link` does what you need**

NB: This package so far tested on MacOS HighSierra and is expected to work on other distributions of MacOS and Linux with python 3 and klayout >= 0.25.3. Windows supports python > klayout linking, but not klayout > system.


### Type 1: From klayout to system
This looks in the package directory and does setup.py for the python package. Every time the application opens

- done

#### Notes
When klayout is initialized, pymacros/startup.py autoruns

It figures out system python by using a command line "which". Then it gets a bunch of absolute directories

Using system python, an import mylylib is run. Then it asserts the version is right.

If this causes an error, it uses system python to run setup.py for mylylib.

#### Caveat
The GSI python is different than the system python. It has all of the builtin packages installed in a Framework located within the klayout.app. This means it is extremely difficult to figure out what happens when you call "python" from your command line or as a regular user of some other application (which ultimately does the same thing).

This has led to a requirement. You have to symlink it somewhere in `/usr/local/bin`, `/usr/local/python`, or `/usr/local/opt`. These are pretty common places to install "python", which is really a symlink leading to `/usr/local/.../Frameworks/.../python3.6.5` or `/usr/.../Cellar/python/3.6.5/bin/python3.6.5` if you are a brew user.

Here is what you must do

```bash
ln -s /usr/local/bin/python3 /usr/local/bin/python
```

Maybe you don't have "python3" (another symlink) there?! A more involved but foolproof way is to actually go to your terminal and see where it leads. Here is an example that will differ for you in terms of paths and numbers

```bash
$ python
Python 3.7.0 (default, Jun 29 2018, 20:13:13)
[Clang 9.1.0 (clang-902.0.39.2)] on darwin
Type "help", "copyright", "credits" or "license" for more information.

>>> import sys
>>> sys.executable
'/usr/local/opt/python/bin/python3.7'
```

Exit the python interpreter and then do

```bash
ln -s /usr/local/opt/python/bin/python3.7 /usr/local/bin/python
```

Here is what you cannot do

- `alias python=python3`
- not have python 3 installed somewhere
- use Anaconda (I think this would be ok, *as long as* `/usr/local/bin/python` *is symlinked to the appropriate place*)
- use pyenv (Also think this would be fine, but not tested)
- use Windows



### Type 2: From python component to klayout

- Currently: finds enclosing klayout_dot_config and makes a symlink
- Ideally: download the thing from github and put the hard thing in the right place
- **not recommended** for the following reasons
    - downloading from github does not process klayout package dependencies
    - this is pip-driven, which strongly discourages running arbitrary post-install code

#### Notes
`pip` does not allow post-install scripts, but `setup.py` does. So your hybrid klayout packages cannot go on PyPI.

Where you would use this: **developer mode**, particularly when the klayout package is **not yet on the salt mine**

    1. clone the repo of your klayout package from a git server
    1. run `python setup.py install` in its python directory
        - it should have a dependency of the pure-python component on PyPI: `lygadgets_lite` **NO** dependencies are installed after post-install definition in setup.py
    1. it symlinks to your git clone from the `.klayout/salt` directory
    1. Finally, changes you make in your git clone will be reflected immediately in the klayout application


## Best practices on packaging a hybrid lyproject
You must structure your package like this. Starred names are *required to be named exactly*

```
my-git-project
| .gitignore
| examples
| README.md             (This is the long one)
| *klayout_dot_config*
    | *grain.xml*
    | *pymacros*
    | *python*
        | *setup.py*
        | README.md     (This can be a short one that just links to github)
        | mypypackage
            | *__init__.py*     (This must define a "__version__" attribute)
            | some_module.py
```

Put this in your `setup.py`:

```python
try:
    from lygadgets import postinstall_hook
except (ImportError, ModuleNotFoundError):
    print('\033[95mlygadgets not found, so klayout package not linked.')
    print('Please download it in the klayout Package Manager\033[0m')
    my_postinstall = dict()
else:
    setup_dir = os.path.dirname(os.path.realpath(__file__))
    lypackage_dir = os.path.dirname(setup_dir)
    my_postinstall = {'install': postinstall_hook(lypackage_dir)}

...

setup(
      ...
      cmdclass=my_postinstall,
      ...
      )
```

Note this code *will not run* if `pip install`, and all your users have to do `lygadgets_link mypackage`. This situation always occurs when using PyPI.

If `setup.py install` is used, no problem. This is more likely to be the method of installation when users install from source in a git project.


#### Authors: Alex Tait, Adam McCaughan, Sonia Buckley, Jeff Chiles, Jeff Shainline, Rich Mirin, Sae Woo Nam
#### National Institute of Standards and Technology, Boulder, CO, USA

