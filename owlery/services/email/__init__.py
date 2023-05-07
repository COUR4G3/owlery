import dataclasses
import datetime as dt
import typing as t

from collections import UserDict
from email.message import EmailMessage as PyEmailMessage
from email.utils import format_datetime, make_msgid

from .. import USER_AGENT, Attachment, Message, Service, ServiceManager

AddressType = t.Union[str, t.Tuple[t.Optional[str], str]]
AddressesType = t.Iterable[AddressType]


@dataclasses.dataclass
class EmailAttachment(Attachment):
    """A representation of an email attachment.

    :param data: Bytes or file-like object contain attachment data.
    :param filename: Filename of the attachment.
    :param mimetype: Mimetype of the attachment, defaults to
                     ``'application/octet-stream'``.

    """

    filename: t.Optional[str] = None


@dataclasses.dataclass
class EmailMessage(Message):
    """A representation for a received email message.

    :param to: A list of recipient addresses.
    :param subject: The email subject.
    :param body: The text body of the email.
    :param html_body: The HTML body of the email.
    :param amp_html_body: The body of the email in AMP HTML
                          (https://amp.dev/about/email)
    :param cc: A list of carbon-copy recipients.
    :param bcc: A list of blind carbon-copy recipients.
    :param reply_to: An optional address to send replies to.
    :param from\\_: The from address of the email message.
    :param attachments: A list of attachments.
    :param headers: A list of additional messages headers.
    :param service: Service to use for sending, reply etc.

    """

    to: AddressesType
    subject: str
    body: str
    html_body: t.Optional[str] = None
    amp_html_body: t.Optional[str] = None
    cc: AddressesType = dataclasses.field(default_factory=list)
    bcc: AddressesType = dataclasses.field(default_factory=list)
    reply_to: t.Optional[AddressType] = None
    from_: t.Optional[AddressType] = None
    attachments: t.List[EmailAttachment] = dataclasses.field(
        default_factory=list,
    )
    headers: t.Dict[str, str] = dataclasses.field(default_factory=dict)
    service: t.Optional["Email"] = None

    @classmethod
    def build(self, **kwargs):
        return EmailMessageBuilder(**kwargs)

    def forward(
        self,
        to: AddressesType,
        quote: bool = True,
        service: t.Optional["Email"] = None,
        **kwargs,
    ):
        r"""Forward this message.

        :param to: A list of recipients.
        :param quote: Quote the original message, defaults to ``True``.
        :param service: Optional service to use.
        :param \*\*kwargs: See the :class:`EmailMessage` object.

        """
        if not service:
            service = self.service
        if not service:
            return

        body = self.body

        service.send(to, body, attachments=self.attachments, **kwargs)

    def reply(
        self,
        quote: bool = True,
        service: t.Optional["Email"] = None,
        **kwargs,
    ):
        r"""Reply to this message.

        :param quote: Quote the original message, defaults to ``True``.
        :param service: Optional service to use.
        :param \*\*kwargs: See the :class:`EmailMessage` object.

        """
        if not service:
            service = self.service
        if not service:
            return

        body = self.body

        service.send(self.to, body, **kwargs)

    def reply_all(
        self,
        quote: bool = True,
        service: t.Optional["Email"] = None,
        **kwargs,
    ):
        r"""Reply to all recipients of this message.

        :param quote: Quote the original message, defaults to ``True``.
        :param service: Optional service to use.
        :param \*\*kwargs: See the :class:`EmailMessage` object.

        """
        if not service:
            service = self.service
        if not service:
            return

        body = self.body

        service.send(self.to, body, cc=self.cc, **kwargs)


