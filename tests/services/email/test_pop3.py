import imaplib
import socket
import time

import pytest

from owlery.exceptions import ServiceAuthFailed
from owlery.services.email.pop3 import POP3


def check_pop3(host, port):
    try:
        sock = socket.create_connection((host, port), timeout=5.0)
        sock.send(b"\0")
        sock.recv(1)
    except (OSError, socket.timeout):
        return False
    else:
        sock.close()

    return True


@pytest.fixture(scope="session")
def pop3_service(docker_ip, docker_services):
    port = docker_services.port_for("pop3", 110)

    docker_services.wait_until_responsive(
        timeout=30.0,
        pause=0.1,
        check=lambda: check_pop3(docker_ip, port),
    )

    return docker_ip, port


@pytest.fixture()
def pop3_message(docker_services, pop3_service, message):
    host = pop3_service[0]
    port = docker_services.port_for("pop3", 143)

    with imaplib.IMAP4(host=host, port=port) as imap:
        imap.login("user", "pass")

        imap.append(
            "INBOX",
            (),
            time.time(),
            message.as_bytes(),
        )

    time.sleep(5.0)

    return message


@pytest.fixture(scope="session")
def pop3(pop3_service):
    host, port = pop3_service
    return POP3(host=host, port=port, user="user", password="pass")


@pytest.fixture
def manager_with_pop3(manager, pop3_service):
    host, port = pop3_service
    return manager.register(
        POP3,
        host=host,
        port=port,
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
def test_connect_ssl(docker_services, pop3_service):
    host = pop3_service[0]
    port = docker_services.port_for("pop3", 995)

    pop3 = POP3(
        host=host,
        port=port,
        ssl=True,
        user="user",
        password="pass",
    )

    pop3.open()
    pop3.close()


@pytest.mark.integration
def test_connect_starttls(pop3_service):
    host, port = pop3_service
    pop3 = POP3(
        host=host,
        port=port,
        starttls=True,
        user="user",
        password="pass",
    )

    pop3.open()
    pop3.close()


@pytest.mark.integration
@pytest.mark.slow
def test_connect_wrong_credentials(pop3_service):
    host, port = pop3_service
    pop3 = POP3(
        host=host,
        port=port,
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
@pytest.mark.slow
@pytest.mark.xfail
def test_receive(pop3, pop3_message):
    received_message = None
    for received_message in pop3.receive(limit=10):
        received_message = received_message
    pop3.close()
    assert received_message.subject == pop3_message.subject


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.xfail
def test_receive_contextmanager(pop3, pop3_message):
    received_message = None
    with pop3:
        for received_message in pop3.receive(limit=10):
            received_message = received_message
    assert received_message.subject == pop3_message.subject


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.xfail
def test_receive_with_manager(manager_with_pop3, pop3_message):
    received_message = None
    for received_message in manager_with_pop3.receive(limit=10):
        received_message = received_message
    manager_with_pop3.close()
    assert received_message.subject == pop3_message.subject


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.xfail
def test_receive_with_manager_contextmanager(manager_with_pop3, pop3_message):
    received_message = None
    with manager_with_pop3:
        for received_message in manager_with_pop3.receive(limit=10):
            received_message = received_message
    assert received_message.subject == pop3_message.subject
