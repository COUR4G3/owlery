import dataclasses
import typing as t

import phonenumbers

from .. import Message, Service, ServiceManager


@dataclasses.dataclass
class SMSMessage(Message):
    """A representation of an SMS text message.

    :param to: The recipient number.
    :param body: The text message body.
    :param from_: The sender number.
    :param id: The message unique identifier.
    :param reply_id: The message identifier this message is replied to.
    :param raw: The raw data response from service.
    :param service: Service to use for sending, replies and fowarding.

    """

    to: t.Optional[str] = None
    body: t.Optional[str] = None
    from_: t.Optional[str] = None

    def forward(self, to: str, service=None, **kwargs):
        if not service:
            service = self.service
        if not service or not service.can_send:
            raise ValueError("No service to foward this message")

        return service.send(
            to=to,
            body=self.body,
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


class SMS(Service):
    """Base class for an SMS messaging service."""

    name = "sms"

    def __init__(
        self,
        region: t.Optional[str] = None,
        number_format: int = phonenumbers.PhoneNumberFormat.E164,
        sender_id: t.Optional[str] = None,
        **kwargs,
    ):
        self.region = region
        self.number_format = number_format
        self.sender_id = sender_id

        super().__init__(**kwargs)

    def format_number(self, number):
        number = phonenumbers.parse(number, self.region)
        number = phonenumbers.format_number(number, self.number_format)

        return number

    def receive(self, limit: int = 100, **kwargs):
        """Receive SMS text messages.

        :param limit: Limit number of messages received, defaults to ``100``.

        """
        ...

    def send(
        self,
        to: str,
        body: str,
        from_: t.Optional[str] = None,
        **kwargs,
    ):
        """Send an SMS text message.

        :param to: The message receipient number.
        :param body: Text body of the message.
        :param from_: The message sender number.

        """
        ...

    def send_otp(
        self,
        to: str,
        body: str,
        code: str,
        domain: str,
        app_hash: t.Optional[str] = None,
        embedded_host: t.Optional[str] = None,
        **kwargs,
    ):
        r"""Send a One-Time Password (OTP) over SMS text message.

        :param to: The message receipient number.
        :param body: Formatting string representing the message body, with an
            optional ``'{code}'`` to include the One-Time Password ``code``.
        :param code: The One-Time Password (OTP) token.
        :param domain: The root domain of the application/website.
        :param app_hash: The optional Android app hash.
        :param embedded_host: The optional embedded host of the app.
        :param \*\*kwargs: See :method:`SMS.send` for more parameters.

        """
        body = body.format(code=code).rstrip()
        body += f"\n\n@{domain} #{code}"
        if app_hash:
            body += f" ^{app_hash}"
        if embedded_host:
            body += f" @{embedded_host}"

        return self.send(to, body, **kwargs)


class SMSManager(SMS, ServiceManager):
    """Service manager for SMS text messaging services."""

    def register(self, service_cls, **kwargs):
        kwargs.setdefault("region", self.region)
        return super().register(service_cls, **kwargs)
