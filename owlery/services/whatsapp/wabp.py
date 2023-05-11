import dataclasses
import typing as t

import phonenumbers

from twilio.request_validator import RequestValidator
from twilio.rest import Client

from .. import Attachment, ServiceManager
from . import WhatsApp, WhatsAppLocation, WhatsAppMessage


class WhatsAppBusinessPlatform(WhatsApp):
    """Send WhatsApp messages with WhatsApp Business Platform.

    :param account_sid: Twilio Account SID.
    :param auth_token: Twilio Authentication Token.
    :param region: Region to parse phone numbers in.
    :param sender_id: Your WhatsApp Sender ID.

    """

    name = "whatsapp_business_platform"

    def __init__(
        self,
        account_sid: t.Optional[str] = None,
        auth_token: t.Optional[str] = None,
        **kwargs,
    ):
        self.auth_token = auth_token
        self.client = Client(account_sid, auth_token)

        super().__init__(**kwargs)

    def format_number(self, number):
        number = number.lstrip("whatsapp:")

        number = phonenumbers.parse(number)
        number = phonenumbers.format_number(
            number, phonenumbers.PhoneNumberFormat.E164
        )

        return f"whatsapp:{number}"

    def receive(self, limit: int = 100, **kwargs):
        messages = self.client.messages.stream(
            to=self.sender_id,
            date_sent_after=date_sent_after,
            limit=limit,
        )

        for message in messages:
            to = message.to.lstrip("whatsapp:")
            from_ = message.waid.lstrip("whatsapp:")

            yield WhatsAppMessage(
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

        to = request.form["To"].lstrip("whatsapp:")
        body = request.form["Body"]
        from_ = request.form["From"].lstrip("whatsapp:")

        message = WhatsAppMessage(
            to=to,
            body=body,
            from_=from_,
            id=request.form["MessageSid"],
            reply_id=request.form.get("OriginalRepliedMessageSid"),
            profile_name=request.form.get("ProfileName"),
            forwarded=request.form.get("Forwarded", False),
            frequently_forwarded=request.form.get(
                "FrequentlyForwarded", False
            ),
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

        if request.form.get("Latitude") and request.form.get("Longitude"):
            location = WhatsAppLocation(
                lat=request.form["Latitude"],
                lon=request.form["Longitude"],
                address=request.form.get("Address"),
                label=request.form.get("Label"),
            )

            message.location = location

        return message

    def send(
        self,
        to,
        body,
        from_=None,
        attachments=None,
        location=None,
        **kwargs,
    ):
        if not from_:
            from_ = self.sender_id
        if from_:
            from_ = self.format_number(from_)

        to = self.format_number(to)

        result = self.client.messages.create(
            to=to,
            body=body,
            from_=from_,
            # media_url=media_urls,
        )

        message = WhatsAppMessage(
            to=to.lstrip("whatsapp:"),
            body=body,
            from_=from_.lstrip("whatsapp:"),
            attachments=attachments,
            location=location,
            id=result.sid,
            raw=result,
            service=self,
        )

        return message
