Email
=====

Send and receive email messages in your applications.


Services
--------

.. toctree::
   :maxdepth: 1

   imap
   pop3
   smtp


Sending messages
----------------

You can send a message with the :meth:`send <owlery.services.email.Email.send>` method:

.. automethod:: owlery.services.email.Email.send


Building messages
~~~~~~~~~~~~~~~~~

You can build an email message with the :class:`EmailMessage <owlery.services.email.EmailMessage>` class and call the
:meth:`send_message <owlery.services.email.Email.send_message>` method:

.. code-block:: python

   message = EmailMessage(
      subject="Test message",
      body="This is a test message",
      html_body="<p>This is a test message.</p>",
      to=["someone@example.com"],
      from_="admin@example.com",
   )

   email.send_message(message)


You can alternatively, `fluently <https://en.wikipedia.org/wiki/Fluent_interface>`_ build an email message with the
:meth:`Message <owlery.services.email.Email.Message>` method to call the
:class:`EmailMessageBuilder <owlery.services.email.EmailMessageBuilder>`:

.. code-block:: python

   message = email.Message() \
      .subject("Test message") \
      .body("This is a test message.") \
      .html_body("<p>This is a test message.</p>") \
      .to(["someone@example.com"]) \
      .from_("admin@example.com") \
      .send()


The full interface of the :class:`EmailMessageBuilder <owlery.services.email.EmailMessageBuilder>`:

.. autoclass:: owlery.services.email.EmailMessageBuilder
   :exclude-members: attach
   :members:


Receiving messages
------------------

You can receive one or more messages with the :meth:`receive <owlery.services.email.Email.receive>`
method:

.. automethod:: owlery.services.email.Email.receive


It will return up to ``limit`` :class:`EmailMessage <owlery.services.email.EmailMessage>` objects.

The full interface of the :class:`EmailMessage <owlery.services.email.EmailMessage>`:

.. autoclass:: owlery.services.email.EmailMessage
   :members:


Attachments
-----------

Email messages can accept any number of attachments, however certain services and providers may put
limits on the size, number, total size and file type of attachments.

It is recommended to send only audio, image and video attachments as well as documents such as PDF
and documents. Other file types may be rejected by services, providers or virus scanners.

The full interface of the :class:`EmailAttachment <owlery.services.email.EmailAttachment>` class:

.. autoclass:: owlery.services.email.EmailAttachment
   :members:


You can provide one or more attachments as a list to your
:meth:`send <owlery.services.email.Email.send>` method. Or when constructing a message with the
fluent interface you can use the :meth:`attach <owlery.services.email.EmailMessageBuilder.attach>`
method:

.. automethod:: owlery.services.email.EmailMessageBuilder.attach


On a received :class:`EmailMessage <owlery.services.email.EmailMessage>` you can access the list of
:class:`EmailAttachment <owlery.services.email.EmailAttachment>` objects from the
:attr:`attachments <owlery.services.email.EmailAttachment.attachments>` attribute.


API Reference
-------------

.. autoclass:: owlery.services.email.Email
   :exclude-members: Message, receive, send
   :members:
