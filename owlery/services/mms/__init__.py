import dataclasses
import typing as t

import phonenumbers

from .. import Attachment, Message, MessageBuilder, Service, ServiceManager


@dataclasses.dataclass
class MMSMessage(Message):
    """A representation of a MMS multimedia message.

    :param to: The recipient number.
    :param body: The text message body.
    :param from_: The sender number.
    :param attachments: A list of :class:`owlery.services.Attachment` objects.
    :param id: The message unique identifier.
    :param reply_id: The message identifier this message is replied to.
    :param raw: The raw data response from service.
    :param service: Service to use for sending, replies and fowarding.

    """

    to: t.Optional[str] = None
    body: t.Optional[str] = None
    from_: t.Optional[str] = None
    attachments: t.List[Attachment] = dataclasses.field(default_factory=list)

    def attach(
        self,
        data: t.Union[bytes, t.IO[bytes]],
        mimetype: str = "application/octet-stream",
    ):
        attachment = Attachment(data, mimetype)
        self.attachments.append(attachment)

    @classmethod
    def builder(self):
        return MMSMessageBuilder()

    def forward(self, to: str, service=None, **kwargs):
        if not service:
            service = self.service
        if not service or not service.can_send:
            raise ValueError("No service to foward this message")

        return service.send(
            to=to,
            body=self.body,
            attachments=self.attachments,
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


class MMSMessageBuilder(MessageBuilder):
    """Build a MMS multimedia message."""

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

    def to(self, to: str):
        return self._replace(to=to)


class MMS(Service):
    """Base class for an MMS multimedia messaging service."""

    name = "mms"

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
        """Receive MMS multimedia messages.

        :param limit: Limit number of messages received, defaults to ``100``.

        """
        ...

    def send(
        self,
        to: str,
        body: str,
        from_: t.Optional[str] = None,
        attachments: t.Optional[t.List[Attachment]] = None,
        **kwargs,
    ):
        """Send a MMS multimedia message.

        :param to: The message receipient number.
        :param body: Text body of the message.
        :param from_: The message sender number.
        :param attachments: A list of attachments i.e. images, videos.

        """
        ...

    def send_message(self, message):
        """Send a MMS multimedia message from a message object.

        :param message: A :class:`MMSMessage` message object.

        """
        return message.send(service=self)


class MMSManager(MMS, ServiceManager):
    """Service manager for MMS multimedia messaging services."""

    def register(self, service_cls, **kwargs):
        kwargs.setdefault("region", self.region)
        return super().register(service_cls, **kwargs)
