import pytest

from flask import Flask

from owlery.integrations.flask import Owlery
from owlery.services.email import EmailManager
from owlery.services.email.smtp import SMTP
from owlery.services.misc import Null


@pytest.fixture
def app():
    app = Flask(__name__)
    app.testing = True

    return app


@pytest.fixture
def extension(app):
    return Owlery(app)


def test_init(app):
    Owlery(app)

    assert "owlery" in app.extensions


def test_init_app(app):
    owlery = Owlery()

    assert "owlery" not in app.extensions

    owlery.init_app(app)

    assert "owlery" in app.extensions


def test_register_manager(app, extension):
    email = extension.register(EmailManager, name="email")

    assert "email" in app.extensions["owlery"]
    assert email in app.extensions["owlery"].values()


def test_register_manager_pre_init():
    app = Flask(__name__)
    extension = Owlery()

    email = extension.register(EmailManager, name="email")

    assert any(s[0] == "email" for s in extension.default_services)

    with pytest.raises(RuntimeError):
        email.services

    extension.init_app(app)

    assert "email" in app.extensions["owlery"]

    with app.app_context():
        assert email in app.extensions["owlery"].values()


def test_register_service(app, extension):
    null = extension.register(Null, name="null")

    assert "null" in app.extensions["owlery"]["services"]
    assert null in app.extensions["owlery"]["services"].values()


def test_register_service_pre_init():
    app = Flask(__name__)
    extension = Owlery()

    null = extension.register(Null, name="null")

    assert any("null" in s[0] for s in extension.default_services)

    with pytest.raises(RuntimeError):
        null.name

    extension.init_app(app)

    assert "null" in app.extensions["owlery"]["services"]

    with app.app_context():
        assert null in app.extensions["owlery"]["services"].values()


def test_config_manager(app, extension):
    app.config["OWLERY_EMAIL_DEFAULT_CLS"] = SMTP
    app.config["OWLERY_EMAIL_DEFAULT_HOST"] = "localhost"
    app.config["OWLERY_EMAIL_DEFAULT_PORT"] = 25

    app.config["OWLERY_EMAIL_BULK_CLS"] = SMTP
    app.config["OWLERY_EMAIL_BULK_HOST"] = "remotehost"
    app.config["OWLERY_EMAIL_BULK_PORT"] = 26

    manager = extension.register(EmailManager, name="email")

    assert "default" in manager.services
    assert manager.services["default"].host == "localhost"
    assert manager.services["default"].port == 25

    assert "bulk" in manager.services
    assert manager.services["bulk"].host == "remotehost"
    assert manager.services["bulk"].port == 26


def test_config_service(app, extension):
    app.config["OWLERY_SERVICES_SMTP_HOST"] = "remotehost"
    app.config["OWLERY_SERVICES_SMTP_PORT"] = 26

    smtp = extension.register(SMTP)

    assert smtp.host == "remotehost"
    assert smtp.port == 26
