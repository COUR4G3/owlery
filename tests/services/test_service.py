import pytest

from owlery.exceptions import (
    ServiceReceiveCapabilityError,
    ServiceSendCapabilityError,
)
from owlery.services import Service


def test_contextmanager():
    service = Service(suppress=True)
    with service:
        pass
    assert service.opened is False


def test_init():
    service = Service(suppress=True)
    service.open()
    service.close()


def test_suppress():
    service = Service(suppress=True)
    service.send()  # will raise if suppress doesn't work


def test_receive_not_capable():
    service = Service()
    with pytest.raises(ServiceReceiveCapabilityError):
        for _ in service.receive():
            pass


def test_send_not_capable():
    service = Service()
    with pytest.raises(ServiceSendCapabilityError):
        service.send()
