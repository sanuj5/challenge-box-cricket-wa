import base64
import json

from service.base_message_processor import BaseProcessor
from model.exceptions import InvalidStateException
from logger import Logger


class PaymentProcessor(BaseProcessor):
    def __init__(self):
        super().__init__()

    def validate_payment_response(self, header, response):
        # TODO get mobile number from response transaction ID
        validated_response = self.payment_service.validate_response(header, response)
        Logger.info(f"Response validation {validated_response}")
        existing_booking = dict()
        if validated_response:
            response_string = base64.b64decode(
                json.loads(response).get("response"))
            Logger.info(response_string)
            existing_booking = self.db_service.get_pending_booking(
                validated_response.get("order_id"))
            if validated_response.get("success"):
                amount = validated_response.get("amount")
                # TODO validate amount
                self.db_service.confirm_booking(
                    existing_booking,
                    validated_response.get("order_id"),
                    validated_response.get("original_response")
                )
                return_message = self.mbs.get_final_text_message(
                    existing_booking.get("mobile"),
                    "",
                    f"""Awesome, your booking is confirmed!!! 

    Date: {existing_booking.get("date")}
    Slots: {", ".join([self.slots.get(slot.strip()).get("title") for slot in existing_booking.get("slots")])}
    Amount paid: {existing_booking.get("amount")}         

    Happy Cricketing!!!           
    """
                )
            else:
                return_message = self.mbs.get_final_text_message(
                    existing_booking.get("mobile"),
                    "",
                    "Your payment is timed out. Please start new booking."
                )
        else:
            return_message = self.mbs.get_final_text_message(
                existing_booking.get("mobile"),
                "",
                "Some error has occurred while processing your request."
            )
        self.api_service.send_post_request(return_message)

    def generate_payment_link(self, amount, transaction_id):
        self.db_service.remove_pending_bookings()
        if not self.db_service.get_mobile_token_mapping(transaction_id):
            raise InvalidStateException("Invalid transaction token")
        elif not self.db_service.get_pending_booking(transaction_id):
            raise InvalidStateException("<h1>This payment link is expired. "
                                        "Please start new booking from WhatsApp.</h1>")
        else:
            return self.payment_service.generate_payment_link(
                amount, transaction_id
            )
