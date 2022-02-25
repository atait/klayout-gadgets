[![Build Status](https://travis-ci.org/atait/klayout-gadgets.svg?branch=master)](https://travis-ci.org/atait/klayout-gadgets)
[![Downloads](https://static.pepy.tech/personalized-badge/lygadgets?period=total&units=international_system&left_color=grey&right_color=brightgreen&left_text=Downloads)](https://pepy.tech/project/lygadgets)

# klayout-gadgets

Tools to make klayout, the standalone, and python environments work better together.

Particular focus on script-based layout of integrated circuits. There are some python-driven scripters and others that use the klayout language. Both can use tools to get certain simple information about klayout. The problem is that their environments and even execution engines are extremely different.

The purpose of this package is to provide simple klayout-related tools in a way that is highly robust to the environment in which it is being interpreted.

- No import errors when you are trying to test/debug a pure python aspect of an otherwise klayout GSI script.
- No inconsistencies between GSI and system namespace.

![](icons/lygadgets.png?raw=true)


- [Installation](#installation)
- [Vocabulary](#definition-of-terms)
- [Features](#features)
    * [Scope linking](#linking-all-sorts-of-things-into-klayout-scope)
    * [Cell translation](#cell-translation)
    * [Environment](#environment)
- [Upcoming features and ideas](#upcoming-features-and-ideas)


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

*Warning for OSX Catalina*: `lygadgets` requires a klayout environment with python >3.6. A suitable klayout binary that works with OSX Catalina and python 3 has not been released as of 10/25/19.


## Definition of terms
**lypackage (or salt package)**: handled by the klayout Package Manager. It includes a `grain.xml`. These can define macros, DRC, python packages, etc.

**salt package**: A lypackage that is published and available through the klayout Package Manager.

**pypackage**: python package included as part of a lypackage.

**system python**: the interpreter that runs when you type `python xxx.py` in the command line.

**system namespace**: the modules that are visisble to system python

**GSI (generic scripting interface)**: an interpreter than can run python and Ruby within the special namespace available to klayout.

**GSI/klayout namespace** modules visible in GSI. This includes regular python builtins, Pypackages located in salt packages. And *sometimes* the system namespace, but only if you launch klayout from the command line.

**GUI mode**: running scripts when there an open application window. In this mode, GSI is the primary interpreter.


## Features

### Linking all sorts of things into klayout scope
See the "examples" directory for more detailed discussion and demonstration.

`lygadgets_link` symlinks stuff (pypackages, technologies, salt packages) to the right places, just as if you had downloaded them through salt. Symlinking is especially useful if you have git project that changes, and you want changes to be immediately reflected in the klayout application.

*Note on Windows: symlinking requires running as administrator*

These things can be linked

- lypackages (i.e. klayout_dot_config)
- python packages
- python modules
- klayout technologies, either .lyt file or enclosing tech directory
- macros: ruby or python

`lygadgets_link` has flags `--force` to overwrite anything that is currently there. However, you won't have to do this often because links are symbolic, meaning they update as you update the file/directory. The `--copy` flag lets you make static copies instead of links.

#### Linking python packages
Right after `pip install mypack`, run `lygadgets_link mypack`, and it will show up to klayout's GSI. This creates a symlink from source files to the `~/.klayout/python` directory.

**As of v0.1.25**, this command can also trigger linking of other dependencies. The trigger list is a package attribute called `__lygadget_link__`, defined in `__init__`. Here is where you put pip dependencies:

```python
# setup.py
setup(name='lygadgets',
      ...
      install_requires=['future', 'xmltodict'],
      )
```

Now, we *also* put them in `__init__.py`.

``` python
# lygadgets/__init__.py
__version__ = '0.1.25'
__lygadget_link__ = ['future', 'xmltodict']

```

Some packages that require lygadgets linking:
- [lyipc](https://github.com/atait/klayout-ipc)
- [lytest](https://github.com/atait/lytest)
- [lymask](https://github.com/atait/lymask)

#### Linking technologies
This usually goes like

```bash
lygadgets_link SOEN-PDK/tech/OLMAC
```

and then you will be able to access all the features of that technology (layers, pcells, properties, ...) within system python or GSI like this

```python
from lygadgets import pya
the_tech = pya.Technology.technology_by_name('OLMAC')
```

### Cell translation
See "tests/translation_test.py" for demonstrations.

There are at least ten python-based layout languages targeted for photonics. I have no idea how many there are for electronics. None of them are compatible. What some folks do is translation by-hand followed by rigorous regression testing. This might work for a PDK with 10's of really simple PCells. But imagine an actual, real codebase that has 1,000's of PCells, sometimes embedded within a hierarchy of other PCells. The permutations of parameters is staggering. Regression testing will not work<sup>\*</sup>.

The solution offered here is to take advantage of the one universal layout specification: GDS. An example call would be

```python
# Setup a klayout cell
pya_layout = pya.Layout()
pya_cell = pya_layout.create_cell('newname')
# Make a phidl device
phidl_device = some_device(10, 20)
# Translate
lygadgets.anyCell_to_anyCell(init_device, pya_cell)
```

Under the hood, lygadgets is taking the phidl Device, writing it to GDS, loading that GDS into `pya_cell`, then deleting the GDS. In the future, I hope to add support for IPKISS, nazca, gdspy, and maybe others on request.

<sup>\*</sup>Geometric regression testing is useful. See [lytest](https://github.com/atait/lytest) for that. It's practically necessary for large codebases being modified by multiple people. "Multiple people" can include you and yourself in the future who will have forgotten everything.

#### PCell translation
This is handled in `lygadgets.autolibrary.WrappedPCell`. Example call:

```python
from lygadgets.autolibrary import WrappedPCell
from olmac_pcells import wg_to_snspd

pya_layout = pya.Layout()
WgToSNSPD = WrappedPCell(wg_to_snspd)

# You now have a pya PCell. You can put it in your layout multiple times with different parameters
wg_cell1, wg_ports1 = WgToSNSPD('My_SNSPD').pcell(pya_layout, params={'wgnw_length': 200})
wg_cell2, wg_ports2 = WgToSNSPD('My_SNSPD').pcell(pya_layout, params={'wgnw_length': 400})
```

This translation can also go from klayout -> phidl.

#### Make your non-klayout PCells available for GUI layout
We can now convert any PCell into a klayout PCell. The klayout GUI has a decent interface for inserting PCells interactively.

```python
# Macro: klayout_Library.lym. Find it in SOEN-PDK
from olmac_pcells import wg_to_snspd, htron
class OLMAC_Library(lygadgets.WrappedLibrary):
    tech_name = "OLMAC"
    all_funcs_to_wrap = [wg_to_snspd, htron]
    description = "NIST SOEN"
OLMAC_Library()  # This registers it with the GUI and the GSI
```

(This is still a little buggy).

### Environment
See the "examples" directory for more detailed discussion and demonstration.

Detects the interpreter in which code is being run. Provides a `pya` that is safe to import. In system interpreter, this will break

```python
import pya
```

but this will never break:

```python
from lygadgets import pya
```

however, of course, you then cannot try to use the GUI features of `pya`. You can't use it at all if you do not have the klayout standalone: `pip install klayout`.

If you have the klayout python standalone, that is what you will get as "pya". Then, its layout database features will be available, just like the regular GSI version of `pya` in batch mode. In GSI mode, lygadgets gives the GSI pya so as not disrupt things.

#### More aggressive: `patch_environment`
GSI pya contains more than the standalone klayout.db. Your exciting python scripts that were run using `klayout -r script.py` and all of its dependencies that auto-run a whole bunch of stuff in their `__init__.py`s -- all of that stuff contains references to pya and GUI features of pya (Example: SiEPIC_Tools). So you definitely cannot do `python script.py`.

The command `lygadgets.patch_environment()` solves this problem by hijacking the way python finds packages. Just put it at the very top of `script.py`, after importing lygadgets. Now, you no longer need to do `from lygadgets import pya`. GUI calls will be stifled. The downside is that this aggressive approach is less likely to work cross-platform. It is still being debugged on Windows and Anaconda.

Backwards compatibility with GSI is the top priority of `patch_environment`. If it detects the GSI, it will do nothing.


## Upcoming features and ideas
- detect version of lypackages and pypackages to determine whether or not to force link update
- Port translation


## Things that lygadgets does not do

- no non-standard required dependencies (only future and xmltodict)
- no reference to particular technologies (e.g. OLMAC) or specific types of properties (e.g. "WAVEGUIDES.xml"), except for the sake of documentaion/illustration
- no calling `subprocess.call('klayout -r foo.py')`
- no phidl in the implementation.
- `klayout.db` is allowed if it speeds it up, but it cannot be required



#### Authors: Alex Tait, Adam McCaughan, Sonia Buckley, Jeff Chiles, Jeff Shainline, Rich Mirin, Sae Woo Nam
#### National Institute of Standards and Technology, Boulder, CO, USA

