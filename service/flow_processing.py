import datetime
from abc import abstractmethod
from functools import cmp_to_key

import pytz

from model.enums import Screen
from model.flow import FlowResponse
from service.base_message_processor import BaseProcessor


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

    def exists_pending_booking(self, token):
        mobile = self.db_service.get_mobile_token_mapping(token).get(token)
        return self.db_service.get_pending_booking(mobile=mobile)


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
        formatted_date = f'{date.strftime(self.mbs.date_format)}'

        if self.exists_pending_booking(message.flow_token):
            response['success'] = "false"
            return FlowResponse(data=response, screen=Screen.SUCCESS.value)
        response['slots'] = self.get_available_slots(formatted_date)
        response['selected_date'] = formatted_date
        response['error_messages'] = ""
        response['show_error_message'] = False
        return FlowResponse(data=response, screen=Screen.SLOT_SELECTION.value)


class SlotScreenProcessor(BaseFlowRequestProcessor):

    def __init__(self, db_service):
        super().__init__(db_service)

    def process_flow_request(self, message, *args, **kwargs) -> FlowResponse:
        date_selected = message.data.get("selected_date")
        token = message.flow_token
        date = datetime.datetime.strptime(date_selected, self.mbs.date_format)
        today_date = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
        current_hour = today_date.hour
        slots_selected = message.data.get("slots")
        response = dict()
        error = False
        if self.exists_pending_booking(message.flow_token):
            response['success'] = "false"
            return FlowResponse(data=response, screen=Screen.SUCCESS.value)
        if not slots_selected or len(slots_selected) == 0:
            error = True
            response['error_messages'] = "Please select at least 1 slot"

        booked_slots = self.db_service.get_reserved_slots(date_selected)
        for slot in slots_selected:
            slot_details = self.slots.get(slot)
            if booked_slots.get(slot) or (
                    (today_date.date() == date.date()
                     and slot_details.get("start_hour") <= current_hour
                     and slot_details.get("start_hour") > 4)):
                error = True
                response[
                    'error_messages'] = f"Slot {self.slots.get(slot).get("title")} is unavailable. Please select different slot."
                break

        if error:
            response['selected_date'] = date_selected
            response['show_error_message'] = True
            response['slots'] = self.get_available_slots(date_selected)
            return FlowResponse(data=response, screen=Screen.SLOT_SELECTION.value)

        sorted_array = sorted([self.slots.get(slot) for slot in slots_selected], key=cmp_to_key(lambda x, y: x.get("sort_order") - y.get("sort_order")))
        slots_title = [slot.get("title") for slot in sorted_array]
        total_amount = sum(
            [self.slots.get(slot).get("price") for slot in slots_selected])
        response['selected_date'] = f"{date_selected}"
        response['slots_title'] = f"{', '.join(slots_title)}"
        response['slots'] = f"{', '.join(slots_selected)}"
        response['amount'] = f"₹ {total_amount}/-"
        response['token'] = token
        return FlowResponse(data=response, screen=Screen.BOOKING_CONFIRMATION.value)

    # def overlapping_slots(self, slots_selected):
    #     hours = dict()
    #     for slot in slots_selected:
    #         c_slot = self.slots.get(slot)
    #         start_hour = c_slot.get("start_hour")
    #         end_hour = c_slot.get("end_hour")
    #         # Below will break when slot range goes across multiple days
    #         while start_hour < end_hour:
    #             if hours.get(start_hour):
    #                 return True
    #             hours[start_hour] = True
    #             start_hour += 1
    #     return False


class BookingConfirmationProcessor(BaseFlowRequestProcessor):

    def __init__(self, db_service):
        super().__init__(db_service)

    def process_flow_request(self, message, *args, **kwargs) -> FlowResponse:
        date_selected = message.data.get("selected_date")
        token = message.flow_token
        slots = message.data.get("slots").split(",")
        amount = message.data.get("amount")
        response = dict()
        if self.exists_pending_booking(message.flow_token):
            response['success'] = "false"
            return FlowResponse(data=response, screen=Screen.SUCCESS.value)
        response['selected_date'] = date_selected
        response['slots'] = message.data.get("slots")
        response['amount'] = amount
        response['token'] = token
        response['success'] = "true"
        return FlowResponse(data=response, screen=Screen.SUCCESS.value)
