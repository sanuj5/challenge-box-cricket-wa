import calendar
import json
from datetime import datetime

from model.booking import Booking
from model.enums import InteractiveRequestType, Slot, Month, Screen
from model.flow import FlowResponse, FlowRequest
from model.interactive_message import InteractiveMessage, Interactive, Header, Body, \
    Action, Section, Row
from model.text_message import TextMessage, Text
from model.webhook_interactive import Message as InteractiveWebhookMessage
from model.webook_text import Message as TextWebhookMessage
from whatsapp_api import WhatsappApi


class BoxService:
    def __init__(self):
        self.api_service = WhatsappApi()

    def process_interactive_message(self, mobile: str,
                                    message: InteractiveWebhookMessage):
        request_type, _id, booking = self.get_request_type(message)
        print(booking.day, booking.month, booking.slot)
        return_message = None
        if request_type == InteractiveRequestType.GOTO_MAIN:
            return_message = self.get_interactive_message(mobile, "Booking",
                                                          "Select Month",
                                                          self.get_months()
                                                          )
        elif request_type == InteractiveRequestType.MONTH_SELECTED:
            return_message = self.get_interactive_message(mobile, "Booking",
                                                          "Select Date",
                                                          self.get_dates_data(
                                                              _id, booking)
                                                          )
        elif request_type == InteractiveRequestType.DATE_SELECTED:
            return_message = self.get_interactive_message(mobile, "Booking",
                                                          "Select Slot",
                                                          self.get_slot_data(
                                                              _id, booking)
                                                          )
        elif request_type == InteractiveRequestType.SLOT_SELECTED:
            return_message = self.get_interactive_message(mobile, "Booking",
                                                          "Select Date",
                                                          self.get_confirmation_data(
                                                              _id, booking)
                                                          )
        elif request_type == InteractiveRequestType.ADDITIONAL_SLOT:
            return_message = self.get_interactive_message(mobile, "Booking",
                                                          "Select Date",
                                                          self.get_slot_data(
                                                              _id, booking)
                                                          )
        elif request_type == InteractiveRequestType.CONFIRMED:
            return_message = self.get_final_text_message(mobile, _id, booking)
        self.api_service.send_post_request(return_message)

    def get_request_type(self, message: InteractiveWebhookMessage):
        list_id = message.interactive.list_reply.get("id")
        if list_id == "main":
            return InteractiveRequestType.GOTO_MAIN, list_id
        other_id = list_id.split("_")
        booking = Booking.create_booking(list_id)
        if len(other_id) == 1:
            return InteractiveRequestType.MONTH_SELECTED, list_id, booking
        elif len(other_id) == 2:
            return InteractiveRequestType.DATE_SELECTED, list_id, booking
        elif other_id[-1] == 'cs':
            return InteractiveRequestType.CONFIRMED, list_id, booking
        elif other_id[-1] == 'as':
            return InteractiveRequestType.ADDITIONAL_SLOT, list_id, booking
        else:
            return InteractiveRequestType.SLOT_SELECTED, list_id, booking

    def process_text_message(self, mobile, request_body: TextWebhookMessage):
        return_message = self.get_interactive_message(mobile, "Booking",
                                                      "Select Month",
                                                      self.get_months()
                                                      )
        self.api_service.send_post_request(return_message)

    @staticmethod
    def get_interactive_message(mobile: str,
                                message_body: str,
                                button_text: str,
                                data: list[Row]) -> InteractiveMessage:

        sections = list()
        section = Section()
        section.title = ""
        section.rows = data
        sections.append(section)

        action = Action()
        action.button = button_text
        action.sections = sections

        header = Header()
        header.type = "text"
        header.text = "CBC"

        body = Body()
        body.text = message_body

        interactive = Interactive()
        interactive.type = "list"
        interactive.header = header
        interactive.body = body
        interactive.action = action

        message = InteractiveMessage()
        message.to = mobile
        message.type = "interactive"
        message.messaging_product = "whatsapp"
        message.interactive = interactive
        return message

    @staticmethod
    def get_dates_data(_id, booking) -> list[Row]:
        month = int(booking.month)
        now = datetime.now()
        days_in_month = calendar.monthrange(now.year, month)[1]
        remaining_days = range(now.day, days_in_month)
        rows = list()
        for day in remaining_days:
            row = Row()
            row.id = f"{_id}_{day}"
            row.title = day
            rows.append(row)
        return rows

    @staticmethod
    def get_slot_data(_id, booking) -> list[Row]:
        # TODO show only remaining slots of today
        rows = list()
        for slot in list(Slot):
            row = Row()
            row.id = f"{_id}_{slot.name}"
            row.title = slot.value
            rows.append(row)
        return rows

    @staticmethod
    def get_confirmation_data(_id, booking) -> list[Row]:
        # TODO show only remaining slots of today
        rows = list()
        row1 = Row()
        row1.id = f"{_id}_as"
        row1.title = "Book Additional Slot"
        rows.append(row1)
        row2 = Row()
        row2.id = f"{_id}_cs"
        row2.title = "Confirm you booking"
        rows.append(row2)
        return rows

    @staticmethod
    def get_months() -> list[Row]:
        now = datetime.now()
        current_month = now.month
        next_month = current_month + 1
        if current_month == 12:
            next_month = 1

        rows = list()
        row1 = Row()
        row1.id = str(current_month)
        row1.title = Month(current_month).name
        rows.append(row1)
        row2 = Row()
        row2.id = str(next_month)
        row2.title = Month(next_month).name
        rows.append(row2)
        return rows

    @staticmethod
    def get_final_text_message(mobile, _id, booking):
        # TODO read data from booking
        text = Text()
        text.body = "Your booking if confirmed. Please send hi again to start new booking."
        text_message = TextMessage()
        text_message.messaging_product = "whatsapp"
        text_message.recipient_type = "individual"
        text_message.to = mobile
        text_message.type = "text"
        text_message.text = text
        return text_message

    def process_flow_request(self, input_data):
        flow_request = FlowRequest(**json.loads(input_data))
        print(flow_request)
        current_screen = Screen(flow_request.screen)
        response_data = None
        next_screen = None
        if current_screen == Screen.DATE_SELECTION:
            response_data, next_screen = self.process_date_screen_data(flow_request)
        elif current_screen == Screen.SLOT_SELECTION:
            response_data, next_screen = self.process_slot_screen_data(flow_request)
        elif current_screen == Screen.BOOKING_CONFIRMATION:
            response_data, next_screen = self.process_booking_confirmation_screen_data(
                flow_request)
        return FlowResponse(screen=next_screen, data=response_data)

    def process_date_screen_data(self, flow_request) -> (dict, str):
        response = dict()
        #  TODO check available slots
        slots = [{'id': 'slot5', 'title': '5 AM - 6 AM'},
                 {'id': 'slot6', 'title': '6 AM - 7 AM'}]
        response['slots'] = slots
        return response, Screen.SLOT_SELECTION



if __name__ == '__main__':
    service = BoxService()
    data = '{"version":"3.0","action":"data_exchange","screen":"DATE_SELECTION","data":{"selected_date":"1702425600000","form_name":"form"},"flow_token":"flows-builder-2a5dd546"}'
    service.process_flow_request(data)
