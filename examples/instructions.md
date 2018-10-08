## There are 3 packages
lypy_hybrid (klayout), lybar (within lypy_hybrid), lyfoo (pure python)

lypy_hybrid defines menu buttons. lyfoo is used just for utility functions. lybar does a combination of things: uses lyfoo, uses the GUI elements of pya. It also acesses non-GUI elements of pya. This case is most relevant to script-based layout from the command-line.


## Installation/uninstallation behavior
When you run `python setup.py install` in either python package, they will be installed in the system (that's the point), and transferred to the klayout namespace. Note: linking will NOT work if you do `pip install .` because pip restricts post-install behavior.

lypy_hybrid does not automatically export lybar to the system as it would normally. You have to press a button to see what would happen normally.

To emulate the effect of having something in klayout but not system, run setup.py and then, `source clean_system.sh`. For the reverse, do `source clean_klayout.sh`. This doesn't yet detect windows.

### When you are done with this demo
Run both clean scripts and everything will return to normal. Sit back, think about what you learned here today.


## Testers
lypy_hybrid gives you three GUI menu buttons. One checks for a successful call passing through lybar and lyfoo. Another does an explicit GUI thing via lybar. Another performs the lybar export to system. This is usually done automatically, but is made manual here for illustration.

There is also a test script to report system status. It can be run with `python status.py` or `klayout -r status.py`.


## Try it
This is your test flow: run setup.py in both. Then clean out either klayout or system or neither. Then run the tests to your liking.

Interesting excercise: clean the system, open klayout. Try running status.py as *both* python and klayout -r. Then, in the klayout menu, press "export lybar". Try the status calls again.

Does it work the same when klayout.app is launched from Dock vs. command-line?
