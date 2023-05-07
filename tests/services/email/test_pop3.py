import pytest

from owlery.exceptions import ServiceAuthFailed
from owlery.services.email.pop3 import POP3


@pytest.fixture(scope="session")
def message():
    return {
        "body": "This is a test message",
        "from_": "test@example.com",
        "subject": "Test message",
        "to": ["test@example.com"],
    }


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
    for _ in pop3.receive(limit=10):
        pass
    pop3.close()


@pytest.mark.integration
def test_receive_contextmanager(pop3, message):
    with pop3:
        for _ in pop3.receive(limit=10):
            pass


@pytest.mark.integration
def test_receive_with_manager(manager_with_pop3, message):
    for _ in manager_with_pop3.receive(limit=10):
        pass
    manager_with_pop3.close()


@pytest.mark.integration
def test_receive_with_manager_contextmanager(manager_with_pop3, message):
    with manager_with_pop3:
        for _ in manager_with_pop3.receive(limit=10):
            pass
