import imaplib
import time

from email.utils import make_msgid

import pytest

from owlery.exceptions import ServiceAuthFailed
from owlery.services.email import EmailMessage
from owlery.services.email.imap import IMAP


@pytest.fixture()
def message():
    message = EmailMessage(
        to=["user"],
        subject="Test message",
        body="This is a test message.",
        from_="test@example.com",
        id=make_msgid(),
    )

    with imaplib.IMAP4(host="localhost", port=143) as imap:
        imap.login("user", "pass")

        imap.append(
            "INBOX",
            (),
            time.time(),
            message.as_bytes(),
        )

    return message


@pytest.fixture(scope="session")
def imap():
    return IMAP(host="localhost", port=143, user="user", password="pass")


@pytest.fixture
def manager_with_imap(manager):
    return manager.register(
        IMAP,
        host="localhost",
        port=143,
        user="user",
        password="pass",
    )


def test_init():
    IMAP(host="localhost", port=143, user="user", password="pass")


@pytest.mark.integration
def test_connect():
    imap = IMAP(host="localhost", port=143, user="user", password="pass")

    imap.open()
    imap.close()


@pytest.mark.integration
def test_connect_ssl():
    imap = IMAP(
        host="localhost",
        port=993,
        ssl=True,
        user="user",
        password="pass",
    )

    imap.open()
    imap.close()


@pytest.mark.integration
def test_connect_starttls():
    imap = IMAP(
        host="localhost",
        port=143,
        starttls=True,
        user="user",
        password="pass",
    )

    imap.open()
    imap.close()


@pytest.mark.integration
@pytest.mark.slow
def test_connect_wrong_credentials():
    imap = IMAP(host="localhost", port=143, user="user", password="wrong")

    with pytest.raises(ServiceAuthFailed):
        imap.open()

    imap.close()


def test_auto_port():
    imap = IMAP()
    assert imap.port == 143


def test_auto_port_ssl():
    imap = IMAP(ssl=True)
    assert imap.port == 993


def test_auto_port_starttls():
    imap = IMAP(starttls=True)
    assert imap.port == 143


def test_specified_port():
    imap = IMAP(port=144)
    assert imap.port == 144


@pytest.mark.integration
def test_receive(imap, message):
    for received_message in imap.receive(limit=10):
        received_message = received_message
    imap.close()
    assert received_message.id == message.id


@pytest.mark.integration
def test_receive_contextmanager(imap, message):
    with imap:
        for received_message in imap.receive(limit=10):
            received_message = received_message
    assert received_message.id == message.id


@pytest.mark.integration
def test_receive_with_manager(manager_with_imap, message):
    for received_message in manager_with_imap.receive(limit=10):
        received_message = received_message
    manager_with_imap.close()
    assert received_message.id == message.id


@pytest.mark.integration
def test_receive_with_manager_contextmanager(manager_with_imap, message):
    with manager_with_imap:
        for received_message in manager_with_imap.receive(limit=10):
            received_message = received_message
    assert received_message.id == message.id
