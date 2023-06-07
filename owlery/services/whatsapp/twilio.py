import phonenumbers

from .. import Attachment
from ..twilio import TwilioMixin
from . import WhatsApp, WhatsAppLocation, WhatsAppMessage


class TwilioWhatsApp(TwilioMixin, WhatsApp):
    """Send WhatsApp messages with Twilio.

    :param account_sid: Twilio Account SID.
    :param auth_token: Twilio Authentication Token.
    :param region: Region to parse phone numbers in.
    :param sender_id: Your WhatsApp Sender ID.

    """

    name = "twilio_whatsapp"

    def format_number(self, number):
        number = number.replace("whatsapp:", "")

        number = phonenumbers.parse(number, self.region)
        number = phonenumbers.format_number(
            number,
            phonenumbers.PhoneNumberFormat.E164,
        )

        return f"whatsapp:{number}"

    def receive(self, limit: int = 100, **kwargs):
        messages = self.client.messages.stream(
            to=self.format_number(self.sender_id),
            # date_sent_after=date_sent_after,
            limit=limit,
        )

        for message in messages:
            to = message.to.replace("whatsapp:", "")
            from_ = message.waid.replace("whatsapp:", "")

            yield WhatsAppMessage(
                to=to,
                body=message.body,
                from_=from_,
            )

    def receive_webhook(self, request):
        self._validate_webhook_request(request)

        to = request.form["To"].replace("whatsapp:", "")
        body = request.form["Body"]
        from_ = request.form["From"].replace("whatsapp:", "")

        message = WhatsAppMessage(
            to=to,
            body=body,
            from_=from_,
            id=request.form["MessageSid"],
            reply_id=request.form.get("OriginalRepliedMessageSid"),
            profile_name=request.form.get("ProfileName"),
            forwarded=request.form.get("Forwarded", False),
            frequently_forwarded=request.form.get(
                "FrequentlyForwarded",
                False,
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

        yield message

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

        if attachments:
            media_urls = self.generate_media_urls(attachments)
        else:
            media_urls = None

        message = WhatsAppMessage(
            to=to.replace("whatsapp:", ""),
            body=body,
            from_=from_ and from_.replace("whatsapp:", "") or None,
            attachments=attachments,
            location=location,
            raw=kwargs,
            service=self,
        )

        try:
            result = self.client.messages.create(
                to=to,
                body=body,
                from_=from_,
                media_url=media_urls,
            )
        except Exception as e:
            message.exc = e
            message.status = "error"
        else:
            message.id = result.sid
            message.raw = result
            message.status = "sent"

        return message
