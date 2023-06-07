import dataclasses
import datetime as dt
import logging
import platform
import random
import typing as t

from collections import UserDict, UserList
from contextlib import contextmanager

from .. import __version__
from ..exceptions import (
    ServiceNotRegistered,
    ServiceReceiveCapabilityError,
    ServiceSendCapabilityError,
)
from ..signals import (
    on_after_send,
    on_before_send,
    on_close_session,
    on_open_session,
    on_receive_message,
    on_receive_status_callback,
    on_register_service,
    on_unregister_service,
)

USER_AGENT = (
    f"owlery/{__version__} "
    f"{platform.python_implementation()}/{platform.python_version()}"
)


@dataclasses.dataclass
class Attachment:
    """A representation of an attachment.

    :param data: Bytes or file-like object contain attachment data.
    :param mimetype: Mimetype of the attachment, defaults to
                     ``'application/octet-stream'``.

    """

    data: t.Union[bytes, t.IO[bytes]]
    mimetype: str = "application/octet-stream"


MessageStatus = t.Literal[
    "draft",
    "queued",
    "sent",
    "received",
    "read",
    "cancelled",
    "error",
]


@dataclasses.dataclass
class Message:
    """A representation for a received messages.

    :param id: The message unique identifier.
    :param reply_id: The message identifier this message is replied to.
    :param date: The date the message was sent/received.
    :param raw: The raw data response from service.
    :param status: The message status.
    :param exc: The exception object if an error occured.
    :param service: Service to use for sending, replies and fowarding.

    """

    id: t.Optional[str] = None
    reply_id: t.Optional[str] = None
    date: t.Optional[dt.datetime] = None
    raw: t.Any = None
    status: MessageStatus = "draft"
    exc: t.Optional[Exception] = None
    service: t.Optional["Service"] = None

    def as_dict(self):
        return dataclasses.asdict(self)

    def send(self, service=None):
        if not service:
            service = self.service
        if not service:
            raise ValueError("No service to send this message")

        return service.send_message(self)


class MessageBuilder(UserDict):
    def __init__(self, dict=None, service=None, **kwargs):
        self.service = service

        super().__init__(dict, **kwargs)

    def _replace(self, **kwargs):
        message = self.copy()
        message.update(**kwargs)

        return message

    def send(self):
        service = self.service
        if not service:
            raise ValueError("No service to send this message")

        return service.send(**self.data)


class Outbox(UserList):
    """Outbox containing captured messages.

    :param suppress: Do not send messages when released.

    """

    def __init__(self, service, suppress=False):
        self.service = service
        self.suppress = suppress

        super().__init__()

    def append(self, item):
        super().append(item)

        self.service.logger.debug("Enqueued a message in outbox:\n%r", item)

    def clear(self):
        count = len(self.data)

        super().clear()

        self.service.logger.debug("Discarded %d messages from outbox", count)

    def discard(self):
        """Discard all messages."""
        self.clear()

    def release(self):
        """Release messages to be sent, unless :data:``suppress`` is set."""
        # if self.suppress:
        #     self.data.clear()

        count = len(self.data)

        with on_before_send.muted():
            while self.data:
                service, message = self.data.pop()
                service.send(**message)

        self.service.logger.debug("Released %d messages from outbox", count)


