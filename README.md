# klayout-gadgets
**This is a prototype still in progress.**

**It has been tested on MacOS HighSierra and is expected to work on other distributions of MacOS and Linux with python 3 and klayout >= 0.25.3. No windows yet.**

Tools to make klayout and python work together better.

![](klayout_dot_config/icons/lygadgets.png?raw=true)

Specifically, it makes hybrid salt packages (klayout macros and python) easier by auto-installing the python part in *system* python and of course is always visible in the klayout namespace.

This has a special focus on script-based layout of integrated circuits. Scripts that are run within klayout should also run correctly when running without the klayout application. Eventually, this should make transitioning to the klayout python standalone smoother.

### Here are the rules for this package

- no calling `klayout -r foo.py` from the command line
- no phidl
- no reference to particular technologies or specific types of properties (e.g. "WAVEGUIDES.xml")
- lightweight as possible
- `klayout.db` is allowed if it speeds it up, but it cannot be required
- `pya` is allowed and necessary in some cases, but it is not available outside of the GSI (unless you have the klayout standalone). Everything based on system python launches must avoid pya or fail gracefully

### Definition of terms
**lypackage**: An extension to klayout packaged in a particular format. It includes a `grain.xml`. It can define macros, DRC, python packages, etc.

**salt package**: A lypackage that is published and available through the klayout Package Manager.

**pypackage**: python package included as part of a lypackage.

**system python**: the interpreter that runs when you type `python xxx.py` in the command line.

**system namespace**: the modules that are visisble to system python

**GSI (generic scripting interface)**: an interpreter than can run python and Ruby within the special namespace available to klayout.

**GSI/klayout namespace** modules visible in GSI. This includes regular python builtins, Pypackages located in salt packages. And *sometimes* the system namespace, but only if you launch klayout from the command line.

**GUI mode**: running scripts when there an open application window. In this mode, GSI is the primary interpreter.

## Packaging philosophies
<!-- First some desires. Suppose you have a script called `xx.py`. We want to have the same namespace when that script is executed like `klayout -r xx.py`, like `python xx.py`, and from a menu button in the GUI. Ok these are very different use cases. The reason is that `xx` is part of a larger code structure with other modules. All of the imports have to work.

Maybe `xx.py` is eventually to be used in GUI, but you would like to debug its non-GUI subfunctions from command-line. An example of this is lyipc, a single python package, that has components that can be used in both -->aUIOPV560C09/............................................................................. NG

There are three ways a python package can be delivered to you

1. PyPI
2. git, then run `python setup.py install` or `pip -e install .`. Case a) standalone python package, or Case b) ones contained in a lypackage
3. salt

In case 1, any related lypackages must be fetched (since they cannot be listed as python dependencies). This is moot because post-install scripts are not allowed. It must be done manually. This is recommended for pure python; however, then the GSI namespace can miss it unless run by the user from the terminal.

**Any code that will eventually run in the GUI should not go through PyPI**. If you have a package "trivial" with function "add_one" and this function is only ever called by you from the command line, it can go PyPI, otherwise it should go through salt. **Exception**: if somebody finds a way to extend the GSI PYTHONPATH. I have tried os.environ

Case 2 is easy. You are likely developing code that is either not on a package manager or changing between major releases. The challenge is keeping it synchronized. In case 2a, there is no lypackage structure -- `lygadgets` can (*should* todo) dynamic link your source into the `.klayout/python` directory. In 2b, `lygadgets` offers the `postinstall_factory` to take care of the linkage.

In case 3, the pypackage goes into klayout. System python will not be able to find it. The solution is to put an autorun script in the lypackage that finds system python and uses it to call `setup.py`. This is lygadget's `export_to_system`.

## Autoinstall hooks
There are two categories

### From klayout GUI package manager.
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

### From a python component

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

#### Here's how
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
def my_postinstall():
    try:
        from lygadgets import post_install_factory
    except (ImportError, ModuleNotFoundError):
        print('\033[95mlygadgets not found, so klayout package not linked.')
        print('Please download it in the klayout Package Manager\033[0m')
        return dict()
    else:
        lypackage_root = os.path.realpath(os.path.join('..', '..', 'klayout_dot_config'))
        return {'install': post_install_factory(lypackage_root)}

...

setup(
      ...
      cmdclass=my_postinstall(),
      ...
      )
```

## Environment
Detects the interpreter in which code is being run. Provides a `pya` that is safe to import. In system interpreter, this will break

```python
import pya
```

but this will never break:

```python
from lygadgets import pya
```

however, of course, you then cannot try to use the GUI features of `pya`.

If you have the klayout python standalone, that is what you will get as "pya". Then, its layout database features will be available, just like the regular GSI version of `pya`.

## Markup reading
This will, in the future, expand into technology component access, which are just XML files. Outside of GSI, `pya.Technology` breaks, and `klayout.db.Technology` has not loaded the technology list.

Also includes the `yaml` package, so you can just `import yaml` within the GSI.

## Messaging
`message` and `message_loud` will detect the best way to report to the user, either in or out of GUI mode.
