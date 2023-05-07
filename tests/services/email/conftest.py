import pytest

from owlery.services.email import EmailManager


@pytest.fixture()
def manager():
    return EmailManager()
