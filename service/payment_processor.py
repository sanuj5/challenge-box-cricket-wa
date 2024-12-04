import base64
import json

from external.payment import BasePayment
from model.payment_status import PaymentStatus, Payment, Amount
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
        validate_request = self.payment_service.validate_response(header, response)
        Logger.info(f"Response validation {validate_request}")
        if validate_request:
            response_dict = json.loads(response)
            if response_dict.get('event') != "order.paid":
                Logger.info(f"Ignoring other event {response_dict.get('event')}")
                return
            payment_payload = response_dict.get("payload").get(
                "payment").get("entity")
            order_payload = response_dict.get("payload").get(
                "order").get("entity")
            mapping = self.db_service.get_mobile_token_mapping(
                order_payload.get("receipt")
            )
            if mapping is None:
                Logger.error(
                    f"No mobile token mapping found for toke {order_payload.get('receipt')}")
                return
            self.validate_status(
                PaymentStatus(
                    id=order_payload.get("receipt"),
                    status=payment_payload.get("status"),
                    payment=Payment(
                        reference_id=order_payload.get("receipt"),
                        amount=Amount(
                            order_payload.get("amount_paid"),
                            self.secrets.get("AMOUNT_OFFSET")
                        ),
                        currency=order_payload.get("currency")
                    ),
                    recipient_id=mapping.get(order_payload.get("receipt")),
                    timestamp=response_dict.get("created_at"),
                    type="payment_link"
                )
            )

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
        success = self.is_payment_successful(message)
        if success:
            if not existing_booking:
                # TODO refund the amount
                Logger.error(
                    "Existing booking does not exist for {}".format(
                        message,
                    ))
            elif confirmed_booking:
                Logger.error(
                    "Booking already is confirmed {}".format(
                        message,
                    ))
            elif self.check_if_slot_unavailable(existing_booking.get("date"),
                                                existing_booking.get("slots")):
                Logger.error(
                    "Slot was booked while confirming this booking {}".format(
                        message,
                    ))
            else:
                self.db_service.confirm_booking(existing_booking,
                                                message.payment.reference_id,
                                                json.dumps(message,
                                                           default=lambda
                                                               o: o.__dict__
                                                           )
                                                )
                name = self.db_service.get_user_details(
                    mobile=message.recipient_id) or ""
                self.api_service.send_message_request(
                    self.mbs.get_order_confirmation_message(
                        mobile=message.recipient_id,
                        token=message.payment.reference_id,
                        message=f"""

*Hi {name}, your booking is confirmed.*

Date: {existing_booking.get("date")}
Slots: {", ".join([slot.get("title") for slot in sorted(
                            [self.slots.get(slot) for slot in
                             existing_booking.get("slots")],
                            key=lambda x: x.get("sort_order"))])}
""")

                )
                self.notification_service.send_payment_notifications(
                    existing_booking.get("date"),
                    ", ".join([slot.get("title") for slot in sorted(
                        [self.slots.get(slot) for slot in
                         existing_booking.get("slots")],
                        key=lambda x: x.get("sort_order"))]),
                    f"{existing_booking.get("mobile")}",
                    str(float(existing_booking.get("amount")))
                )
        else:
            Logger.error("Payment Status is invalid {} {}".format(
                existing_booking,
                message.status))
        return "", 200

    def check_if_slot_unavailable(self, date: str, slots: list) -> bool:
        confirmed_booking_for_today = self.db_service.get_confirmed_bookings(date)
        for booking in confirmed_booking_for_today:
            for slot in booking.slots:
                if slot.strip() in slots:
                    return True
        return False

    def verify_payment_link_signature(
            self,
            payment_link_id,
            payment_link_reference_id,
            payment_link_status,
            razorpay_payment_id,
            razorpay_signature
    ) -> bool:
        return self.payment_service.verify_payment_link_signature(
            payment_link_id=payment_link_id,
            payment_link_reference_id=payment_link_reference_id,
            payment_link_status=payment_link_status,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature
        )

    def process_tournament_payment(self, message: PaymentStatus):
        Logger.info(f"Payment Status {message}")
        success = self.is_payment_successful(message)
        if success:
            self.db_service.confirm_tournament_payment(
                mobile=message.recipient_id,
                token=message.payment.reference_id,
                payment_response=json.dumps(message,
                                            default=lambda
                                                o: o.__dict__
                                            )
            )
            name = self.db_service.get_user_details(
                mobile=message.recipient_id) or ""
            registraion = self.db_service.get_tournament_registration(
                message.payment.reference_id
            )
            amount = registraion.get("amount")
            team_name = registraion.get("team_name")
            self.api_service.send_message_request(
                self.mbs.get_order_confirmation_message(
                    mobile=message.recipient_id,
                    token=message.payment.reference_id,
                    message=f"""Payment of *₹ {amount}/-* is successful.""")
            )

            self.notification_service.send_custom_notification_with_image(
                mobile=message.recipient_id,
                message=f"""Congratulations *{name}*, You have successfully enrolled your team *{team_name}* for upcoming box cricket tournament. Practice hard and go for the win.""",
                image_url=self.db_service.get_tournament_details().get("image_url")
            )
            self.notification_service.send_tournament_registration_notification(
                name,
                message.recipient_id,
                team_name,
                amount
            )
        else:
            Logger.error("Payment Status is invalid {} {}".format(
                message.payment.reference_id,
                message.status))
        return "", 200

    def is_payment_successful(self, message):
        success = False
        if message.status == "captured":
            if message.type == "payment_link":
                success = True
            else:
                wa_payment_status = self.api_service.get_payment_status(
                    message.payment.reference_id)
                if (
                        wa_payment_status.get("payments")
                        and wa_payment_status.get("payments")[0]
                        and wa_payment_status.get("payments")[0].get(
                    "status") == "CAPTURED"
                ):
                    success = True
                else:
                    Logger.error(
                        "Payment Status is invalid {}".format(wa_payment_status))
        return success
