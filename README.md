# klayout-gadgets
**This is a prototype still in progress**

Tools to make klayout and python work together better.

Specifically, it makes hybrid salt packages (klayout macros and python) easier by auto-installing the python part in *system* python and of course is always visible in the klayout namespace.

This has a special focus on script-based layout of integrated circuits. Scripts that are run within klayout should also run correctly when running without the klayout application. Eventually, this should make transitioning to the klayout python standalone more smooth.

### Here are the rules for this package

- no calling `klayout -r foo.py` from the command line
- no phidl
- no reference to particular technologies or specific types of properties (e.g. "WAVEGUIDES.xml")
- lightweight as possible
- `klayout.db` is allowed if it speeds it up, but it cannot be required
- `pya` is allowed and necessary in some cases, but it is not available outside of the GSI (unless you have the klayout standalone). Everything based on system python launches must avoid pya or fail gracefully

### Definition of terms
**lypackage (or salt package)**: handled by the klayout Package Manager. It includes a `grain.xml`. These can define macros, DRC, python packages, etc.

**pypackage**: python package included as part of the lypackage. It will now be auto-installed to both klayout and system, if desired.

**system python**: the interpreter that runs when you type `python xxx.py` in the command line.

**system namespace**: the modules that are visisble to system python

**GSI (generic scripting interface)**: an interpreter than can run python and Ruby within the special namespace available to klayout.

**GSI/klayout namespace** modules visible in GSI. This includes regular python builtins, Pypackages located in salt packages. And *sometimes* the system namespace, but only if you launch klayout from the command line.

**GUI mode**: running scripts when there an open application window. In this mode, GSI is the primary interpreter.


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

def setup(
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

however, of course, you then cannot try to use the GUI features of `pya`. If you have the klayout python standalone, that is what you will get as "pya". Then, its layout database features will be available, just like the regular GSI version of `pya`.

## Markup reading
This will, in the future, expand into technology component access, which are just XML files. Outside of GSI, `pya.Technology` breaks, and `klayout.db.Technology` has not loaded the technology list.

Also includes the `yaml` package, so you can just `import yaml` within the GSI.

## Messaging
`message` and `message_loud` will detect the best way to report to the user, either in or out of GUI mode.