class Service:
    """Base class for all services."""

    name: str

    can_receive: bool = False
    can_send: bool = False

    has_receive_webhook = False
    has_receive_webhook_methods = ["POST"]

    has_status_callback = False
    has_status_callback_methods = ["POST"]

    def __init__(self, suppress=False, **kwargs):
        self.opened = False
        """Whether a connection or session has been started."""

        self.suppress = suppress
        """Suppress sending of messages."""

        self._media_helper = None

        self._wrap_methods()

        self.logger = logging.getLogger(__name__)

    def _on_receive_message(self, message):
        message.status = "received"

        on_receive_message.send(self, message=message)

        self.logger.debug("Received message:\n%r", message)

    def _wrap_close(self):
        # wrap the close method:
        # - dispatch the `on_session_close` signals.
        # - unset the ``opened`` flag.
        # - log a message.
        original_close = self.close

        def close(self):
            original_close()

            on_close_session.send(self)

            self.logger.debug("Closed session")

            self.opened = False

        self.close = close.__get__(self, Service)
        self._close = original_close

    def _wrap_methods(self):
        # wrap all methods
        self._wrap_close()
        self._wrap_open()
        self._wrap_receive()
        self._wrap_receive_webhook()
        self._wrap_send()
        self._wrap_status_callback()

    def _wrap_open(self):
        # wrap the open method:
        # - dispatch `on_session_open` signals.
        # - set the ``opened`` flag.
        # - log a message.

        original_open = self.open

        def open(self):
            original_open()

            on_open_session.send(self)

            self.logger.debug("Opened session")

            self.opened = True

        self.open = open.__get__(self, Service)
        self._open = original_open

    def _wrap_receive(self):
        # wrap the receive method:
        # - dispatch `on_receive_message` signals.
        # - open the connection or session if ``opened`` flag not set.
        # - log messages.

        original_receive = self.receive

        def receive(self, **kwargs):
            if not self.opened:
                self.open()

            count = 0
            for message in original_receive(**kwargs):
                self._on_receive_message(message)

                yield message
                count += 1

            self.logger.info("Received %d messages", count)

        self.receive = receive.__get__(self, Service)
        self._receive = original_receive

    def _wrap_receive_webhook(self):
        # wrap the receive_webhook method:
        # - dispatch `on_receive_message` signals.
        # - log messages.

        original_receive = self.receive_webhook

        def receive_webhook(self, request):
            count = 0
            for message in original_receive(request):
                self._on_receive_message(message)

                yield message
                count += 1

            self.logger.info("Received %d messages from webhook", count)

        self.receive_webhook = receive_webhook.__get__(self, Service)
        self._receive_webhook = original_receive

    def _wrap_send(self):
        # wrap the send method:
        # - dispatch ``on_before_send`` and ``on_after_send`` signals.
        # - open the connection or session if ``opened`` flag not set.
        # - silently discard the message if ``suppress`` flag is set.
        # - log messages.

        original_send = self.send

        def send(self, **kwargs):
            on_before_send.send(self, message=kwargs)

            if self.suppress:
                return

            if not self.opened:
                self.open()

            message = original_send(**kwargs)

            on_after_send.send(self, message=message)

            # self.logger.info("Sent message %s", message.id)
            # self.logger.debug("%r", message)

            return message

        self.send = send.__get__(self, Service)
        self._send = original_send

    def _wrap_status_callback(self):
        # wrap the status_callback method:
        # - dispatch ``on_receive_status_callback`` signals.
        # - log messages.

        original_status = self.status_callback

        def status_callback(self, request):
            message_id, status, raw = original_status(request)
            on_receive_status_callback.send(
                self,
                message_id=message_id,
                status=status,
                raw=raw,
            )

            self.logger.info(
                "Received message status: %s, %s",
                message_id,
                status,
            )

            return message_id, status, raw

        self.status_callback = status_callback.__get__(self, Service)
        self._status_callback = original_status

    def __enter__(self):
        if not self.opened:
            self.open()

        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()

    def close(self):
        """Close a session or connection.

        Developers SHOULD implement this method if they need to cleanup or
        disconnect from a session.

        This is called at the end of a context manager, otherwise must be
        called manually.

        """
        return

    def generate_media_urls(self, attachments: t.List[Attachment]):
        """Generate URLs for services that require external media URLs."""
        urls = []
        for attachment in attachments:
            url = self._media_helper(attachment)
            urls.append(url)
        return urls

    def open(self):
        """Open or prepare a connection or session.

        Developers SHOULD implement this method if they need to setup or
        configure a connection.

        This is called on first send and called at the start of a context
        manager.

        """
        return

    def media_helper(self, f):
        """Register a function to help with external media."""
        self._media_helper = f

    @contextmanager
    def outbox(self):
        """Capture outgoing messages.

        On exit, the messages will be released and sent.

        You can call the :meth:`release` method manually:

        .. code-block:: python

            with service.outbox() as outbox:
                service.send(...)

                outbox.release()  # all messages are sent


        You can call the :meth:`discard` method to discard all messages:

        .. code-block:: python

            with service.outbox() as outbox:
                service.send(...)

                outbox.discard()  # all messages are discarded

            # nothing is sent

        """
        outbox = Outbox(self, suppress=self.suppress)

        def capture(this, kwargs):
            outbox.append((this, kwargs))

        on_before_send.connect(capture)

        original_suppress = self.suppress
        self.suppress = True

        try:
            yield outbox
        except Exception:
            outbox.discard()
            raise
        finally:
            on_before_send.disconnect(capture)
            self.suppress = original_suppress

        outbox.release()

    def receive(
        self,
        limit: int = 100,
        **kwargs,
    ) -> t.Generator[Message, None, None]:
        """Receive messages.

        Developers MUST implement this method.

        :param limit: Limit number of messages fetched.

        :raises ServiceReceiveCapabilityError: Receiving not supported.

        :return: A received message.
        :rtype: Message

        """
        name = self.__class__.__name__
        raise ServiceReceiveCapabilityError(name=name)

    def receive_webhook(self, request):
        """Receive messages from a webhook.

        Developers SHOULD implement this method.

        :param request: The request to parse.

        :raises ServiceReceiveCapabilityError: Receiving not supported.

        """
        name = self.__class__.__name__
        raise ServiceReceiveCapabilityError(name=name)

    def send(self, *args, **kwargs):
        """Send a message.

        Developers MUST implement this method.

        :raises ServiceSendCapabilityError: Sending messages not supported.

        """
        name = self.__class__.__name__
        raise ServiceSendCapabilityError(name=name)

    def send_message(self, message: Message):
        """Send a message from a message object.

        :param message: A :class:`Message` message object.

        """
        data = message.as_dict()
        data["service"] = self
        return message.send(**data)

    def status_callback(self, request):
        """Receive sent message status callback from a webhook.

        Developers SHOULD implement this method.

        :param request: The request to parse.

        :raises NotImplementedError: Status callback not supported.

        """
        raise NotImplementedError()

    @contextmanager
    def suppressed(self):
        """Suppress outgoing messages for duration of the context manager."""
        original_suppress = self.suppress
        self.suppress = True

        try:
            yield
        finally:
            self.suppress = original_suppress


