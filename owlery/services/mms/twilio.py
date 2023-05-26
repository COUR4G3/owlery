import typing as t

from twilio.request_validator import RequestValidator
from twilio.rest import Client

from .. import Attachment
from . import MMS, MMSMessage


class TwilioMMS(MMS):
    """Send MMS multimedia messages with Twilio.

    :param account_sid: Twilio Account SID.
    :param auth_token: Twilio Authentication Token.
    :param region: Region to parse phone numbers in.
    :param sender_id: Your MMS Sender ID.

    """

    name = "twilio_mms"

    def __init__(
        self,
        account_sid: t.Optional[str] = None,
        auth_token: t.Optional[str] = None,
        **kwargs,
    ):
        self.client = Client(account_sid, auth_token)

        super().__init__(**kwargs)

    def receive(self, limit: int = 100, **kwargs):
        messages = self.client.messages.stream(
            to=self.sender_id,
            date_sent_after=date_sent_after,
            limit=limit,
        )

        for message in messages:
            to = message.to
            from_ = message.waid

            yield MMSMessage(
                to=to,
                body=message.body,
                from_=from_,
            )

    def receive_webhook(self, request):
        validator = RequestValidator(self.auth_token)
        if not validator.validate(
            request.url,
            request.form,
            request.headers.get("X-Twilio-Signature"),
        ):
            raise ValueError("Invalid signature")

        to = request.form["To"]
        body = request.form["Body"]
        from_ = request.form["From"]

        message = MMSMessage(
            to=to,
            body=body,
            from_=from_,
            id=request.form["MessageSid"],
            reply_id=request.form.get("OriginalRepliedMessageSid"),
            raw=request.form,
            service=self,
        )

        for i in range(request.form["NumMedia"]):
            response = self.client.request("GET", request.form[f"MediaUrl{i}"])

            attachment = Attachment(
                data=response.content,
                mimetype=request.form[f"MediaContentType{i}"],
            )

            message.attachments.append(attachment)

        return message

    def send(
        self,
        to,
        body,
        from_=None,
        attachments=None,
        **kwargs,
    ):
        if not from_:
            from_ = self.sender_id
        if from_:
            from_ = self.format_number(from_)

        to = self.format_number(to)

        message = MMSMessage(
            to=to,
            body=body,
            from_=from_,
            attachments=attachments,
            raw=kwargs,
            service=self,
        )

        try:
            result = self.client.messages.create(
                to=to,
                body=body,
                from_=from_,
                # media_url=media_urls,
            )
        except Exception as e:
            message.exc = e
            message.status = "error"
        else:
            message.id = result.sid
            message.raw = result
            message.status = "sent"

        return message
