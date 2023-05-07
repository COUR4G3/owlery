import poplib
import typing as t

from ...exceptions import (
    ServiceAuthFailed,
    ServiceConnectError,
    ServiceTimeoutError,
)
from . import Email

if t.TYPE_CHECKING:
    import ssl


class POP3(Email):
    """Service to receive email messages from an POP3 server mailbox.

    :param host: Hostname of the server, defaults to ``'localhost'``.
    :param port: Port of the server.
    :param user: Username to login.
    :param password: Password to login.
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

        super().__init__(**kwargs)

    def close(self):
        self.session.quit()

    def open(self):
        try:
            if self.ssl:
                self.session = poplib.POP3_SSL(
                    self.host,
                    self.port,
                    context=self.ssl_context,
                )
            else:
                self.session = poplib.POP3(self.host, self.port)
        except TimeoutError as e:
            raise ServiceTimeoutError(e)
        except ConnectionError as e:
            raise ServiceConnectError(e)

        if self.starttls:
            self.session.stls(context=self.ssl_context)

        try:
            self.session.user(self.user or "")
            self.session.pass_(self.password or "")
        except poplib.error_proto as e:
            if "[AUTH] Authentication failed" in str(e):
                raise ServiceAuthFailed()
            raise

    @property
    def port(self) -> int:
        port = self._port
        if not port:
            if self.ssl and not self.starttls:
                port = 995
            else:
                port = 110

        return port

    def receive(self, limit: int = 100, **kwargs):
        res, data, size = self.session.list()
        count = len(data)

        for i in range(1, min(count, limit) + 1):
            res, data, octets = self.session.retr(i)
            yield data
