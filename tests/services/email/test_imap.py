import imaplib
import socket
import time

import pytest

from owlery.exceptions import ServiceAuthFailed
from owlery.services.email.imap import IMAP


def check_imap(host, port):
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
def imap_service(docker_ip, docker_services):
    port = docker_services.port_for("imap", 143)

    docker_services.wait_until_responsive(
        timeout=30.0,
        pause=0.1,
        check=lambda: check_imap(docker_ip, port),
    )

    return docker_ip, port


@pytest.fixture()
def imap_message(imap_service, message):
    host, port = imap_service

    with imaplib.IMAP4(host=host, port=port) as imap:
        imap.login("user", "pass")

        imap.append(
            "INBOX",
            (),
            time.time(),
            message.as_bytes(),
        )

    return message


@pytest.fixture(scope="session")
def imap(imap_service):
    host, port = imap_service
    return IMAP(host=host, port=port, user="user", password="pass")


@pytest.fixture
def manager_with_imap(imap_service, manager):
    host, port = imap_service
    return manager.register(
        IMAP,
        host=host,
        port=port,
        user="user",
        password="pass",
    )


def test_init():
    IMAP(host="localhost", port=143, user="user", password="pass")


@pytest.mark.integration
@pytest.mark.xfail
def test_connect(imap_service):
    host, port = imap_service
    imap = IMAP(host=host, port=port, user="user", password="pass")

    imap.open()
    imap.close()


@pytest.mark.integration
def test_connect_ssl(docker_ip, docker_services):
    port = docker_services.port_for("imap", 993)

    imap = IMAP(
        host=docker_ip,
        port=port,
        ssl=True,
        user="user",
        password="pass",
    )

    imap.open()
    imap.close()


@pytest.mark.integration
def test_connect_starttls(imap_service):
    host, port = imap_service

    imap = IMAP(
        host=host,
        port=port,
        starttls=True,
        user="user",
        password="pass",
    )

    imap.open()
    imap.close()


@pytest.mark.integration
@pytest.mark.slow
def test_connect_wrong_credentials(imap_service):
    host, port = imap_service
    imap = IMAP(host=host, port=port, user="user", password="wrong")

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
def test_receive(imap, imap_message):
    for received_message in imap.receive(limit=10):
        received_message = received_message
    imap.close()
    assert received_message.id == imap_message.id


@pytest.mark.integration
def test_receive_contextmanager(imap, imap_message):
    with imap:
        for received_message in imap.receive(limit=10):
            received_message = received_message
    assert received_message.id == imap_message.id


@pytest.mark.integration
def test_receive_with_manager(manager_with_imap, imap_message):
    for received_message in manager_with_imap.receive(limit=10):
        received_message = received_message
    manager_with_imap.close()
    assert received_message.id == imap_message.id


@pytest.mark.integration
def test_receive_with_manager_contextmanager(manager_with_imap, imap_message):
    with manager_with_imap:
        for received_message in manager_with_imap.receive(limit=10):
            received_message = received_message
    assert received_message.id == imap_message.id
