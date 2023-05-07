import typing as t


class OwleryException(Exception):
    """Base class for all Owlery exceptions."""

    def __init__(self, description, *args, exc_info=None):
        self.description = str(description)
        self.exc_info = exc_info

        super().__init__(description, *args)

    def __repr__(self):
        name = self.__class__.__name__
        return f"{name}: {self.description}"

    def __str__(self):
        return self.description


class SmsBodyTooLarge(OwleryException):
    """SMS body size exceeds what service can send."""

    description = "SMS body size exceeds what service can send"

    def __init__(self, body, max_size=160, service=None):
        self.body = body
        self.max_size = max_size
        self.service = service

        super().__init__(
            "SMS body size exceeds what service can send.",
            body,
            max_size,
            service,
        )

    @property
    def size(self):
        return len(self.body)


class ServiceAuthFailed(OwleryException):
    """Service authentication failed."""

    def __init__(self, exc_info):
        super().__init__("Service authentication failed.", exc_info=exc_info)


class ServiceConfigError(OwleryException):
    """Service not configured correctly."""

    def __init__(self, exc_info):
        super().__init__(
            "Service not configured correctly.",
            exc_info=exc_info,
        )


class ServiceConnectError(OwleryException):
    """Service connection error."""

    def __init__(self, exc_info):
        super().__init__(exc_info, exc_info=exc_info)


class ServiceNotRegistered(OwleryException):
    """Service not registered on a service manager."""

    def __init__(self, name: t.Optional[str] = None):
        if name:
            description = f"Service '{name}' not registered on this manager"
        else:
            description = "No service registered on this manager"

        super().__init__(description, name)


class ServiceReceiveCapabilityError(OwleryException):
    """Service cannot receive messages."""

    def __init__(self, name: t.Optional[str] = None):
        if name:
            description = f"Service '{name}' cannot receive messages"
        else:
            description = "No service registered to receive on this manager"

        super().__init__(description, name)


class ServiceSendCapabilityError(OwleryException):
    """Service cannot send messages."""

    def __init__(self, name: t.Optional[str] = None):
        if name:
            description = f"Service '{name}' cannot send messages"
        else:
            description = "No service registered to send on this manager"

        super().__init__(description, name)


class ServiceTimeoutError(OwleryException):
    """Service connection timeout."""

    def __init__(self, exc_info):
        super().__init__(exc_info, exc_info=exc_info)
