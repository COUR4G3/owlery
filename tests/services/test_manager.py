import pytest

from owlery.exceptions import (
    ServiceNotRegistered,
    ServiceReceiveCapabilityError,
    ServiceSendCapabilityError,
)
from owlery.services import Message, Service, ServiceManager


class ServiceTest(Service):
    name = "test"
    can_send = True

    def __init__(self):
        self.last_sent = None

        super().__init__()

    def send(self, **kwargs):
        self.last_sent = kwargs


class ServiceTestReceive(Service):
    name = "test_receive"
    can_receive = True

    def __init__(self, message):
        self.message = message
        super().__init__()

    def receive(self, **kwargs):
        yield Message(raw=self.message)


@pytest.fixture
def manager():
    return ServiceManager()


def test_close(manager):
    service1 = manager.register(ServiceTest, name="service1")
    service1.open()
    assert service1.opened is True

    service2 = manager.register(ServiceTest, name="service2")
    service2.open()
    assert service2.opened is True

    manager.close()

    assert service1.opened is False
    assert service2.opened is False


def test_close_contextmanager(manager):
    pass


def test_ensure_service(manager):
    with pytest.raises(ServiceNotRegistered):
        manager.ensure_service()

    manager.register(ServiceTest)
    manager.ensure_service()


def test_ensure_service_name(manager):
    with pytest.raises(ServiceNotRegistered):
        manager.ensure_service("name")

    manager.register(ServiceTest, name="name")
    manager.ensure_service("name")


def test_ensure_service_receive(manager):
    with pytest.raises(ServiceNotRegistered):
        manager.ensure_service(receive=True)

    manager.register(ServiceTest, name="service1")

    with pytest.raises(ServiceReceiveCapabilityError):
        manager.ensure_service(receive=True)

    with pytest.raises(ServiceReceiveCapabilityError):
        manager.ensure_service(name="service1", receive=True)

    manager.register(ServiceTestReceive, name="service2", message=None)
    manager.ensure_service(receive=True)


def test_ensure_service_send(manager):
    with pytest.raises(ServiceNotRegistered):
        manager.ensure_service(send=True)

    manager.register(ServiceTestReceive, message=None, name="service1")

    with pytest.raises(ServiceSendCapabilityError):
        manager.ensure_service(send=True)

    with pytest.raises(ServiceSendCapabilityError):
        manager.ensure_service(name="service1", send=True)

    manager.register(ServiceTest, name="service2")
    manager.ensure_service(send=True)


def test_outbox(manager):
    service1 = manager.register(ServiceTest, name="service1")
    service2 = manager.register(ServiceTest, name="service2")

    with manager.outbox() as outbox:
        manager.send()
        manager.send(via="service2")

        assert len(outbox) == 2

        assert service1.last_sent is None
        assert service2.last_sent is None

    assert service1.last_sent is not None
    assert service2.last_sent is not None


def test_outbox_explicit_discard(manager):
    service1 = manager.register(ServiceTest, name="service1")
    service2 = manager.register(ServiceTest, name="service2")

    with manager.outbox() as outbox:
        manager.send()
        manager.send(via="service2")

        outbox.discard()

    assert service1.last_sent is None
    assert service2.last_sent is None


def test_outbox_implicit_discard(manager):
    service1 = manager.register(ServiceTest, name="service1")
    service2 = manager.register(ServiceTest, name="service2")

    try:
        with manager.outbox():
            manager.send()
            manager.send(via="service2")

            assert 1 == 0
    except AssertionError:
        pass

    assert service1.last_sent is None
    assert service2.last_sent is None


def test_outbox_explicit_release(manager):
    service1 = manager.register(ServiceTest, name="service1")
    service2 = manager.register(ServiceTest, name="service2")

    with manager.outbox() as outbox:
        manager.send()
        manager.send(via="service2")

        outbox.release()

        assert service1.last_sent is not None
        assert service2.last_sent is not None


def test_register(manager):
    service = manager.register(ServiceTest)
    assert len(manager.services) == 1
    assert service in manager.services.values()


def test_register_name(manager):
    service = manager.register(ServiceTest, name="service1")
    assert len(manager.services) == 1
    assert service is manager.services["service1"]


def test_register_no_overwrite(manager):
    manager.register(ServiceTest, name="service1")
    with pytest.raises(KeyError):
        manager.register(ServiceTest, name="service1")

    assert len(manager.services) == 1