class EmailMessageBuilder(UserDict):
    """A builder for email messages.

    :param to: A list of recipient addresses.
    :param subject: The email subject.
    :param body: The text body of the email.
    :param html_body: The HTML body of the email.
    :param amp_html_body: The body of the email in AMP HTML
                          (https://amp.dev/about/email)
    :param cc: A list of carbon-copy recipients.
    :param bcc: A list of blind carbon-copy recipients.
    :param reply_to: An optional address to send replies to.
    :param from\\_: The from address of the email message.
    :param attachments: A list of attachments.
    :param headers: A list of additional messages headers.
    :param service: Service to use for sending, reply etc.

    """

    def __init__(
        self,
        to: t.Optional[AddressesType] = None,
        subject: t.Optional[str] = None,
        body: t.Optional[str] = None,
        html_body: t.Optional[str] = None,
        amp_html_body: t.Optional[str] = None,
        cc: t.Optional[AddressesType] = None,
        bcc: t.Optional[AddressesType] = None,
        reply_to: t.Optional[AddressType] = None,
        from_: t.Optional[AddressType] = None,
        attachments: t.Optional[t.Iterable[EmailAttachment]] = None,
        headers: t.Optional[t.Dict[str, str]] = None,
        service: t.Optional["Email"] = None,
    ):
        self.service = service

        super().__init__(
            {
                "to": to,
                "subject": subject,
                "body": body,
                "cc": cc,
                "bcc": bcc,
                "headers": headers,
                "html_body": html_body,
                "amp_html_body": amp_html_body,
                "reply_to": reply_to,
                "from_": from_,
                "attachments": attachments,
            },
        )

    def amp_html_body(self, amp_html_body: t.Optional[str] = None):
        if not amp_html_body:
            return self.data["amp_html_body"]

        return self.replace(amp_html_body=amp_html_body)

    def attach(
        self,
        data: t.Union[bytes, t.IO[bytes]],
        filename: t.Optional[str] = None,
        mimetype: str = "application/octet-stream",
    ):
        """Attach a file to the message.

        :param data: Bytes or file-like object contain attachment data.
        :param filename: Filename of the attachment.
        :param mimetype: Mimetype of the attachment, defaults to
                         ``'application/octet-stream'``.

        """
        attachment = EmailAttachment(
            data,
            filename=filename,
            mimetype=mimetype,
        )

        attachments = self.attachments.copy()
        attachments.append(attachment)

        return self.replace(attachments=attachments)

    @property
    def attachments(self):
        """List of email attachments."""
        return self.data["attachments"]

    def bcc(self, bcc: t.Optional[AddressesType] = None):
        if not bcc:
            return self.data["bcc"]

        return self.replace(bcc=bcc)

    def body(self, body: t.Optional[str] = None):
        if not body:
            return self.data["body"]

        return self.replace(body=body)

    def cc(self, cc: t.Optional[AddressesType] = None):
        if not cc:
            return self.data["cc"]

        return self.replace(cc=cc)

    def from_(self, from_: t.Optional[AddressType] = None):
        if not from_:
            return self.data["from_"]

        return self.replace(from_=from_)

    def format_message(self) -> PyEmailMessage:
        message = PyEmailMessage()

        date = self.get("date")
        if not date:
            date = dt.datetime.now()
        message["Date"] = format_datetime(date)

        message["Message-ID"] = self.get("id", make_msgid())

        from_ = self.get("from_")
        if from_:
            message["From"] = from_

        to = self.get("to")
        if to:
            message["To"] = to

        cc = self.get("cc")
        if cc:
            message["Cc"] = cc

        reply_to = self.get("reply_to")
        if reply_to:
            message["Reply-To"] = reply_to

        subject = self.get("subject")
        if subject:
            message["Subject"] = subject

        message.set_content(self["body"], subtype="plain")

        amp_html_body = self.get("amp_html_body")
        if amp_html_body:
            message.add_alternative(amp_html_body, subtype="x-amp-html")

        html_body = self.get("html_body")
        if html_body:
            message.add_alternative(html_body, subtype="html")

        message["User-Agent"] = message["X-Mailer"] = USER_AGENT

        headers = self.get("headers")
        if headers:
            for name, value in headers.items():
                message[name] = value

        return message

    def html_body(self, html_body: t.Optional[str] = None):
        if not html_body:
            return self.data["html_body"]

        return self.replace(html_body=html_body)

    def replace(self, **kwargs):
        data = self.data.copy()
        data.update(kwargs)

        return self.__class__(**data)

    def reply_to(self, reply_to: t.Optional[AddressesType] = None):
        if not reply_to:
            return self.data["reply_to"]

        return self.replace(reply_to=reply_to)

    def send(self):
        """Send the email message."""
        if not self.service:
            raise NotImplementedError()
        return self.service.send_message(self.format_message())

    def subject(self, subject: t.Optional[str] = None):
        if not subject:
            return self.data["subject"]

        return self.replace(subject=subject)

    def to(self, to: t.Optional[AddressesType] = None):
        if not to:
            return self.data["to"]

        return self.replace(to=to)


class Email(Service):
    """Base class for an email messaging service."""

    name = "email"

    def Message(self, **kwargs):
        """Build a message."""
        return EmailMessageBuilder(service=self, **kwargs)

    def receive(  # type: ignore[empty-body]
        self,
        limit: int = 100,
        **kwargs,
    ) -> t.Generator[EmailMessage, None, None]:
        """Receive email messages.

        :param limit: Limit number of messages fetched.

        :raises ServiceReceiveCapabilityError: Receiving not supported.

        :return: A generator of received email messages.

        """
        ...

    def send(
        self,
        to: AddressesType,
        subject: str,
        body: str,
        html_body: t.Optional[str] = None,
        amp_html_body: t.Optional[str] = None,
        cc: t.Optional[AddressesType] = None,
        bcc: t.Optional[AddressesType] = None,
        reply_to: t.Optional[AddressType] = None,
        from_: t.Optional[AddressType] = None,
        attachments: t.Optional[t.Iterable[EmailAttachment]] = None,
        headers: t.Optional[t.Dict[str, str]] = None,
    ):
        """Send an email message.

        :param to: A list of recipient addresses.
        :param subject: The email subject.
        :param body: The text body of the email.
        :param html_body: The HTML body of the email.
        :param amp_html_body: The body of the email in AMP HTML
                              (https://amp.dev/about/email)
        :param cc: A list of carbon-copy recipients.
        :param bcc: A list of blind carbon-copy recipients.
        :param reply_to: An optional address to send replies to.
        :param from\\_: The from address of the email message.
        :param attachments: A list of attachments.
        :param headers: A list of additional messages headers.

        """
        ...

    def send_message(self, message: EmailMessage):
        """Send an email message from :class:`EmailMessage`."""
        return self.send(**dataclasses.asdict(message))


class EmailManager(Email, ServiceManager):
    """Service manager for email messaging services."""