class ServiceManager(Service):
    """Base class for all service managers."""

    can_receive = True
    can_send = True

    _wrap_close = property()
    _wrap_open = property()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.services = {}
        """Registered messaging services."""

        self._via = None

        self._update_methods()

    def _update_methods(self):
        # update methods for service managers
        self._update_receive()
        self._update_send()

    def _update_receive(self):
        # update the send method:
        # - dispatch ``on_receive_message`` signal.
        # - select the correct service with ``via`` or receive on all services

        def receive(self, limit=100, via=None, **kwargs):
            services = []
            if via:
                try:
                    service = self.services[via]
                except KeyError:
                    raise ServiceNotRegistered(via)
                else:
                    services.append(service)
            else:
                # get all services in a random order to prevent a single
                # service from blocking all other services
                services = list(
                    s for s in self.services.values() if s.can_receive
                )
                random.shuffle(services)

            if not services:
                raise ServiceReceiveCapabilityError()

            for service in services:
                for message in service.receive(limit=limit, **kwargs):
                    # if service cannot send replies, set to manager
                    if not service.can_send:
                        message.service = self
                    on_receive_message.send(self, message=message)
                    yield message
                    limit -= 1

        self.receive = receive.__get__(self, ServiceManager)

    def _update_send(self):
        # update the send method:: bool = False
        # - dispatch ``on_before_send`` and ``on_after_send`` signals.
        # - silently discard the message if ``suppress`` flag is set.
        # - select the correct service, either default or ``via``.

        def send(self, via=None, **kwargs):
            service = None

            if self._via and not via:
                via = self._via(self, **kwargs)

            if via:
                try:
                    service = self.services[via]
                except KeyError:
                    raise ServiceNotRegistered(via)

            if not service:
                try:
                    service = list(
                        s for s in self.services.values() if s.can_send
                    )[0]
                except IndexError:
                    raise ServiceSendCapabilityError()

            on_before_send.send(service, kwargs=kwargs)

            if self.suppress:
                return

            result = service.send(**kwargs)

            on_after_send.send(self, kwargs=kwargs)

            return result

        self.send = send.__get__(self, ServiceManager)

    def _wrap_methods(self):
        return

    def close(self):
        for service in self.services.values():
            if service.opened:
                service.close()

    def ensure_service(
        self,
        name: t.Optional[str] = None,
        receive: bool = False,
        send: bool = False,
    ):
        """Ensure a service is registered.

        :param name: Optional name to check, if not specified then ensure that
            at least one service is registered.
        :param receive: Ensure service can receive messages.
        :param send: Ensure service can send messages.

        :raises ServiceNotRegistered: No service or service with name
            registered.
        :raises ServiceReceiveCapabilityError: No service or service with name
            with receive capability.
        :raises ServiceSendCapabilityError: No service or service with name
            with sending capability.

        """
        if name:
            try:
                service = self.services[name]
            except KeyError:
                raise ServiceNotRegistered(name)

            if receive and not service.can_receive:
                raise ServiceReceiveCapabilityError(name)
            if send and not service.can_send:
                raise ServiceSendCapabilityError(name)
        else:
            if len(self.services) == 0:
                raise ServiceNotRegistered()

            found_receive = found_send = False

            for service in self.services.values():
                if service.can_receive:
                    found_receive = True
                if service.can_send:
                    found_send = True

            if receive and not found_receive:
                raise ServiceReceiveCapabilityError()
            if send and not found_send:
                raise ServiceSendCapabilityError()

    def media_helper(self, f):
        """Register a function to help with external media."""
        super().media_helper(f)

        for service in self.services.values():
            service.media_helper(f)

    def register(
        self,
        service_cls,
        *args,
        name=None,
        overwrite=False,
        **kwargs,
    ):
        r"""Register a service.

        :param service_cls: The service to register and initialise.
        :param \*args: Positional arguments to pass to the service on
                       initialisation.
        :param name: Name to use for the service, defaults to ``name`` of the
                     service.
        :param overwrite: Overwrite an existing service with ``name``, defaults
                          to ``False``.
        :param \*\*kwargs: Keyword-arguments to pass to the service on
                           initialisation.

        """
        if not name:
            name = service_cls.name
        if name in self.services and not overwrite:
            raise KeyError(f"Service '{name}' already exists")

        service = service_cls(*args, **kwargs)

        if self._media_helper:
            service.media_helper(self._media_helper)

        self.services[name] = service

        on_register_service.send(self, service=service)

        self.logger.info("Registered a service: %s", service.name)

        return service

    def unregister(self, service, ignore_missing=False):
        """Unregister a service.

        :param service: The service or service name to unregister.
        :param ignore_missing: Do not raise an exception if service does not
                               exist on manager, defaults to ``False``.

        """
        if isinstance(service, str):
            try:
                service = self.services.pop(service)
            except KeyError:
                if ignore_missing:
                    return
                raise KeyError(f"Service '{service}' does not exist")
        else:
            name = None
            for name, service_ in self.services.items():
                if service is service_:
                    name = name
                    break
            else:
                if ignore_missing:
                    return
                raise KeyError(f"Service '{service!r}' does not exist")

            service = self.services.pop(name)

        on_unregister_service.send(self, service=service)

        self.logger.info("Unregistered a service: %s", service.name)

    def via(
        self,
        f: t.Callable[
            ["ServiceManager", "t.ParamSpecKwargs"],
            t.Optional[str],
        ],
    ):
        """Register a function to select the service based on message."""
        self._via = f
