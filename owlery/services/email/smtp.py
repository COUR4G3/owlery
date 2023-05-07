import smtplib
import typing as t

from ...exceptions import ServiceConnectError, ServiceTimeoutError
from . import Email

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

        super().__init__(**kwargs)

    def close(self):
        self.session.quit()

    def open(self):
        try:
            self.session.connect(self.host, self.port)
        except TimeoutError as e:
            raise ServiceTimeoutError(e)
        except ConnectionError as e:
            raise ServiceConnectError(e)

        if self.starttls:
            self.session.starttls(context=self.ssl_context)

        if self.user:
            self.session.login(self.user, self.password or "")

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
        message = self.Message(**kwargs).format_message()
        return self.session.send_message(message)
