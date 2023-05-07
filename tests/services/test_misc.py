import logging

import pytest

from owlery.services import ServiceManager
from owlery.services.misc import Logger, Null, ReceiveFunction, SendFunction

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@pytest.fixture
def manager():
    return ServiceManager()


def test_logger(caplog):
    service = Logger(logger.name)
    service.send(foo="bar")

    assert caplog.records[0].levelno == service.level
    assert caplog.records[0].msg == service.message
    assert caplog.records[0].foo == "bar"


def test_null(mocker):
    service = Null()

    spy = mocker.spy(service, "send")

    service.send(foo="bar")

    assert spy.call_count == 1
    assert spy.spy_return is None


def test_null_with_manager(manager, mocker):
    manager.register(Null)

    spy = mocker.spy(manager, "send")

    manager.send(foo="bar")

    assert spy.call_count == 1
    assert spy.spy_return is None


def test_receive_function(mocker):
    stub = mocker.stub(name="receive_function")

    limit = 10

    service = ReceiveFunction(stub)
    for _ in service.receive(limit=limit):
        pass

    stub.assert_called_once_with(limit=limit)


def test_send_function(mocker):
    stub = mocker.stub(name="send_function")

    service = SendFunction(stub)
    service.send(foo="bar")

    stub.assert_called_once_with(foo="bar")
