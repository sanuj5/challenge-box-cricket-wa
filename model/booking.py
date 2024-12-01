from dataclasses import dataclass

from model.enums import Month, Day

@dataclass
class Booking:
    def __init__(self, date, slots, amount, mobile, token):
        self.date = date
        self.slots = slots
        self.amount = amount
        self.mobile = mobile
        self.token = token

    @staticmethod
    def create_booking(confirmed_bookings):
        bookings: list[Booking] = list()
        for booking in confirmed_bookings:
            b: dict = booking.to_dict()
            bookings.append(
                Booking(
                    date=b.get("date"),
                    slots=b.get("slots"),
                    amount=b.get("amount"),
                    token=b.get("token"),
                    mobile=b.get("mobile")
                )
            )
        return bookings
