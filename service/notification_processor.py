import datetime

import pytz

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
                        tb.get_text_parameter(booking_number),
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
            final_message = "\n".join([
                f"""
    {booking.amount}
    {', '.join([self.slots.get(slot).get("title") for slot in booking.slots])}
    {booking.amount}
    """
                for booking in bookings
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