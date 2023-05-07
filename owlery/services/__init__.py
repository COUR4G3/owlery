import dataclasses
import platform
import random
import typing as t

from collections import UserList
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


@dataclasses.dataclass
class Message:
    """A representation for a received messages."""


class Outbox(UserList):
    """Outbox containing captured messages.

    :param suppress: Do not send messages when released.

    """

    def __init__(self, suppress=False):
        self.suppress = suppress

        super().__init__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type:
            self.discard()
        else:
            self.release()

    def discard(self):
        """Discard all messages."""
        self.data.clear()

    def release(self):
        """Release messages to be sent, unless :data:``suppress`` is set."""
        if self.suppress:
            self.data.clear()

        with on_before_send.muted():
            while self.data:
                service, message = self.data.pop()
                service.send(**message)


class Service:
    """Base class for all services."""

    name: str
    can_receive: bool = False
    can_send: bool = False

    def __init__(self, suppress=False, **kwargs):
        self.opened = False
        """Whether a connection or session has been started."""

        self.suppress = suppress
        """Suppress sending of messages."""

        self._wrap_methods()

    def _wrap_close(self):
        # wrap the close method:
        # - dispatch the `on_session_close` signals.
        # - unset the ``opened`` flag.
        original_close = self.close

        def close(self):
            original_close()

            on_close_session.send(self)

            self.opened = False

        self.close = close.__get__(self, Service)
        self._close = original_close

    def _wrap_methods(self):
        # wrap all methods
        self._wrap_close()
        self._wrap_open()
        self._wrap_receive()
        self._wrap_send()

    def _wrap_open(self):
        # wrap the open method:
        # - dispatch `on_session_open` signals.
        # - set the ``opened`` flag.

        original_open = self.open

        def open(self):
            original_open()

            on_open_session.send(self)

            self.opened = True

        self.open = open.__get__(self, Service)
        self._open = original_open

    def _wrap_receive(self):
        # wrap the receive method:
        # - dispatch `on_receive_message` signals.
        # - open the connection or session if ``opened`` flag not set.

        original_receive = self.receive

        def receive(self, **kwargs):
            if not self.opened:
                self.open()

            for message in original_receive(**kwargs):
                on_receive_message.send(self, message=message)

                yield message

        self.receive = receive.__get__(self, Service)
        self._receive = original_receive

    def _wrap_send(self):
        # wrap the send method:
        # - dispatch ``on_before_send`` and ``on_after_send`` signals.
        # - open the connection or session if ``opened`` flag not set.
        # - silently discard the message if ``suppress`` flag is set.

        original_send = self.send

        def send(self, **kwargs):
            on_before_send.send(self, message=kwargs)

            if self.suppress:
                return

            if not self.opened:
                self.open()

            results = original_send(**kwargs)

            on_after_send.send(self, message=kwargs)

            return results

        self.send = send.__get__(self, Service)
        self._send = original_send

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

    def open(self):
        """Open or prepare a connection or session.

        Developers SHOULD implement this method if they need to setup or
        configure a connection.

        This is called on first send and called at the start of a context
        manager.

        """
        return

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
        outbox = Outbox(suppress=self.suppress)

        def capture(this, kwargs):
            outbox.append((this, kwargs))

        on_before_send.connect(capture, self)

        original_suppress = self.suppress
        self.suppress = True

        try:
            yield outbox
        finally:
            on_before_send.disconnect(capture, self)
            self.suppress = original_suppress

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

    def send(self, *args, **kwargs):
        """Send a message.

        Developers MUST implement this method.

        :raises ServiceSendCapabilityError: Sending messages not supported.

        """
        name = self.__class__.__name__
        raise ServiceSendCapabilityError(name=name)

    @contextmanager
    def suppressed(self):
        """suppress outgoing messages for duration of the context manager."""
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
                    raise RuntimeError(f"No service '{via}' registered")
                else:
                    services.append(service)
            else:
                # get all services in a random order to prevent a single
                # service from blocking all other services
                services = list(
                    s for s in self.services.values() if s.can_receive
                )
                services = random.shuffle(services)

            for service in services:
                for message in service.receive(limit=limit, **kwargs):
                    on_receive_message(self, message=message)
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
                    raise RuntimeError(f"No service '{via}' registered")

            if not service:
                try:
                    service = list(
                        s for s in self.services.values() if s.can_send
                    )[0]
                except IndexError:
                    raise RuntimeError("No sending services registered")

            on_before_send.send(self, kwargs=kwargs)

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
        if name in self.services and not overwrite:
            raise KeyError(f"Service '{name}' already exists")

        service = service_cls(*args, **kwargs)
        self.services[name] = service

        return service

    def unregister(self, service, ignore_missing=False):
        """Unregister a service.

        :param service: The service or service name to unregister.
        :param ignore_missing: Do not raise an exception if service does not
                               exist on manager, defaults to ``False``.

        """
        if isinstance(service, str):
            try:
                return self.services.pop(service)
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

            return self.services.pop(name)

    def via(
        self,
        f: t.Callable[
            ["ServiceManager", "t.ParamSpecKwargs"],
            t.Optional[str],
        ],
    ):
        """Register a function to select the service based on message."""
        self._via = f
