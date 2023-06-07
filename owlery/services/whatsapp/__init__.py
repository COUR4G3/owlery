import dataclasses
import typing as t

import phonenumbers

from .. import Attachment, Message, MessageBuilder, Service, ServiceManager


@dataclasses.dataclass
class WhatsAppLocation:
    lat: float
    lon: float
    address: t.Optional[str] = None
    label: t.Optional[str] = None


@dataclasses.dataclass
class WhatsAppMessage(Message):
    """A representation of a WhatsApp message.

    :param to: The recipient number.
    :param body: The text message body.
    :param from_: The sender number.
    :param attachments: A list of :class:`owlery.services.Attachment` objects.
    :param location: An optional location pin as :class:`WhatsAppLocation`.
    :param profile_name: The public WhatsApp profile name.
    :param fowarded: Whether the message has been forwarded.
    :param frequently_forwarded: Whether the message has been frequently
        forwarded.
    :param id: The message unique identifier.
    :param reply_id: The message identifier this message is replied to.
    :param raw: The raw data response from service.
    :param service: Service to use for sending, replies and fowarding.

    """

    to: t.Optional[str] = None
    body: t.Optional[str] = None
    from_: t.Optional[str] = None
    attachments: t.List[Attachment] = dataclasses.field(default_factory=list)
    location: t.Optional[WhatsAppLocation] = None
    profile_name: t.Optional[str] = None
    forwarded: bool = False
    frequently_forwarded: bool = False

    def attach(
        self,
        data: t.Union[bytes, t.IO[bytes]],
        mimetype: str = "application/octet-stream",
    ):
        attachment = Attachment(data, mimetype)
        self.attachments.append(attachment)

    @classmethod
    def builder(self):
        return WhatsAppMessageBuilder()

    def forward(self, to: str, service=None, **kwargs):
        if not service:
            service = self.service
        if not service or not service.can_send:
            raise ValueError("No service to foward this message")

        return service.send(
            to=to,
            body=self.body,
            attachments=self.attachments,
            location=self.location,
            **kwargs,
        )

    def reply(self, body: str, service=None, **kwargs):
        if not service:
            service = self.service
        if not service or not service.can_send:
            raise ValueError("No service to reply to this message")

        return service.send(
            to=self.from_,
            body=body,
            from_=self.to,
            **kwargs,
        )


class WhatsAppMessageBuilder(MessageBuilder):
    """Build a WhatsApp message."""

    def attach(
        self,
        data: t.Union[bytes, t.IO[bytes]],
        mimetype: str = "application/octet-stream",
    ):
        attachment = Attachment(data, mimetype)

        attachments = self.get("attachments")
        if attachments:
            attachments = attachments.copy()

        attachments.append(attachment)

        return self._replace(attachments=attachments)

    def body(self, body: str):
        return self._replace(body=body)

    def from_(self, from_: str):
        return self._replace(from_=from_)

    def location(
        self,
        lat: float,
        lon: float,
        address: t.Optional[str] = None,
        label: t.Optional[str] = None,
    ):
        return self._replace(
            location=WhatsAppLocation(lat, lon, address, label),
        )

    def to(self, to: str):
        return self._replace(to=to)


class WhatsApp(Service):
    """Base class for an WhatsApp messaging service."""

    name = "whatsapp"

    def __init__(
        self,
        region: t.Optional[str] = None,
        sender_id: t.Optional[str] = None,
        **kwargs,
    ):
        self.region = region
        self.sender_id = sender_id

        super().__init__(**kwargs)

    def format_number(self, number):
        number = phonenumbers.parse(number, self.region)
        number = phonenumbers.format_number(
            number,
            phonenumbers.PhoneNumberFormat.E164,
        )

        return number

    def receive(self, limit: int = 100, **kwargs):
        """Receive WhatsApp messages.

        :param limit: Limit number of messages received, defaults to ``100``.

        """
        ...

    def send(
        self,
        to: str,
        body: str,
        from_: t.Optional[str] = None,
        attachments: t.Optional[t.List[Attachment]] = None,
        location: t.Optional[WhatsAppLocation] = None,
        **kwargs,
    ):
        """Send a WhatsApp message.

        :param to: The message receipient number.
        :param body: Text body of the message.
        :param from_: The message sender number.
        :param attachments: A list of attachments i.e. images, videos.
        :param location: A location, latitude, longitude and optional name.

        """
        ...

    def send_message(self, message):
        """Send a WhatsApp message from a message object.

        :param message: A :class:`WhatsAppMessage` message object.

        """
        return message.send(service=self)


class WhatsAppManager(WhatsApp, ServiceManager):
    """Service manager for WhatsApp messaging services."""

    def register(self, service_cls, **kwargs):
        kwargs.setdefault("region", self.region)
        return super().register(service_cls, **kwargs)
