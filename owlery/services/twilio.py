import typing as t

from twilio.request_validator import RequestValidator
from twilio.rest import Client

MAP_TWILIO_STATUS = {
    "read": "read",
}


class TwilioMixin:
    """Mixin to send and receive messages with Twilio.

    :param account_sid: Twilio Account SID.
    :param auth_token: Twilio Authentication Token.
    :param region: Region to parse phone numbers in.
    :param sender_id: Your WhatsApp Sender ID.

    """

    name = "twilio"

    can_receive = True
    can_send = True

    has_receive_webhook = True
    has_receive_webhook_methods = ["POST"]

    has_status_callback = True
    has_status_callback_methods = ["POST"]

    def __init__(
        self,
        account_sid: t.Optional[str] = None,
        auth_token: t.Optional[str] = None,
        **kwargs,
    ):
        self.client = Client(account_sid, auth_token)

        super().__init__(**kwargs)

    def _validate_webhook_request(self, request):
        validator = RequestValidator(self.auth_token)
        if not validator.validate(
            request.url,
            request.values,
            request.headers.get("X-Twilio-Signature"),
        ):
            raise ValueError("Invalid signature")

    def status_callback(self, request):
        # url = request.build_absolute_uri()
        # data = request.POST
        # headers = request.META

        self._validate_webhook_request(request)

        message_id = request.values["MessageSid"]

        twilio_status = request.values["MessageStatus"]
        status = MAP_TWILIO_STATUS.get(twilio_status, "unknown")

        yield message_id, status, request.values
