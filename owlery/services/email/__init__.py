import dataclasses
import typing as t

from collections import UserDict
from email import (
    message_from_binary_file,
    message_from_bytes,
    message_from_file,
    message_from_string,
)
from email.message import EmailMessage as PyEmailMessage
from email.utils import (
    format_datetime,
    make_msgid,
    parseaddr,
    parsedate_to_datetime,
)

from .. import USER_AGENT, Attachment, Message, Service, ServiceManager

try:
    import envelope
except ImportError:
    ENVELOPE_AVAILABLE = False
else:
    ENVELOPE_AVAILABLE = True

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
    :param encrypted: Email message is encrypted with GPG, PGP or S/MIME
    :param verified: Email message integrity has been verified.
    :param service: Service to use for sending, reply etc.

    """

    to: t.Optional[AddressesType] = None
    subject: t.Optional[str] = None
    body: t.Optional[str] = None
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
    encrypted: bool = False
    signed: bool = False
    verified: bool = False
    raw: t.Any = None
    service: t.Optional["Email"] = None

    def as_bytes(self):
        message = self.as_email_message()
        return message.as_bytes()

    def as_email_message(self):
        message = PyEmailMessage()

        if self.date:
            message["Date"] = format_datetime(self.date)

        if not self.id:
            self.id = make_msgid()
        message["Message-ID"] = self.id

        if self.from_:
            message["From"] = self.from_

        if self.to:
            message["To"] = self.to

        if self.cc:
            message["Cc"] = self.cc

        if self.reply_to:
            message["Reply-To"] = self.reply_to

        if self.subject:
            message["Subject"] = self.subject

        message.set_content(self.body, subtype="plain")

        if self.amp_html_body:
            message.add_alternative(self.amp_html_body, subtype="x-amp-html")

        if self.html_body:
            message.add_alternative(self.html_body, subtype="html")

        message["User-Agent"] = message["X-Mailer"] = USER_AGENT

        if self.headers:
            for name, value in self.headers.items():
                message[name] = value

        return message

    def as_string(self):
        message = self.as_email_message()
        return message.as_string()

    @classmethod
    def build(self, **kwargs):
        return EmailMessageBuilder(**kwargs)

    def _check_encrypted_and_signed(self):
        message = self.as_email_message()
        encrypted = signed = False
        for part in message.walk():
            if part.get_content_type() == "multipart/encrypted":
                encrypted = True
            elif part.get_content_type() == "multipart/signed":
                signed = True
        return encrypted, signed

    def decrypt(self):
        """Decrypt the message.

        Requires the `envelope` library to be installed.

        """
        if not ENVELOPE_AVAILABLE:
            raise RuntimeError("envelope library not available")

        message = self.as_email_message()

        env = envelope.Envelope.load(message)

        return self.from_email_message(env.as_message())

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

    @classmethod
    def from_binary_file(cls, fp: t.IO[bytes]):
        msg = message_from_binary_file(fp, PyEmailMessage)
        return cls.from_email_message(msg)  # type: ignore

    @classmethod
    def from_bytes(cls, s: bytes):
        msg = message_from_bytes(s, PyEmailMessage)
        return cls.from_email_message(msg)  # type: ignore

    @classmethod
    def from_email_message(cls, message: PyEmailMessage):
        to = [parseaddr(t.strip()) for t in message.get("To", "").split(",")]
        from_ = parseaddr(message.get("From", ""))
        subject = message.get("Subject", "")
        body = message.get_body(("plain",))
        html_body = message.get_body(("html",))
        cc = [parseaddr(c.strip()) for c in message.get("Cc", "").split(",")]
        reply_to = parseaddr(message.get("Reply-To", ""))
        date = message.get("Date", None)
        if date:
            date = parsedate_to_datetime(date)
        id = message.get("Message-ID")

        headers = {}
        for name, value in message.items():
            if name in (
                "From",
                "Subject",
                "To",
                "Cc",
                "Reply-To",
                "Date",
                "Message-ID",
            ):
                continue
            headers[name] = value

        headers = dict(message.items())

        return cls(
            to=to,
            subject=subject,
            body=body and body.get_payload() or "",
            html_body=html_body and html_body.get_payload() or None,
            cc=cc,
            reply_to=reply_to,
            from_=from_,
            headers=headers,
            date=date,
            id=id,
            raw=message,
        )

    @classmethod
    def from_file(cls, fp: t.IO[str]):
        msg = message_from_file(fp, PyEmailMessage)
        return cls.from_email_message(msg)  # type: ignore

    @classmethod
    def from_string(cls, s: str):
        msg = message_from_string(s, PyEmailMessage)
        return cls.from_email_message(msg)  # type: ignore

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

    def verify(self):
        """Verify the message integrity.

        Requires the `envelope` library to be installed.

        :returns: message integrity verification
        :rtype: bool

        """
        if not ENVELOPE_AVAILABLE:
            raise RuntimeError("envelope library not available")

        message = self.as_email_message()

        env = envelope.Envelope.load(message)

        sig = data = None
        for part in message.walk():
            if part.get_content_type() == "multipart/signed":
                for subpart in part.walk():
                    if (
                        subpart.get_content_type()
                        == "application/pgp-signature"
                    ):
                        sig = part.get_payload().encode()
                    else:
                        data = part.get_payload().encode()

        if sig and data:
            result = env._gpg_verify(sig, data)
            self.verified = result
            return result

        return False


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
        encrypt: bool = False,
        sign: bool = False,
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
                "encrypt": encrypt,
                "sign": sign,
            },
        )

    def amp_html_body(self, amp_html_body: t.Optional[str] = None):
        if not amp_html_body:
            return self.data["amp_html_body"]

        return self.replace(amp_html_body=amp_html_body)

    def as_message(self):
        return EmailMessage(**self.data)

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

    def encrypt(self):
        """Encrypt the message.

        Requires the `envelope` library to be installed.

        """
        if not ENVELOPE_AVAILABLE:
            raise RuntimeError("envelope library not available")

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

    def sign(self):
        """Sign the message.

        Requires the `envelope` library to be installed.

        """
        if not ENVELOPE_AVAILABLE:
            raise RuntimeError("envelope library not available")

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


class EmailManager(Email, ServiceManager):
    """Service manager for email messaging services."""
