# klayout-gadgets

## Version checking
- System version
- Source version
- Cached klayout version

## Autoinstall hooks
There are two categories

1. From klayout GUI package manager. This looks in the package directory and does setup.py for the python package. Every time the application opens

    - done

2. From python standalone

    - Currently: finds enclosing klayout_dot_config and makes a symlink
    - Ideally: download the thing from github and put the hard thing in the right place

### Notes on the klayout package manager driven one
When klayout is initialized, pymacros/startup.py autoruns

It figures out system python by using a command line "which". Then it gets a bunch of absolute directories

Using system python, an import mylylib is run. Then it asserts the version is right.

If this causes an error, it uses system python to run setup.py for mylylib.

