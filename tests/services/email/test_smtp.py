import socket

import pytest

from owlery.exceptions import ServiceAuthFailed
from owlery.services.email.smtp import SMTP


def check_smtp(host, port):
    try:
        sock = socket.create_connection((host, port), timeout=5.0)
        sock.recv(1)
    except (OSError, socket.timeout):
        return False
    else:
        sock.close()

    return True


@pytest.fixture(scope="session")
def smtp_service(docker_ip, docker_services):
    port = docker_services.port_for("smtp", 1025)

    docker_services.wait_until_responsive(
        timeout=30.0,
        pause=0.1,
        check=lambda: check_smtp(docker_ip, port),
    )

    return docker_ip, port


@pytest.fixture(scope="session")
def smtp(smtp_service):
    host, port = smtp_service
    return SMTP(host=host, port=port, user="test", password="test")


@pytest.fixture
def manager_with_smtp(manager, smtp_service):
    host, port = smtp_service
    return manager.register(
        SMTP,
        host=host,
        port=port,
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
def test_connect_ssl(docker_ip, docker_services):
    port = docker_services.port_for("imap", 465)

    smtp = SMTP(
        host=docker_ip,
        port=port,
        ssl=True,
        user="user",
        password="pass",
    )

    smtp.open()
    smtp.close()


@pytest.mark.integration
def test_connect_starttls(docker_ip, docker_services):
    port = docker_services.port_for("imap", 587)

    smtp = SMTP(
        host=docker_ip,
        port=port,
        starttls=True,
        user="user",
        password="pass",
    )

    smtp.open()
    smtp.close()


@pytest.mark.integration
def test_connect_auth(docker_ip, docker_services):
    port = docker_services.port_for("imap", 587)
    smtp = SMTP(host=docker_ip, port=port, user="user", password="pass")

    smtp.open()
    smtp.close()


@pytest.mark.integration
def test_connect_wrong_credentials(docker_ip, docker_services):
    port = docker_services.port_for("imap", 587)
    smtp = SMTP(host=docker_ip, port=port, user="user", password="wrong")

    with pytest.raises(ServiceAuthFailed):
        smtp.open()
    smtp.close()


@pytest.mark.integration
def test_send(smtp, message):
    smtp.send_message(message)
    smtp.close()


@pytest.mark.integration
def test_send_contextmanager(smtp, message):
    with smtp:
        smtp.send_message(message)


@pytest.mark.integration
def test_send_with_manager(manager_with_smtp, message):
    manager_with_smtp.send_message(message)
    manager_with_smtp.close()


@pytest.mark.integration
def test_send_with_manager_contextmanager(manager_with_smtp, message):
    with manager_with_smtp:
        manager_with_smtp.send_message(message)
