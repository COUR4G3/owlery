"""Example of using Redis Queue to create an email queue manager.

An email queue manager periodically sends a batch of emails from a queue using
Redis Queue and RQ-Scheduler.


Author: Michael de Viliers <michael@devilears.co.za>

"""

import datetime as dt
import json

from redis import Redis
from rq import Queue
from rq_scheduler import Scheduler

from owlery.services.email import EmailManager

email = EmailManager()

redis = Redis()

queue = Queue(connection=redis)

queue_name = "email-queue"


def queue_email(**kwargs):
    """Queue a message for sending."""
    redis.lpush(queue_name, json.dumps(kwargs))


def queue_manager(limit=10):
    """Send up to ``limit`` messages in the queue."""
    messages = redis.rpop(queue_name, limit)

    with email:
        for message in messages:
            message = json.loads(message)

            email.send(**message)


scheduler = Scheduler(connection=redis)

# run the queue manager every 15 minutes to send up to 10 queued emails
scheduler.schedule(
    scheduled_time=dt.datetime.utcnow(),
    func=queue_manager,
    kwargs={"limit": 10},
    interval=900,
    repeat=0,
)
