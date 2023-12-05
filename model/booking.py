from dataclasses import dataclass

from model.enums import Month, Day

@dataclass
class Booking:
    def __init__(self, month: Month = None, day: Day = None, slot=None):
        self.month: Month = month
        self.day: Day = day
        self.slot = slot

    @staticmethod
    def create_booking(selected_id: str):
        booking = Booking()
        _id = selected_id.split("_")
        if len(_id) > 0:
            booking.month = _id[0]
        if len(_id) > 1:
            booking.day = _id[1]
        if len(_id) > 2:
            slots = _id[2:]
            if _id[-1] == 'cs' or _id[-1] == 'as':
                slots = slots[:-1]
            booking.slot = slots
        return booking
