import smtplib
import typing as t

from ...exceptions import ServiceAuthFailed, ServiceConnectError
from . import Email, EmailMessage

if t.TYPE_CHECKING:
    import ssl


class SMTP(Email):
    """Service to send email messages from an SMTP server.

    :param host: Hostname of the server, defaults to ``'localhost'``.
    :param port: Port of the server.
    :param user: Username to login.
    :param password: Password to login.
    :param starttls: Use STARTTLS encryption.
    :param ssl: Use SSL encryption.
    :param ssl_context: SSL context, see :class:`ssl.SSLContext`.

    """

    name = "smtp"

    can_send = True

    def __init__(
        self,
        host: str = "localhost",
        port: t.Optional[int] = None,
        user: t.Optional[str] = None,
        password: t.Optional[str] = None,
        starttls: bool = False,
        ssl: bool = False,
        ssl_context: t.Optional["ssl.SSLContext"] = None,
        **kwargs,
    ):
        self.host = host
        self._port = port
        self.user = user
        self.password = password
        self.starttls = starttls
        self.ssl = ssl
        self.ssl_context = ssl_context

        self.session: t.Union[smtplib.SMTP, smtplib.SMTP_SSL]
        if ssl:
            self.session = smtplib.SMTP_SSL(context=ssl_context)
        else:
            self.session = smtplib.SMTP()

        # this is required for ssl support
        self.session._host = host  # type: ignore

        super().__init__(**kwargs)

    def close(self):
        self.session.quit()

    def open(self):
        try:
            self.session.connect(self.host, self.port)
        except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected) as e:
            raise ServiceConnectError(e)

        if self.starttls:
            self.session.starttls(context=self.ssl_context)

        if self.user:
            try:
                self.session.login(self.user, self.password or "")
            except smtplib.SMTPAuthenticationError as e:
                raise ServiceAuthFailed(e)

    @property
    def port(self) -> int:
        port = self._port
        if not port:
            if self.starttls:
                port = 587
            elif self.ssl:
                port = 465
            else:
                port = 25

        return port

    def send(self, **kwargs):
        message = EmailMessage(**kwargs)

        try:
            self.session.send_message(message.as_email_message())
        except smtplib.SMTPException as e:
            message.exc = e
            message.status = "error"
        else:
            message.status = "sent"

        return message
