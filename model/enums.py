import enum


class InteractiveRequestType(enum.Enum):
    GOTO_MAIN = 0
    MONTH_SELECTED = 1
    DATE_SELECTED = 2
    SLOT_SELECTED = 3
    ADDITIONAL_SLOT = 4
    CONFIRMED = 5


class Day(enum.Enum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


class Month(enum.Enum):
    January = 1
    February = 2
    March = 3
    April = 4
    May = 5
    June = 6
    July = 7
    August = 8
    September = 9
    October = 10
    November = 11
    December = 12


class Slot(enum.Enum):
    S5 = "5 AM - 6 AM"
    S6 = "6 AM - 7 AM"
    S7 = "7 AM - 8 AM"
    S8 = "8 AM - 9 AM"
    S9 = "9 AM - 10 AM"
    S10 = "10 AM - 11 AM"
    S11 = "11 AM - 12 PM"
    S12 = "12 PM - 1 PM"
    S13 = "1 PM - 2 PM"
    S14 = "2 PM - 3 PM"
    S15 = "3 PM - 4 PM"
    S16 = "4 PM - 5 PM"
    S17 = "5 PM - 6 PM"
    S18 = "6 PM - 7 PM"
    S19 = "7 PM - 8 PM"
    S20 = "8 PM - 9 PM"
    S21 = "9 PM - 10 PM"
    S22 = "10 PM - 11 PM"
    S23 = "11 PM - 12 PM"
    S24 = "12 PM - 1 AM"


class Screen(enum.Enum):
    DATE_SELECTION = "DATE_SELECTION"
    SLOT_SELECTION = "SLOT_SELECTION"
    BOOKING_CONFIRMATION = "BOOKING_CONFIRMATION"
    PAYMENT_CONFIRMATION = "PAYMENT_CONFIRMATION"
    SUCCESS = "SUCCESS"

class MessageType(enum.Enum):
    INTERACTIVE = "interactive"
    TEXT = "text"
    NFM_REPLY = "nfm_reply"
