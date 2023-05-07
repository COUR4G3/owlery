import pytest

from owlery.exceptions import ServiceAuthFailed
from owlery.services.email.imap import IMAP


@pytest.fixture(scope="session")
def message():
    return {
        "body": "This is a test message",
        "from_": "test@example.com",
        "subject": "Test message",
        "to": ["test@example.com"],
    }


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
    for _ in imap.receive(limit=10):
        pass
    imap.close()


@pytest.mark.integration
def test_receive_contextmanager(imap, message):
    with imap:
        for _ in imap.receive(limit=10):
            pass


@pytest.mark.integration
def test_receive_with_manager(manager_with_imap, message):
    for _ in manager_with_imap.receive(limit=10):
        pass
    manager_with_imap.close()


@pytest.mark.integration
def test_receive_with_manager_contextmanager(manager_with_imap, message):
    with manager_with_imap:
        for _ in manager_with_imap.receive(limit=10):
            pass
