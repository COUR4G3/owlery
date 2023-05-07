Getting Started
===============

Firstly, we should initialise the appropriate :class:`ServiceManager <owlery.services.ServiceManager>` for our messaging
medium and then register one or more :class:`Service <owlery.services.Service>` instances.

In our examples we'll be using the :class:`EmailManager <owlery.services.email.EmailManager>` to send email messages,
however all the same applies to other messaging managers, only the :meth:`send <owlery.services.Service>` method may
vary in what arguments it takes:


.. code-block:: python

    from owlery.services.email import EmailManager
    from owlery.services.email.smtp import SMTP

    email = EmailManager()

    email.register_service(SMTP, hostname="localhost", port=25)


We will be using the :class:`SMTP <owlery.services.email.smtp.SMTP>` service to send emails. We can send an email
message:

.. code-block:: python

    email.send(
        to=["someone@example.com"],
        subject="Test message",
        body="This is a test message",
    )


This will immediately send an email message using the default provider, which in this case if the first one that we
registered.

We can also batch our message sending, to re-use an existing session or connection instead of reconnecting each time we
send a message, this will also ensure our session or connection is closed after the messages are sent:


.. code-block:: python

    with email:
        email.send(
            to=["someone@example.com"],
            subject="Test message",
            body="This is a test message",
        )

        email.send(
            to=["someone@example.com"],
            subject="Another test message",
            body="This is another test message",
        )


We can register more services to send messages, for instance we may want to use a different email server for sending
our marketing emails versus our important notifications, we register the new service with a user-defined ``name`` and
specify which service to use when sending with the ``via`` keyword-argument:


.. code-block:: python

    email.register_service(SMTP, hostname="localhost", port=26, name="bulk")

    email.send(
        to=["someone@example.com"],
        subject="Test message",
        body="This is a test message",
        via="bulk",
    )


We can also automatically send messages via the appropriate service by passing a callable function to the manager,
which will be called with each message to choose the appropriate service automatically:


.. code-block:: python

    email.register_service(
        SMTP, hostname="server.eu", port=25, name="eu-server"
    )

    @email.via
    def via(to, **kwargs):
        if to.endswith(".eu", ".uk"):
            return "eu-server"
        return None  # use the default


The following email message will be sent via the default service:

.. code-block:: python

    email.send(
        to=["someone@example.com"],
        subject="Test message",
        body="This is a test message",
        from_="info@example.com",
    )


However this email message will be sent by our special ``'eu-server'`` service:

.. code-block:: python

    email.send(
        to=["someone@example.eu"],
        subject="Test message",
        body="This is a test message",
        from_="info@example.com",
    )


Receiving messages is much simpler, in this example we'll use the :class:`IMAP <owlery.services.email.imap.IMAP>`
service to receive messages:


.. code-block:: python

    from owlery.services.email.imap import IMAP

    email.register_service(
        IMAP, host="localhost", port=143, user="user", password="pass",
    )

    for message in email.receive():
        print(message)


If you registered more than one service that was capable of receiving messages it would receive for all the services:

.. code-block:: python

    email.register_service(
        IMAP,
        host="localhost",
        port=143,
        user="user2",
        password="pass",
        name="user2-mailbox",
    )

    for message in email.receive():
        print(message)


You could also specify to receive for a specific service with the ``via`` keyword-argument:

.. code-block:: python

    for message in email.receive(via="user2-mailbox"):
        print(message)
