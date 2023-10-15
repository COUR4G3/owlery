.. currentmodule:: owlery.integrations.flask

Flask
=====

Integrate messaging in your Flask application and configure messaging managers and services based on your Flask
:doc:`configuration handling <flask:config>`.


Initializing the extension
--------------------------

To initialize the integration, instantiate the :class:`Owlery` class and pass the ``app`` instance:

.. autoclass:: Owlery


or you can use the :doc:`application factory pattern <flask:patterns/appfactories>` and
:meth:`init_app <Owlery.init_app>`:

.. automethod:: Owlery.init_app


.. code-block:: python

    owlery = Owlery()

    # ... later in your application factory function after configuration

    owlery.init_app(app)


Configuration
-------------

The extension accepts the following configuration variables:

=============== ===============================================================
Key             Description
=============== ===============================================================
OWLERY_SUPPRESS Suppress sending of messages, defaults to ``app.testing``.
=============== ===============================================================


Each service and/or manager expects one or more configuration keys of the form:

``OWLERY_{MANAGER}_{SERVICE}_{KEY}``


where ``MANAGER`` is the uppercase form of the ``name`` passed to the manager in
:meth:`register <Owlery.register>` method and ``SERVICE`` would be uppercase form of the ``name`` passed to the service
in the :meth:`register <owlery.services.ServiceManager.register>`. If no ``name`` is passed for either or both, then
``DEFAULT`` will be used.


An example configuration:

.. code-block:: python

    OWLERY_EMAIL_DEFAULT_CLS = "owlery.services.email.smtp.SMTP"
    OWLERY_EMAIL_DEFAULT_HOST = "localhost"
    OWLERY_EMAIL_DEFAULT_PORT = 25


Once you configure the extension and manager, for example:

.. code-block:: python

    from owlery.integrations.flask import Owlery
    from owlery.services.email import EmailManager

    from .app import app

    owlery = Owlery(app)

    email = owlery.register(EmailManager, name="email")


The previous configuration will result in roughly the following:

.. code-block:: python

    from owlery.services.email import EmailManager
    from owlery.services.email.smtp import SMTP

    email = EmailManager()
    email.register(SMTP, host="localhost", port=25)


API Reference
-------------

.. autoclass:: owlery.integrations.flask.Owlery
    :members:
    :noindex:
