import base64
import json

from external.payment import BasePayment
from model.payment_status import PaymentStatus
from service.base_message_processor import BaseProcessor
from model.exceptions import InvalidStateException
from logger import Logger
from service.notification_processor import NotificationProcessor


class PaymentProcessor(BaseProcessor):
    def __init__(self, db_service, payment_service):
        super().__init__(db_service)
        self.payment_service: BasePayment = payment_service
        self.notification_service = NotificationProcessor(db_service)

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
                token=validated_response.get("order_id"))
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
        elif not self.db_service.get_pending_booking(token=transaction_id):
            raise InvalidStateException("<h1>This payment link is expired. "
                                        "Please start new booking from WhatsApp.</h1>")
        else:
            return self.payment_service.generate_payment_link(
                amount, transaction_id
            )

    def validate_status(self, message: PaymentStatus):
        Logger.info(f"Payment Status {message}")
        existing_booking = self.db_service.get_pending_booking(
            token=message.payment.reference_id
        )
        confirmed_booking = self.db_service.get_confirmed_booking_by_token(
            token=message.payment.reference_id
        )
        if message.status == "captured":
            wa_payment_status = self.api_service.get_payment_status(
                message.payment.reference_id)
            # razorpay_payment_status = self.payment_service.get_payment(
            #     message.payment.reference_id)
            if (
                    wa_payment_status.get("payments")
                    and wa_payment_status.get("payments")[0]
                    and wa_payment_status.get("payments")[0].get("status") == "CAPTURED"
            ):
                if not existing_booking:
                    # TODO refund the amount
                    Logger.error(
                        "Existing booking does not exist for {}".format(
                            wa_payment_status,
                        ))
                elif confirmed_booking:
                    Logger.error(
                        "Booking already is confirmed {}".format(
                            wa_payment_status,
                        ))
                else:
                    self.db_service.confirm_booking(existing_booking,
                                                    message.payment.reference_id,
                                                    json.dumps(message,
                                                               default=lambda
                                                                   o: o.__dict__
                                                               )
                                                    )
                    self.api_service.send_message_request(
                        self.mbs.get_order_confirmation_message(
                            mobile=message.recipient_id,
                            token=message.payment.reference_id,
                            message=f"""

*Your booking is confirmed.*

Date: {existing_booking.get("date")}
Slots" {", ".join([self.slots.get(slot.strip()).get("title") for slot in existing_booking.get("slots")])}
""")

                    )
                    self.notification_service.send_payment_notifications(
                        existing_booking.get("date"),
                        ", ".join([
                            self.slots.get(slot.strip()).get("title") for slot in
                            existing_booking.get("slots")
                        ]),
                        f"{existing_booking.get("mobile")}",
                        str(float(existing_booking.get("amount")))
                    )
            else:
                Logger.error("Payment Status is invalid {} {}".format(wa_payment_status,
                                                                      existing_booking))
        else:
            Logger.error("Payment Status is invalid {} {}".format(
                existing_booking,
                message.status))
        return "", 200
