import datetime as dt

from celery import Celery

from owlery.exceptions import ServiceConnectError
from owlery.services.email import EmailManager

email = EmailManager()

app = Celery("owlery")


@app.task(autoretry_for=(ServiceConnectError,), retry_backoff=True)
def send_email(**kwargs):
    """Send an email asynchronously."""
    email.send(**kwargs)


# send an email asynchronously
send_email.delay(
    to="someone@example.com",
    subject="Test message",
    body="This is a test message.",
    from_="admin@example.org",
)

# send an email in 15 minutes time
eta = dt.datetime.now() + dt.timedelta(minutes=15)
send_email.delay(
    to="someone@example.com",
    subject="Test message",
    body="This is a test message.",
    from_="admin@example.org",
    eta=eta,
)
