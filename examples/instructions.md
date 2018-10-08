## There are 3 packages
lypy_hybrid (klayout), lybar (within lypy_hybrid), lyfoo (pure python)

When you run setup.py in either python package, they will be installed in the system (that's the point), and transferred to the klayout namespace.

When you install lypy_hybrid through salt, or if you open klayout, lybar will be exported to the system.

## Tests
lypy_hybrid gives you two menu buttons. One checks for a successful call passing through lybar and lyfoo. Another performs the lybar export to system. This is usually done automatically, but is made manual here for illustration.

Does it work the same when klayout.app is launched from Dock vs. command-line?

Case 1: lyfoo not linked. Press the button. It should fail.

Case 2: lyfoo