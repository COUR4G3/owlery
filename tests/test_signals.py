import pytest

from owlery import signals
from owlery.services.misc import Null, ReceiveFunction


@pytest.fixture
def message():
    return {
        "foo": "bar",
    }


@pytest.fixture
def service():
    return Null()


def test_on_after_send(service, message):
    captured = []

    def capture(service, message):
        captured.append((service, message))

    with signals.on_after_send.connected_to(capture):
        service.send(**message)

        assert captured[0][0] is service
        assert captured[0][1] == message


def test_on_before_send(service, message):
    captured = []

    def capture(service, message):
        captured.append((service, message))

    with signals.on_before_send.connected_to(capture):
        service.send(**message)

        assert captured[0][0] is service
        assert captured[0][1] == message


def test_on_close_session(mocker, service):
    stub = mocker.stub(name="on_close_session")

    def on_close_session(sender):
        stub(sender)

    with signals.on_open_session.connected_to(on_close_session):
        service.open()
        service.close()

    stub.assert_called_once_with(service)


def test_on_open_session(mocker, service):
    stub = mocker.stub(name="on_open_session")

    def on_open_session(sender):
        stub(sender)

    with signals.on_open_session.connected_to(on_open_session):
        service.open()

    stub.assert_called_once_with(service)


def test_on_receive_message(message):
    captured = []

    def capture(service, message):
        captured.append((service, message))

    def receive(**kwargs):
        return [message]

    service = ReceiveFunction(receive)

    with signals.on_receive_message.connected_to(capture):
        for _ in service.receive():
            pass

        assert captured[0][0] is service
        assert captured[0][1] == message
