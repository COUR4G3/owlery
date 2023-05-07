Signals
=======

Signals are a lightweight way to notify subscribers of certain events in services and service managers. When an event
occurs, it emits the signal, which calls each subscriber.

Signals are implemented with the `Blinker <https://pypi.org/project/blinker/>`_ library. See its documentation for
detailed information on the inner workings.


.. currentmodule:: owlery.signals

.. data:: on_after_send

    This signal is sent when a message is successfully sent. The signal is invoked with the service as ``sender`` and
    the message keyword-arguments as dictionary (named ``message``).

    Example subscriber::

        from owlery.signals import on_after_send

        def print_message_sent(sender, message):
            print("Sent message using '%s': %s", sender.name, message)

        on_after_send.connect(print_message_sent)


.. data:: on_close_session

    This signal is sent when a session or connection is closed. The signal is invoked with the service as ``sender``.

    Example subscriber::

        from owlery.signals import on_close_session

        def print_close_session(sender):
            print("Session for '%s' closed", sender.name)

        on_close_session.connect(print_close_session)


.. data:: on_before_send

    This signal is sent before a message is sent. The signal is invoked with the service as ``sender`` and the message
    keyword-arguments as dictionary (named ``message``).

    Example subscriber::

        from owlery.signals import on_before_send

        def print_message_send(sender, message):
            print("Sending message using '%s': %s", sender.name, message)

        on_before_send.connect(print_message_send)


.. data:: on_open_session

    This signal is sent when a session or connection is opened. The signal is invoked with the service as ``sender``.

    Example subscriber::

        from owlery.signals import on_open_session

        def print_open_session(sender):
            print("Session for '%s' opened", sender.name)

        on_open_session.connect(print_open_session)


.. data:: on_receive_message

    This signal is sent when a message is received. The signal is invoked with the service as ``sender`` and the message
    object as ``message``.

    Example subscriber::

        from owlery.signals import on_receive_message

        def print_message_received(sender, message):
            print("Received message using '%s': %s", sender.name, message)

        on_receive_message.connect(print_message_received)
