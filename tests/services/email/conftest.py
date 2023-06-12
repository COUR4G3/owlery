import random

from email.utils import make_msgid

import factory
import pytest

from owlery.services.email import EmailManager, EmailMessage, EmailRecipient


def generate_name():
    return random.choice(
        [str(factory.Faker("name")), str(factory.Faker("user_name")), None],
    )


class EmailRecipientFactory(factory.Factory):
    class Meta:
        model = EmailRecipient

    name = factory.LazyFunction(generate_name)
    email = factory.Faker("email")


def generate_msgid():
    level = random.randint(0, 2)
    return make_msgid(domain=factory.Faker("hostname", level=level))


def generate_recipient():
    return random.choice([EmailRecipientFactory(), factory.Faker("email")])


def generate_recipients(min=1, max=3):
    return [generate_recipient() for _ in range(random.randint(min, max))]


class EmailMessageFactory(factory.Factory):
    class Meta:
        model = EmailMessage

    to = factory.LazyFunction(generate_recipients)
    subject = factory.Faker("sentence")
    body = factory.Faker("paragraph")
    from_ = factory.LazyFunction(generate_recipient)
    date = factory.Faker("date_time_this_decade")
    id = factory.LazyFunction(generate_msgid)


@pytest.fixture()
def manager():
    return EmailManager()


@pytest.fixture()
def message():
    return EmailMessageFactory()
