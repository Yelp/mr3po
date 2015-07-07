# mr3px

*This package is forked from [mr3po](https://github.com/yelp/mr3po)*

> "The 3PX-series protocol droid were third-degree protocol droids produced by Cybot Galactica in 50 BBY and based on the design of the company's 3PO-series protocol droid." *[Wookiepedia](http://starwars.wikia.com/wiki/3PX-series_protocol_droid)*

**mr3px** is a library of line-based [custom protocols](http://packages.python.org/mrjob/protocols.html#custom-protocols) for use with the [mrjob](http://packages.python.org/mrjob/) library.

## Installing

To install this version with pip:

    pip install mr3px

If you plan to use it on EMR, then you'll need to install it in the bootstrap step.

## Contributing

**mr3px** is about the easiest Open Source project to contribute to. Just submit a class that can read and write an existing line-based format, and you've made a useful contribution.

Some guidelines for contributions:

  - put the code for your format in ``mrjob/<format name>.py``
  - the name of your protocol class(es) should end in ``Protocol``
  - if your protocol class(es) only handle single values (rather than key-value pairs), their name should end in ``ValueProtocol``
  - include tests, in ``tests/test_<format name>.py``. At least one test should inherit from ``tests.roundtrip.RoundTripTestCase``.
  - external dependencies are fine, but should be optional; add them to ``extras_require`` in ``setup.py``.


