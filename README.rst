mr3po
=====

*"Protocols? Why, those are my primary function!"*

**mr3po** is a library of line-based `custom protocols <http://packages.python.org/mrjob/protocols.html#custom-protocols>`_ for use with the `mrjob <http://packages.python.org/mrjob/>`_ library.

**mr3po** is about the easiest Open Source project to contribute to. Just submit a class that can read and write an existing line-based format, and you've made a useful contribution.

Some guidelines for contributions:

* put the code for your format in ``mrjob/<format name>.py``
* include tests, in ``tests/test_<format name>.py``.
* the name of your protocol class(es) should end in ``Protocol``
* if your protocol class(es) only handle single values (rather than key-value pairs), their name should end in ``ValueProtocol``
* external dependencies are fine, but should be optional; add them to ``extras_require`` in ``setup.py``.
