import platform
import typing as t

from collections import UserList
from dataclasses import dataclass, field
from email import (
    message_from_binary_file,
    message_from_bytes,
    message_from_file,
    message_from_string,
)
from email.message import EmailMessage as _EmailMessage
from email.policy import SMTP, EmailPolicy
from email.utils import (
    format_datetime,
    formataddr,
    make_msgid,
    parseaddr,
    parsedate,
)

from ... import __version__
from .. import Attachment, Message, MessageBuilder, Service, ServiceManager

EMAIL_USER_AGENT = (
    f"owlery/{__version__} "
    f"{platform.python_implementation()}/{platform.python_version()}"
)


@dataclass
class EmailAttachment(Attachment):
    """A representation of an email attachment.

    :param data: The attachment data.
    :param mimetype: The mimetype, default `'application/octet-stream'`.
    :param filename: The filename, optional.
    :param cid: The Content-ID of the inline attachment, optional.
    :param inline: Whether this is an inline attachment or not.

    """

    filename: t.Optional[str] = None
    cid: t.Optional[str] = None
    inline: bool = False


@dataclass
class EmailRecipient:
    """A representation of an email recipient.

    :param email: The recipient's email address.
    :param name: The recipient's name, optional.

    """

    email: str
    name: t.Optional[str] = None

    def __eq__(self, other):
        if isinstance(other, str):
            other = self.parse(other)
        return super().__eq__(other)

    def __str__(self):
        return formataddr((self.name, self.email))

    @classmethod
    def parse(cls, s):
        name, email = parseaddr(s)
        return cls(name=name, email=email)


EmailRecipientType = t.Union[EmailRecipient, str]
EmailRecipientsType = t.Iterable[t.Union[EmailRecipient, str]]


class EmailRecipients(UserList):
    """A list of email recipients."""

    def __init__(self, initlist: t.Optional[EmailRecipientsType] = None):
        if initlist:
            initlist = (
                isinstance(s, str) and EmailRecipient.parse(s) or s
                for s in initlist
            )

        super().__init__(initlist)

    def append(self, item: EmailRecipientType):
        if isinstance(item, str):
            item = EmailRecipient.parse(item)
        super().append(item)

    def extend(self, other: EmailRecipientsType):
        other = (
            isinstance(s, str) and EmailRecipient.parse(s) or s for s in other
        )

        super().extend(other)

    @classmethod
    def parse(cls, s: str):
        """Parse an email recipient from string."""
        return cls(EmailRecipient.parse(t) for t in s.split(","))


