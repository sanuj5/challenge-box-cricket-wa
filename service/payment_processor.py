import base64
import json

from external.payment import BasePayment
from model.payment_status import PaymentStatus
from model.templates import TemplateBuilder as tb
from service.base_message_processor import BaseProcessor
from model.exceptions import InvalidStateException
from logger import Logger


class PaymentProcessor(BaseProcessor):
    def __init__(self, db_service, payment_service):
        super().__init__(db_service)
        self.payment_service: BasePayment = payment_service

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
        self.api_service.send_message_request(return_message)

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

    def validate_status(self, message: PaymentStatus):
        Logger.info(f"Payment Status {message}")
        existing_booking = self.db_service.get_pending_booking(
            message.payment.reference_id
        )
        if existing_booking and message.status == "captured":
            wa_payment_status = self.api_service.get_payment_status(
                message.payment.reference_id)
            # razorpay_payment_status = self.payment_service.get_payment(
            #     message.payment.reference_id)
            if (
                    wa_payment_status.get("payments")
                    and wa_payment_status.get("payments")[0]
                    and wa_payment_status.get("payments")[0].get("status") == "CAPTURED"
            ):
                self.db_service.confirm_booking(existing_booking,
                                                message.payment.reference_id,
                                                json.dumps(message,
                                                           default=lambda o: o.__dict__
                                                           )
                                                )
                self.api_service.send_message_request(
                    self.mbs.get_order_confirmation_message(
                        mobile=message.recipient_id,
                        token=message.payment.reference_id,
                        message="Booking Confirmed")
                )
                self.send_payment_notifications(
                    existing_booking.get("date"),
                    ", ".join([
                        self.slots.get(slot.strip()).get("title") for slot in existing_booking.get("slots")
                    ]),
                    existing_booking.get("name"),
                    existing_booking.get("mobile"),
                    str(float(existing_booking.get("amount")))
                )
            else:
                Logger.error("Payment Status is invalid {}".format(wa_payment_status))
        else:
            Logger.error("Payment Status is invalid {} {}".format(
                existing_booking,
                message.status))
        return "", 200

    def send_payment_notifications(self, date, slots, name, booking_number, amount):
        mobile_numbers = self.db_service.get_notification_eligible_numbers()
        for mobile_number in mobile_numbers:
            self.api_service.send_message_request(
                tb.build(
                    mobile=mobile_number,
                    template_name="new_booking_notification",
                    parameters=[
                        tb.get_text_parameter(date),
                        tb.get_text_parameter(slots),
                        tb.get_text_parameter(name),
                        tb.get_text_parameter(booking_number),
                        tb.get_text_parameter(amount),
                    ]
                )
            )
