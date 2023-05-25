import pytest

from owlery.exceptions import ServiceAuthFailed
from owlery.services.email.smtp import SMTP


@pytest.fixture(scope="session")
def message():
    return {
        "body": "This is a test message",
        "from_": "test@example.com",
        "subject": "Test message",
        "to": ["test@example.com"],
    }


@pytest.fixture(scope="session")
def smtp():
    return SMTP(host="localhost", port=25, user="test", password="test")


@pytest.fixture
def manager_with_smtp(manager):
    return manager.register(
        SMTP,
        host="localhost",
        user="test",
        password="test",
    )


def test_init():
    SMTP()


def test_auto_port():
    smtp = SMTP()
    assert smtp.port == 25


def test_auto_port_ssl():
    smtp = SMTP(ssl=True)
    assert smtp.port == 465


def test_auto_port_starttls():
    smtp = SMTP(starttls=True)
    assert smtp.port == 587


def test_specified_port():
    smtp = SMTP(port=26)
    assert smtp.port == 26


@pytest.mark.integration
def test_connect(smtp):
    smtp.open()
    smtp.close()


@pytest.mark.integration
def test_connect_ssl():
    smtp = SMTP(
        host="localhost",
        port=465,
        ssl=True,
        user="user",
        password="pass",
    )

    smtp.open()
    smtp.close()


@pytest.mark.integration
def test_connect_starttls():
    smtp = SMTP(
        host="localhost",
        port=587,
        starttls=True,
        user="user",
        password="pass",
    )

    smtp.open()
    smtp.close()


@pytest.mark.integration
def test_connect_auth():
    smtp = SMTP(host="localhost", port=587, user="user", password="pass")

    smtp.open()
    smtp.close()


@pytest.mark.integration
def test_connect_wrong_credentials():
    smtp = SMTP(host="localhost", port=587, user="wrong", password="wrong")

    with pytest.raises(ServiceAuthFailed):
        smtp.open()
    smtp.close()


@pytest.mark.integration
def test_send(smtp, message):
    smtp.send(**message)
    smtp.close()


@pytest.mark.integration
def test_send_contextmanager(smtp, message):
    with smtp:
        smtp.send(**message)


@pytest.mark.integration
def test_send_with_manager(manager_with_smtp, message):
    manager_with_smtp.send(**message)
    manager_with_smtp.close()


@pytest.mark.integration
def test_send_with_manager_contextmanager(manager_with_smtp, message):
    with manager_with_smtp:
        manager_with_smtp.send(**message)
