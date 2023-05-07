import imaplib
import typing as t

from ...exceptions import (
    ServiceAuthFailed,
    ServiceConnectError,
    ServiceTimeoutError,
)
from . import Email

if t.TYPE_CHECKING:
    import ssl


class IMAP(Email):
    """Service to receive email messages from an IMAP server mailbox.

    :param host: Hostname of the server, defaults to ``'localhost'``.
    :param port: Port of the server.
    :param user: Username to login.
    :param password: Password to login.
    :param folder: Folder to check for messages, defaults to ``'INBOX'``.
    :param starttls: Use STARTTLS encryption.
    :param ssl: Use SSL encryption.
    :param ssl_context: SSL context, see :class:`ssl.SSLContext`.

    """

    def __init__(
        self,
        host: str = "localhost",
        port: t.Optional[int] = None,
        user: t.Optional[str] = None,
        password: t.Optional[str] = None,
        folder: str = "INBOX",
        starttls: bool = False,
        ssl: bool = False,
        ssl_context: t.Optional["ssl.SSLContext"] = None,
        **kwargs,
    ):
        self.host = host
        self._port = port
        self.user = user
        self.password = password
        self.folder = folder
        self.starttls = starttls
        self.ssl = ssl
        self.ssl_context = ssl_context

        super().__init__(**kwargs)

    def close(self):
        self.session.shutdown()

    def open(self):
        try:
            if self.ssl:
                self.session = imaplib.IMAP4_SSL(
                    self.host,
                    self.port,
                    ssl_context=self.ssl_context,
                )
            else:
                self.session = imaplib.IMAP4(self.host, self.port)
        except TimeoutError as e:
            raise ServiceTimeoutError(e)
        except ConnectionError as e:
            raise ServiceConnectError(e)

        if self.starttls:
            self.session.starttls(ssl_context=self.ssl_context)

        try:
            self.session.login(self.user, self.password or "")
        except imaplib.IMAP4.error as e:
            if "[AUTHENTICATIONFAILED]" in str(e):
                raise ServiceAuthFailed()
            raise

    @property
    def port(self) -> int:
        port = self._port
        if not port:
            if self.ssl and not self.starttls:
                port = 993
            else:
                port = 143

        return port

    def receive(self, limit: int = 100, **kwargs):
        self.session.select(self.folder, readonly=True)

        res, data = self.session.search("UTF-8", "UNSEEN")
        for num in data[0].split():
            res, data = self.session.fetch(num, "(RFC822)")
            yield data[0][1]

        self.session.close()
