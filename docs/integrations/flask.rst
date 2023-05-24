.. currentmodule:: owlery.integrations.flask

Flask
=====

An simple integration is provided to configure services based on the Flask :doc:`flask:config` along with several other
helpers to configure media URLs, webhooks and status callbacks.


Getting Started
---------------

A simple example of a Flask application with integrated messaging:

.. code-block:: python

    from flask import Flask
    from owlery.integrations.flask import Owlery
    from owlery.services.email import EmailManager
    from owlery.services.email.smtp import SMTP

    app = Flask(__name__)

    app.config["OWLERY_EMAIL_DEFAULT_CLS"] = SMTP
    app.config["OWLERY_EMAIL_DEFAULT_HOST"] = "localhost"
    app.config["OWLERY_EMAIL_DEFAULT_PORT"] = 25

    owlery = Owlery(app)

    email = owlery.register(EmailManager, name="email")

    email.send()

