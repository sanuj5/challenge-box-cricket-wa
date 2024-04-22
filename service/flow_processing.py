import datetime
from abc import abstractmethod

import pytz

from logger import Logger
from service.base_message_processor import BaseProcessor
from model.enums import Screen
from model.flow import FlowResponse


class FlowFactory:
    def __init__(self, db_service):
        self.date_screen_processor = DateScreenProcessor(db_service)
        self.slot_screen_processor = SlotScreenProcessor(db_service)
        self.booking_confirmation_processor = BookingConfirmationProcessor(db_service)

    def process(self, message, screen: Screen):
        match screen:
            case Screen.DATE_SELECTION:
                service = self.date_screen_processor
            case Screen.SLOT_SELECTION:
                service = self.slot_screen_processor
            case Screen.BOOKING_CONFIRMATION:
                service = self.booking_confirmation_processor
            case _:
                raise ValueError("Invalid screen")
        return service.process_flow_request(message)


class BaseFlowRequestProcessor(BaseProcessor):
    def __init__(self, db_service):
        super().__init__(db_service)

    @abstractmethod
    def process_flow_request(self, message, *args, **kwargs) -> FlowResponse:
        pass


class DateScreenProcessor(BaseFlowRequestProcessor):

    def __init__(self, db_service):
        super().__init__(db_service)
    def process_flow_request(self, message, *args, **kwargs):
        date_selected = message.data.get("selected_date")
        response = dict()
        if not date_selected:
            response['error_messages'] = "Please select date"
            return response, Screen.DATE_SELECTION.value
        date = datetime.datetime.fromtimestamp(float(date_selected) / 1000,
                                               tz=pytz.timezone("Asia/Kolkata"))
        today_date = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
        weekday = date.weekday()
        slots = self.day_wise_slots.get(weekday)
        formatted_date = f'{date.strftime(self.mbs.date_format)}'
        # For current user, remove all pending bookings
        self.db_service.remove_pending_bookings()
        reserved_slots: dict = self.db_service.get_reserved_slots(formatted_date)
        evening_slot_booked = None
        for _, booking in reserved_slots.items():
            for slot in booking.get("slots"):
                booked_slot = self.slots.get(slot)
                if (booked_slot.get("start_hour") >= 18 and
                        booked_slot.get("preference") == 1):
                    evening_slot_booked = booked_slot
                    Logger.info("Evening booked slot: " + str(evening_slot_booked))
                    continue

        response['slots'] = list()
        current_hour = today_date.hour

        for slot in slots:
            if (evening_slot_booked and slot.get("start_hour") >= 18 and
                    ((slot.get("preference") == 1 and
                      slot.get("start_hour") != evening_slot_booked.get("start_hour"))
                     or
                     (slot.get("preference") == 2 and
                      evening_slot_booked.get("start_hour") <= slot.get(
                                 "start_hour") < evening_slot_booked.get("end_hour"))
                    )
            ):
                continue
            elif (not evening_slot_booked and slot.get("preference") == 2
                  and slot.get("start_hour") >= 18):
                continue
            item = {
                "id": slot.get("id"),
                "title": f'{slot.get("title")}',
                "description": f'₹ {slot.get("price")}',
                "enabled": True
            }
            if reserved_slots.get(slot.get("id")):
                item["enabled"] = False
            if (today_date.date() == date.date()
                    and slot.get("start_hour") <= current_hour):
                item["enabled"] = False
            response['slots'].append(item)
        response['selected_date'] = formatted_date
        return FlowResponse(data=response, screen=Screen.SLOT_SELECTION.value)


class SlotScreenProcessor(BaseFlowRequestProcessor):

    def __init__(self, db_service):
        super().__init__(db_service)
    def process_flow_request(self, message, *args, **kwargs) -> FlowResponse:
        date_selected = message.data.get("selected_date")
        token = message.flow_token
        date = datetime.datetime.strptime(date_selected, self.mbs.date_format)
        slots_selected = message.data.get("slots")
        response = dict()
        if not slots_selected or len(slots_selected) == 0:
            response['error_messages'] = "Please select at least 1 slot"
            return FlowResponse(data=response, screen=Screen.SLOT_SELECTION.value)
        slots_title = [self.slots.get(slot).get("title") for slot in slots_selected]
        total_amount = sum(
            [self.slots.get(slot).get("price") for slot in slots_selected])
        response['selected_date'] = f"{date_selected}"
        response['slots_title'] = f"{', '.join(slots_title)}"
        response['slots'] = f"{', '.join(slots_selected)}"
        response['amount'] = f"₹ {total_amount}/-"
        response['token'] = token
        response['error_messages'] = {}
        return FlowResponse(data=response, screen=Screen.BOOKING_CONFIRMATION.value)


class BookingConfirmationProcessor(BaseFlowRequestProcessor):

    def __init__(self, db_service):
        super().__init__(db_service)
    def process_flow_request(self, message, *args, **kwargs) -> FlowResponse:
        date_selected = message.data.get("selected_date")
        token = message.flow_token
        slots = message.data.get("slots").split(",")
        amount = message.data.get("amount")
        response = dict()
        response['selected_date'] = date_selected
        response['slots'] = message.data.get("slots")
        response['amount'] = amount
        response['token'] = token
        return FlowResponse(data=response, screen=Screen.SUCCESS.value)
