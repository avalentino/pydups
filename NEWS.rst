PyDups Change History
=====================

PyDups 1.1.0 (under development)
--------------------------------

* The main program now returns a meaningful exit code
  (previously always returned zero).
* Improved exception handling: all exceptions are now caught and logged.
* PyDups command line tool now support auto-completion via
  `argcomplete <https://pypi.org/project/argcomplete/>`_.
* Improved `setup.py` (dependency management).
* Added requirements file.
* Improved testing:

  - added new tests
  - reworked existing tests to be fully compatible with
    `pytest <https://pytest.org>`_
  - testing enabled on `Travis <https://travis-ci.org/>`_
    (see https://travis-ci.org/avalentino/pydups).


PyDups 1.0.0 (25/22/2017)
-------------------------

* Initial release.