@dataclass
class EmailMessage(Message):
    r"""A representation of an email message.

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

    to: t.Optional[EmailRecipientsType] = None
    subject: t.Optional[str] = None
    body: t.Optional[str] = None
    html_body: t.Optional[str] = None
    amp_html_body: t.Optional[str] = None
    attachments: t.List[EmailAttachment] = field(default_factory=list)
    cc: t.Optional[EmailRecipientsType] = None
    bcc: t.Optional[EmailRecipientsType] = None
    from_: t.Optional[EmailRecipientType] = None
    reply_to: t.Optional[EmailRecipientType] = None
    headers: t.Dict[str, str] = field(default_factory=dict)
    user_agent: str = EMAIL_USER_AGENT
    id: t.Optional[t.Any] = field(default_factory=make_msgid)

    _to: EmailRecipientsType = field(init=False, repr=False)
    _cc: EmailRecipientsType = field(init=False, repr=False)
    _bcc: EmailRecipientsType = field(init=False, repr=False)

    def as_bytes(self, policy: t.Optional[EmailPolicy] = None):
        """Return the email message as a bytes."""
        message = self.as_email_message(policy=policy)
        return message.as_bytes(policy=policy)

    def as_dict(self):
        res = super().as_dict()

        res.pop("_to")
        res.pop("_cc")
        res.pop("_bcc")

        return res

    def as_email_message(self, policy: t.Optional[EmailPolicy] = None):
        """Return the email message as a :class:`EmailMessage` object."""
        message = _EmailMessage(policy=policy)

        message["Message-ID"] = self.id
        message["Date"] = format_datetime(self.date)
        message["To"] = str(self.to)
        message["Subject"] = self.subject

        if self.bcc:
            message["Bcc"] = str(self.bcc)
        if self.cc:
            message["Cc"] = str(self.cc)
        if self.from_:
            message["From"] = str(self.from_)
        if self.reply_to:
            message["Reply-To"] = str(self.reply_to)

        message.set_content(self.body, subtype="plain")

        if self.amp_html_body:
            message.add_alternative(self.amp_html_body, subtype="x-amp-html")
        if self.html_body:
            message.add_alternative(self.html_body, subtype="html")

        for name, value in self.headers.items():
            message[name] = value

        if self.user_agent:
            message["User-Agent"] = message["X-Mailer"] = self.user_agent

        return message

    def as_string(self, policy: t.Optional[EmailPolicy] = None):
        """Return the email message as a string."""
        message = self.as_email_message(policy=policy)
        return message.as_string(policy=policy)

    def attach(
        self,
        data: t.Union[bytes, t.IO[bytes]],
        mimetype: str = "application/octet-stream",
        filename: t.Optional[str] = None,
        cid: t.Optional[str] = None,
        inline: bool = False,
    ):
        """Attach a file to the email message.

        :param data: The attachment data.
        :param mimetype: The mimetype, default `'application/octet-stream'`.
        :param filename: The filename, optional.
        :param cid: The Content-ID of the inline attachment, optional.
        :param inline: Whether this is an inline attachment or not.

        """
        attachment = EmailAttachment(
            data=data,
            mimetype=mimetype,
            filename=filename,
            cid=cid,
            inline=inline,
        )
        self.attachments.append(attachment)
        return attachment

    @property  # type: ignore[no-redef]
    def bcc(self):
        return self._bcc

    @bcc.setter
    def bcc(self, value):
        if type(value) is property:
            value = EmailRecipients()
        self._bcc = value

    @property  # type: ignore[no-redef]
    def cc(self):
        return self._cc

    @cc.setter
    def cc(self, value):
        if type(value) is property:
            value = EmailRecipients()
        self._cc = value

    @classmethod
    def from_binary_file(cls, fp: t.IO[bytes], policy: EmailPolicy = SMTP):
        """Parse an email message from a binary file."""
        message = message_from_binary_file(
            fp,
            _class=_EmailMessage,
            policy=policy,
        )
        return cls.from_email_message(message)  # type: ignore

    @classmethod
    def from_bytes(cls, s: bytes, policy: EmailPolicy = SMTP):
        """Parse an email message from bytes."""
        message = message_from_bytes(s, _class=_EmailMessage, policy=policy)
        return cls.from_email_message(message)  # type: ignore

    @classmethod
    def from_file(cls, fp: t.IO[str], policy: EmailPolicy = SMTP):
        """Parse an email message from a file."""
        message = message_from_file(fp, _class=_EmailMessage, policy=policy)
        return cls.from_email_message(message)  # type: ignore

    @classmethod
    def from_email_message(cls, message: _EmailMessage):
        """Parse an email message from an :class:`EmailMessage` object."""
        headers = dict(message.items())

        to = EmailRecipients.parse(headers.pop("To", ""))
        cc = EmailRecipients.parse(headers.pop("Cc", ""))
        bcc = EmailRecipients.parse(headers.pop("Bcc", ""))

        from_ = headers.pop("From", None)
        if from_:
            from_ = EmailRecipient.parse(from_)

        reply_to = headers.pop("Reply-To", None)
        if reply_to:
            reply_to = EmailRecipient.parse(reply_to)

        id = headers.pop("Message-ID", None)

        date = headers.pop("Date", None)
        if date:
            date = parsedate(date)

        subject = headers.pop("Subject", None)

        body = message.get_body(preferencelist=("plain",))
        if body:
            body = body.get_payload()

        amp_html_body = message.get_body(preferencelist=("x-amp-html",))
        if amp_html_body:
            amp_html_body = amp_html_body.get_payload()

        html_body = message.get_body(preferencelist=("html",))
        if html_body:
            html_body = html_body.get_payload()

        attachments = []
        for part in message.iter_attachments():
            attachment = EmailAttachment(
                data=part.get_payload(),
                mimetype=part.get_content_type(),
                filename=part.get_filename(),
                cid=part.get("Content-ID", None),
                inline=part.get_content_disposition() == "inline",
            )

            attachments.append(attachment)

        return cls(
            to=to,
            subject=subject,
            body=body,  # type: ignore
            html_body=html_body,  # type: ignore
            attachments=attachments,
            cc=cc,
            bcc=bcc,
            from_=from_,
            reply_to=reply_to,
            id=id,
            date=date,
            headers=headers,
        )

    @classmethod
    def from_string(cls, s: str):
        """Parse an email message from a string."""
        message = message_from_string(s, _class=_EmailMessage)
        return cls.as_email_message(message)  # type: ignore

    @property  # type: ignore[no-redef]
    def to(self):
        return self._to

    @to.setter
    def to(self, value):
        if type(value) is property:
            value = EmailRecipients()
        self._to = value


class EmailMessageBuilder(MessageBuilder):
    r"""A fluent builder for email messages.

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

    Message = EmailMessage

    def __init__(
        self,
        to: t.Optional[EmailRecipientsType] = None,
        subject: t.Optional[str] = None,
        body: t.Optional[str] = None,
        html_body: t.Optional[str] = None,
        amp_html_body: t.Optional[str] = None,
        attachments: t.Optional[t.List[EmailAttachment]] = None,
        cc: t.Optional[EmailRecipientsType] = None,
        bcc: t.Optional[EmailRecipientsType] = None,
        from_: t.Optional[EmailRecipientType] = None,
        reply_to: t.Optional[EmailRecipientType] = None,
        headers: t.Optional[t.Dict[str, str]] = None,
    ):
        data = {
            "to": to,
            "subject": subject,
            "body": body,
            "html_body": html_body,
            "amp_html_body": amp_html_body,
            "attachments": attachments,
            "cc": cc,
            "bcc": bcc,
            "from_": from_,
            "reply_to": reply_to,
            "headers": headers,
        }

        super().__init__(data)

    def as_bytes(self):
        """Return the email message as a bytes."""
        message = self.as_email_message()
        return message.as_bytes()

    def as_email_message(self):
        """Return the email message as a :class:`EmailMessage` object."""
        message = _EmailMessage()

        return message

    def as_string(self):
        """Return the email message as a string."""
        message = self.as_email_message()
        return message.as_string()

    def attach(
        self,
        data: t.Union[bytes, t.IO[bytes]],
        mimetype: str = "application/octet-stream",
        filename: t.Optional[str] = None,
        cid: t.Optional[str] = None,
        inline: bool = False,
    ):
        """Attach a file to the email message.

        :param data: The attachment data.
        :param mimetype: The mimetype, default `'application/octet-stream'`.
        :param filename: The filename, optional.
        :param cid: The Content-ID of the inline attachment, optional.
        :param inline: Whether this is an inline attachment or not.

        """
        attachments = self["attachments"].copy()
        attachment = EmailAttachment(
            data=data,
            mimetype=mimetype,
            filename=filename,
            cid=cid,
            inline=inline,
        )
        attachments.append(attachment)

        return self._replace(attachments=attachments)

    def bcc(self, *recipients: EmailRecipientType):
        """Add one or more Blind Carbon-Copy recipients."""
        bcc = self["bcc"].copy()
        bcc.extend(recipients)

        return self._replace(bcc=bcc)

    def cc(self, *recipients: EmailRecipientType):
        """Add one or more Carbon-Copy recipients."""
        cc = self["cc"].copy()
        cc.extend(recipients)

        return self._replace(cc=cc)

    def from_(self, from_: EmailRecipientType):
        """Set the From contact of the email message."""
        return self._replace(from_=from_)

    def header(self, name: str, value: str):
        """Set an email header.

        :param name: The email header name.
        :param value: The email header value.

        """
        headers = self["headers"].copy()
        headers[name] = value

        return self._replace(headers=headers)

    def reply_to(self, recipient: EmailRecipientType):
        """Set the Reply-To header of the email message."""
        return self._replace(reply_to=recipient)

    def to(self, *recipients: EmailRecipientsType):
        """Add one or more primary recipients."""
        to = self["to"].copy()
        to.extend(recipients)

        return self._replace(to=to)

    def user_agent(self, user_agent: str):
        """Set the User Agent on the email message."""
        return self._replace(user_agent=user_agent)


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
        to: EmailRecipientsType,
        subject: str,
        body: str,
        html_body: t.Optional[str] = None,
        amp_html_body: t.Optional[str] = None,
        cc: t.Optional[EmailRecipientsType] = None,
        bcc: t.Optional[EmailRecipientsType] = None,
        reply_to: t.Optional[EmailRecipientType] = None,
        from_: t.Optional[EmailRecipientType] = None,
        attachments: t.Optional[t.Iterable[EmailAttachment]] = None,
        headers: t.Optional[t.Dict[str, str]] = None,
    ):
        r"""Send an email message.

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
