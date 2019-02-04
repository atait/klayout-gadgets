[![Build Status](https://travis-ci.org/atait/klayout-gadgets.svg?branch=master)](https://travis-ci.org/atait/klayout-gadgets)

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
pip install klayout-gadgets
```

### Step 2: link to klayout
You have a new terminal script that can link all kinds of stuff to the proper places in the klayout configuration directories.

```bash
lygadgets_link lygadgets
```

## Definition of terms
**lypackage (or salt package)**: handled by the klayout Package Manager. It includes a `grain.xml`. These can define macros, DRC, python packages, etc.

**salt package**: A lypackage that is published and available through the klayout Package Manager.

**pypackage**: python package included as part of a lypackage.

**system python**: the interpreter that runs when you type `python xxx.py` in the command line.

**system namespace**: the modules that are visisble to system python

**GSI (generic scripting interface)**: an interpreter than can run python and Ruby within the special namespace available to klayout.

**GSI/klayout namespace** modules visible in GSI. This includes regular python builtins, Pypackages located in salt packages. And *sometimes* the system namespace, but only if you launch klayout from the command line.

**GUI mode**: running scripts when there an open application window. In this mode, GSI is the primary interpreter.


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

If you have the klayout python standalone, that is what you will get as "pya". Then, its layout database features will be available, just like the regular GSI version of `pya` in batch mode. In GSI mode, lygadgets gives the GSI pya so as not disrupt things.

### Environment, more aggressive
GSI pya contains more than the standalone klayout.db. Your exiting python scripts that were run using `klayout -r script.py` and all of its dependencies that auto-run a whole bunch of stuff in their `__init__.py`s -- all of that stuff contains references to pya and GUI features of pya. So you definitely cannot do `python script.py`.

The command `lygadgets.patch_environment()` solves this problem. Just put it at the very top of `script.py`, after importing lygadgets. Now, you no longer need to do `from lygadgets import pya`. GUI calls will be stifled. The downside is that this aggressive approach is less likely to work cross-platform. It is still being debugged on Windows and Anaconda.

Once again backwards compatibility with GSI is the top priority of `patch_environment`. If it detects the GSI, it will do nothing.

### Markup reading
This will, in the future, expand into technology component access, which are just XML files. Outside of GSI, `pya.Technology` breaks, and `klayout.db.Technology` has not loaded the technology list.

Also includes the `yaml` package, so you can just `import yaml` within the GSI.

### Messaging
`message` and `message_loud` will detect the best way to report to the user, either in or out of GUI mode.

## Namespace linkage
These are technical notes, worth understanding if you are developing new klayout packages with hybrid GSI/system aspects.

The `lygadgets_link` command can insert a variety of things into the klayout namespace. It works with

- lypackages (i.e. klayout_dot_config)
- python packages
- python modules
- klayout technologies, either .lyt file or enclosing tech directory
- macros: ruby or python

It has flags `--force` to overwrite anything that is currently there. However, you won't have to do this often because links are symbolic, meaning they update as you update the file/directory. The `--copy` flag lets you make static copies instead of links.

NB: This package so far tested on MacOS HighSierra and is expected to work on other distributions of MacOS and Linux with python 3 and klayout >= 0.25.3. Windows supports python > klayout linking, but not klayout > system. Full testing with Anaconda managers is underway.

### Implementation rules for developers. Users should also take note if they have compatibility/organization interests

- no reference to particular technologies or specific types of properties (e.g. "WAVEGUIDES.xml")
- no calling `subprocess.call('klayout -r foo.py')`
- no phidl in the implementation. Of course phidl packages will use this one.
- `klayout.db` is allowed if it speeds it up, but it cannot be required

### Todo
- detect version of lypackages and pypackages to determine whether or not to force
- during lygadgets_link, figure out package dependencies and link those too

#### Authors: Alex Tait, Adam McCaughan, Sonia Buckley, Jeff Chiles, Jeff Shainline, Rich Mirin, Sae Woo Nam
#### National Institute of Standards and Technology, Boulder, CO, USA

