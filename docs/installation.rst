Installation
============

Install the latest release from the `Python Package Index (PyPI) <https://pypi.org/project/owlery>`_:

.. prompt:: bash

    pip install owlery


Or, install from the `GitHub <https://github.com/COUR4G3/owlery>`_:

.. prompt:: bash

    git clone https://github.com/COUR4G3/owlery
    cd owlery
    pip install .


Optional Dependencies
---------------------

You can install optional dependencies by:

.. prompt:: bash

    pip install owlery[dev,...]


There are a number of optional dependency targets:

* **dev**: dependencies for development and style checking.
* **docs**: dependencies for building the documentation.
* **tests**: dependencies for running the tests.
* **typing**: dependencies for static type checking.


Some can be installed directly from the ``requirements.txt`` for certain targets:


dev
~~~

.. prompt:: bash

    pip install -r dev/requirements.txt


docs
~~~~

.. prompt:: bash

    pip install -r docs/requirements.txt


tests
~~~~~

.. prompt:: bash

    pip install -r tests/requirements.txt


typing
~~~~~~

.. prompt:: bash

    pip install -r typing/requirements.txt