def test_register_overwrite(manager):
    manager.register(ServiceTest, name="service1")
    manager.register(ServiceTest, name="service1", overwrite=True)
    assert len(manager.services) == 1


def test_receive_no_service(manager):
    with pytest.raises(ServiceReceiveCapabilityError):
        for _ in manager.receive():
            pass


def test_receive_no_send_service(manager):
    manager.register(ServiceTest)

    with pytest.raises(ServiceReceiveCapabilityError):
        for _ in manager.receive():
            pass


def test_receive_via(manager):
    manager.register(ServiceTestReceive, message=1, name="service1")
    assert len(manager.services) == 1

    manager.register(ServiceTestReceive, message=2, name="service2")
    assert len(manager.services) == 2

    for message in manager.receive(via="service1"):
        assert message.raw == 1

    for message in manager.receive(via="service2"):
        assert message.raw == 2


def test_receive_via_missing(manager):
    with pytest.raises(ServiceNotRegistered) as e:
        for _ in manager.receive(via="test"):
            pass
    assert e.value.name == "test"


def test_send_no_service(manager):
    with pytest.raises(ServiceSendCapabilityError):
        manager.send()


def test_send_no_send_service(manager):
    manager.register(ServiceTestReceive, message=None)

    with pytest.raises(ServiceSendCapabilityError):
        manager.send()


def test_send_via_default(manager):
    manager.register(ServiceTestReceive, name="service1", message=None)

    service2 = manager.register(ServiceTest, name="service2")

    service3 = manager.register(ServiceTest, name="service3")
    assert len(manager.services) == 3

    manager.send(to="admin@example.com")
    assert service2.last_sent == dict(to="admin@example.com")
    assert service3.last_sent is None


def test_send_via_func(manager):
    service1 = manager.register(ServiceTest, name="service1")
    assert len(manager.services) == 1

    service2 = manager.register(ServiceTest, name="service2")
    assert len(manager.services) == 2

    @manager.via
    def via_service(manager, **kwargs):
        if kwargs.get("to") == "admin@example.com":
            return "service1"
        else:
            return "service2"

    manager.send(to="admin@example.com")
    assert service1.last_sent == dict(to="admin@example.com")

    manager.send(to="someone@example.com")
    assert service2.last_sent == dict(to="someone@example.com")


def test_send_via_kwargs(manager):
    service1 = manager.register(ServiceTest, name="service1")
    assert len(manager.services) == 1

    service2 = manager.register(ServiceTest, name="service2")
    assert len(manager.services) == 2

    manager.send(to="admin@example.com", via="service1")
    assert service1.last_sent == dict(to="admin@example.com")

    manager.send(to="someone@example.com", via="service2")
    assert service2.last_sent == dict(to="someone@example.com")


def test_send_via_missing(manager):
    with pytest.raises(ServiceNotRegistered) as e:
        manager.send(via="test")
    assert e.value.name == "test"


def test_suppress(manager):
    manager.suppress = True
    service = manager.register(ServiceTest)
    manager.send()

    assert service.last_sent is None


def test_suppressed(manager):
    service = manager.register(ServiceTest)

    manager.send()
    assert service.last_sent is not None
    service.last_sent = None

    with manager.suppressed():
        manager.send()

        assert service.last_sent is None

    manager.send()
    assert service.last_sent is not None


def test_unregister_by_name(manager):
    service = manager.register(ServiceTest, name="name")
    assert len(manager.services) == 1

    manager.unregister("name")
    assert len(manager.services) == 0
    assert service not in manager.services.values()


def test_unregister_by_name_ignore_missing(manager):
    manager.unregister("name", ignore_missing=True)


def test_unregister_by_name_missing(manager):
    with pytest.raises(KeyError):
        manager.unregister("name")


def test_unregister_by_object(manager):
    service = manager.register(ServiceTest, name="name")
    assert len(manager.services) == 1

    manager.unregister(service)
    assert len(manager.services) == 0
    assert service not in manager.services.values()


def test_unregister_by_object_ignore_missing(manager):
    service = ServiceTest()
    manager.unregister(service, ignore_missing=True)
    assert len(manager.services) == 0


def test_unregister_by_object_missing(manager):
    service = ServiceTest()

    with pytest.raises(KeyError):
        manager.unregister(service)


# TODO: test the following:
# - outbox
# - suppress
# - suppressed contextmanager
# - test open-close contextmanager
# - test for notimplemented on send-receive
