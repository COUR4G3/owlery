"""Example of using Redis Queue to asynchronously send email messages.


Author: Michael de Viliers <michael@devilears.co.za>

"""
import datetime as dt

from redis import Redis
from rq import Queue

from owlery.services.email import EmailManager

email = EmailManager()

queue = Queue(connection=Redis())


def send_email(**kwargs):
    """Send an email asynchronously."""
    email.send(**kwargs)


# send an email asynchronously
queue.enqueue(
    send_email,
    to="someone@example.com",
    subject="Test message",
    body="This is a test message.",
    from_="admin@example.org",
)

# send an email in 15 minutes time
queue.enqueue_at(
    dt.datetime.now() + dt.timedelta(minutes=15),
    send_email,
    to="someone@example.com",
    subject="Test message",
    body="This is a test message.",
    from_="admin@example.org",
)
