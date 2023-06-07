import imaplib
import secrets
import time

import pytest

from owlery.exceptions import ServiceAuthFailed
from owlery.services.email import EmailMessage
from owlery.services.email.pop3 import POP3


@pytest.fixture()
def message():
    message = EmailMessage(
        to=["user"],
        subject=f"Test message {secrets.token_hex(8)}",
        body="This is a test message.",
        from_="test@example.com",
    )

    with imaplib.IMAP4(host="localhost", port=144) as imap:
        imap.login("user", "pass")

        imap.append(
            "INBOX",
            (),
            time.time(),
            message.as_bytes(),
        )

    return message


@pytest.fixture(scope="session")
def pop3():
    return POP3(host="localhost", port=110, user="user", password="pass")


@pytest.fixture
def manager_with_pop3(manager):
    return manager.register(
        POP3,
        host="localhost",
        port=110,
        user="user",
        password="pass",
    )


def test_init():
    POP3(host="localhost", port=110, user="user", password="pass")


@pytest.mark.integration
def test_connect(pop3):
    pop3.open()
    pop3.close()


@pytest.mark.integration
def test_connect_ssl():
    pop3 = POP3(
        host="localhost",
        port=995,
        ssl=True,
        user="user",
        password="pass",
    )

    pop3.open()
    pop3.close()


@pytest.mark.integration
def test_connect_starttls():
    pop3 = POP3(
        host="localhost",
        port=110,
        starttls=True,
        user="user",
        password="pass",
    )

    pop3.open()
    pop3.close()


@pytest.mark.integration
@pytest.mark.slow
def test_connect_wrong_credentials(pop3):
    pop3 = POP3(
        host="localhost",
        port=110,
        user="user",
        password="wrong",
        starttls=True,
    )

    with pytest.raises(ServiceAuthFailed):
        pop3.open()

    pop3.close()


def test_auto_port():
    pop3 = POP3()
    assert pop3.port == 110


def test_auto_port_ssl():
    pop3 = POP3(ssl=True)
    assert pop3.port == 995


def test_auto_port_starttls():
    pop3 = POP3(starttls=True)
    assert pop3.port == 110


def test_specified_port():
    pop3 = POP3(port=111)
    assert pop3.port == 111


@pytest.mark.integration
def test_receive(pop3, message):
    received_message = None
    for received_message in pop3.receive(limit=10):
        received_message = received_message
    pop3.close()
    assert received_message.subject == message.subject


@pytest.mark.integration
def test_receive_contextmanager(pop3, message):
    received_message = None
    with pop3:
        for received_message in pop3.receive(limit=10):
            received_message = received_message
    assert received_message.subject == message.subject


@pytest.mark.integration
def test_receive_with_manager(manager_with_pop3, message):
    received_message = None
    for received_message in manager_with_pop3.receive(limit=10):
        received_message = received_message
    manager_with_pop3.close()
    assert received_message.subject == message.subject


@pytest.mark.integration
def test_receive_with_manager_contextmanager(manager_with_pop3, message):
    received_message = None
    with manager_with_pop3:
        for received_message in manager_with_pop3.receive(limit=10):
            received_message = received_message
    assert received_message.subject == message.subject
