import logging
import typing as t

from . import Service


class Logger(Service):
    """Service that logs sent messages to a logger.

    :param logger: Name of the logger, defaults to root logger.
    :param level: Level of logging message, defaults to ``logging.INFO`` (or
                  ``20``)
    :param message: Message template, receives the message keyword-arguments
                    for formatting, defaults to ``'Message sent %s'``

    """

    name = "logger"
    can_send = True

    def __init__(
        self,
        logger: t.Optional[str] = None,
        level: int = logging.INFO,
        message: str = "Message sent %s",
        **kwargs,
    ):
        self.logger = logging.getLogger(logger)
        self.level = level
        self.message = message

        super().__init__(**kwargs)

        self.suppress = False

    def send(self, **kwargs):
        self.logger.log(self.level, self.message, kwargs, extra=kwargs)


class Null(Service):
    """Service that silently discards messages."""

    name = "null"
    can_send = True

    def send(self, **kwargs):
        return


class ReceiveFunction(Service):
    """Service to call a function to receive messages.

    :param func: Function to call.

    """

    name = "receive_function"
    can_receive = True

    def __init__(self, func: t.Callable, **kwargs):
        self.func = func

        super().__init__(**kwargs)

    def receive(self, **kwargs):
        return self.func(**kwargs)


class SendFunction(Service):
    """Service to call a function to send messages.

    :param func: Function to call.

    """

    name = "send_function"
    can_send = True

    def __init__(self, func: t.Callable, **kwargs):
        self.func = func

        super().__init__(**kwargs)

    def send(self, **kwargs):
        return self.func(**kwargs)
