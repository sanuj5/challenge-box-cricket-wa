import datetime

import pytz

from logger import Logger
from service.base_message_processor import BaseProcessor
from model.templates import TemplateBuilder as tb


class NotificationProcessor(BaseProcessor):
    def __init__(self, db_service):
        super().__init__(db_service)

    """
    Send booking notification immediately 
    """

    def send_payment_notifications(self, date, slots, booking_number, amount):
        today_date = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
        notification_date = datetime.datetime.strptime(date, self.mbs.date_format)
        new_booking_only = True

        # If booking date is today's, send to all registered numbers
        if today_date.date() == notification_date.date():
            new_booking_only = False

        mobile_numbers = self.db_service.get_notification_eligible_numbers(
            new_booking_only
        )
        for mobile_number in mobile_numbers:
            self.api_service.send_message_request(
                tb.build(
                    mobile=mobile_number,
                    template_name="new_booking_notification",
                    parameters=[
                        tb.get_text_parameter(date),
                        tb.get_text_parameter(slots),
                        tb.get_text_parameter(
                            f"+{booking_number}, {self.db_service.get_user_details(booking_number) or ""}"),
                        tb.get_text_parameter(amount),
                    ]
                )
            )

    """
    Send daily booking notification at 6 AM, 12 noon, 6 PM 
    """

    def send_scheduled_notifications(self):
        mobile_numbers = self.db_service.get_notification_eligible_numbers(
            new_booking_only=False
        )
        today_date = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
        formatted_date = today_date.strftime(self.mbs.date_format)
        bookings = self.db_service.get_confirmed_bookings(formatted_date)
        if not bookings or len(bookings) == 0:
            final_message = "No bookings confirmed yet for today."
        else:
            final_message = "    --------------------------------------------------------------    ".join(
                [
                    f"_*BOOKING {ind + 1}:*_ +{booking.mobile}, {self.db_service.get_user_details(booking.mobile) or ""} --> {',   '.join([self.slots.get(slot).get("title") for slot in booking.slots.sort()])}"
                    for ind, booking in enumerate(bookings)
                ])
        for mobile_number in mobile_numbers:
            self.api_service.send_message_request(
                tb.build(
                    mobile=mobile_number,
                    template_name="scheduled_booking_notification",
                    parameters=[
                        tb.get_text_parameter(formatted_date),
                        tb.get_text_parameter(final_message)
                    ]
                )
            )

    def send_upcoming_booking_notification(self):
        today_date = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
        formatted_date = today_date.strftime(self.mbs.date_format)
        hour = today_date.hour + 1
        bookings = self.db_service.get_confirmed_bookings(formatted_date)
        for booking in bookings:
            first_slot = sorted(booking.slots)[0]
            if self.slots.get(first_slot).get("start_hour") == hour:
                name = self.db_service.get_user_details(booking.mobile)
                hour_12_format = datetime.datetime.strptime(str(hour), "%H").strftime(
                    "%I:%M %p")
                Logger.info(f"Sending notification for upcoming booking {booking}")
                self.api_service.send_message_request(
                    tb.build(
                        mobile=booking.mobile,
                        template_name=self.secrets.get(
                            "TEMPLATE_NAME_UPCOMING_BOOKING_NOTIFICATION"
                        ),
                        parameters=[
                            tb.get_text_parameter(name),
                            tb.get_text_parameter(f"{hour_12_format}")

                        ],
                        header=[tb.get_image_parameter(self.secrets.get(
                                "IMAGE_URL_UPCOMING_BOOKING_NOTIFICATION")
                        )
                        ]
                    )
                )
