import base64
import datetime
import json
import uuid

import pytz
# import atexit
# from apscheduler.schedulers.background import BackgroundScheduler
from phonepe.sdk.pg.env import Env
from db import DBService
from exceptions import InvalidStateException
from message_builder_service import MessageBuilderService
from model.enums import InteractiveRequestType, Screen
from model.flow import FlowResponse, FlowRequest
from model.interactive_flow_message_reply import InteractiveFlowMessageReply
from model.webhook_interactive import Message as InteractiveWebhookMessage
from model.webook_text import Message as TextWebhookMessage
from payment.phone_pe import PaymentGateway
from whatsapp_api import WhatsappApi
from logger import Logger


class BoxService:
    def __init__(self):
        self.db_service = DBService()
        self.slots, self.day_wise_slots = self.db_service.get_all_slots()
        secrets = self.db_service.get_all_secrets()
        self.api_service = WhatsappApi(secrets.get("WA_API_TOKEN"),
                                       secrets.get("MOBILE_ID"))
        self.flow_id = secrets.get("FLOW_ID")
        self.mbs = MessageBuilderService()
        self.payment_service = PaymentGateway(merchant_id=secrets.get("MERCHANT_ID"),
                                              salt_key=secrets.get("PROD_SALT_KEY"),
                                              salt_index=secrets.get("SALT_INDEX"),
                                              env=Env.PROD)

        # scheduler = BackgroundScheduler()
        # scheduler.add_job(self.remove_pending_bookings, 'interval', seconds=5)
        # scheduler.start()
        # atexit.register(lambda: scheduler.shutdown())

    def process_interactive_message(self, message: InteractiveWebhookMessage):
        mobile = message.message_from
        request_type = InteractiveRequestType.GOTO_MAIN
        return_message = None
        if request_type == InteractiveRequestType.GOTO_MAIN:
            return_message = self.mbs.get_interactive_message(
                mobile, "Booking",
                "Select Month",
                list()
            )
        elif request_type == InteractiveRequestType.CONFIRMED:
            return_message = self.mbs.get_final_text_message(
                mobile,
                "",
                "Your booking is confirmed. Please send hi again to start new booking."
            )
        self.api_service.send_post_request(return_message)

    def process_text_message(self, request_body: TextWebhookMessage):
        #  TODO add view booking option
        mobile = request_body.message_from
        flow_token = str(uuid.uuid4())[:-2].replace("-", "")
        self.db_service.save_flow_token(mobile, flow_token)
        return_message = self.mbs.get_interactive_flow_message(
            mobile,
            "Click below to start booking",
            self.mbs.get_initial_screen_param(
                self.flow_id, flow_token
            )
        )
        self.api_service.send_post_request(return_message)

    def process_nfm_reply_message(self, nfm_message: InteractiveFlowMessageReply):
        mobile = nfm_message.message_from
        response = json.loads(nfm_message.interactive.nfm_reply.get("response_json"))
        Logger.info(f"nfm reply: {response}")
        amount = response.get("amount")
        token = response.get("token")
        slots_id = response.get("slots")
        date = response.get("selected_date")
        slots_title = ", ".join([self.slots.get(slot.strip()).get("title")
                                 for slot in slots_id.split(',')])
        total_amount = sum(
            [self.slots.get(slot.strip()).get("price") for slot in slots_id.split(',')])
        Logger.info(f"Pending payment of amount {total_amount}")
        pending_booking_token = self.db_service.get_mobile_token_mapping(token)
        if not pending_booking_token or pending_booking_token.get(token) != mobile:
            return_message = self.mbs.get_final_text_message(
                mobile,
                "",
                "Request token is invalid or expired. "
                "Please start the booking again."
            )
        else:
            self.db_service.create_booking(
                mobile, token, total_amount, date,
                [slot.strip() for slot in slots_id.split(",")]
            )
            return_message = self.mbs.get_final_text_message(
                mobile,
                "",
                f"""Almost there for your below booking!

Date: {date}
Slots: {slots_title}
Amount: ₹ {total_amount}/-

Please make payment by clicking below link to confirm your booking. 

https://challengecricket.in/api/pay?tx={token}

If booking is not done in 10 minutes, it will be cancelled.
"""
            )
        self.api_service.send_post_request(return_message)

    def process_flow_request(self, input_data):
        flow_request = FlowRequest(**json.loads(input_data))
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
        date_selected = flow_request.data.get("selected_date")
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
            print(item)
        response['selected_date'] = formatted_date
        return response, Screen.SLOT_SELECTION.value

    def process_slot_screen_data(self, flow_request):
        date_selected = flow_request.data.get("selected_date")
        token = flow_request.flow_token
        date = datetime.datetime.strptime(date_selected, self.mbs.date_format)
        slots_selected = flow_request.data.get("slots")
        response = dict()
        if not slots_selected or len(slots_selected) == 0:
            response['error_messages'] = "Please select at least 1 slot"
            return response, Screen.SLOT_SELECTION.value
        slots_title = [self.slots.get(slot).get("title") for slot in slots_selected]
        total_amount = sum(
            [self.slots.get(slot).get("price") for slot in slots_selected])
        response['selected_date'] = f"{date_selected}"
        response['slots_title'] = f"{', '.join(slots_title)}"
        response['slots'] = f"{', '.join(slots_selected)}"
        response['amount'] = f"₹ {total_amount}/-"
        response['token'] = token
        response['error_messages'] = {}
        return response, Screen.BOOKING_CONFIRMATION.value

    def process_booking_confirmation_screen_data(self, flow_request):
        date_selected = flow_request.data.get("selected_date")
        token = flow_request.flow_token
        slots = flow_request.data.get("slots").split(",")
        amount = flow_request.data.get("amount")
        response = dict()
        response['selected_date'] = date_selected
        response['slots'] = flow_request.data.get("slots")
        response['amount'] = amount
        response['token'] = token
        return response, Screen.SUCCESS.value

    def validate_payment_response(self, header, response):
        # TODO get mobile number from response transaction ID
        validated_response = self.payment_service.validate_response(header, response)
        Logger.info(f"Response validation {validated_response}")
        existing_booking = dict()
        if validated_response:
            response_string = base64.b64decode(
                json.loads(response).get("response"))
            Logger.info(response_string)
            response_dict = json.loads(response_string)
            transaction_id = response_dict.get("data").get("merchantTransactionId")
            existing_booking = self.db_service.get_pending_booking(transaction_id)
            if response_dict.get("code") == "PAYMENT_SUCCESS":
                amount = response_dict.get("data").get("amount")
                # TODO validate amount

                self.db_service.confirm_booking(
                    existing_booking, transaction_id, response_dict
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
        self.api_service.send_post_request(return_message)

    def generate_payment_link(self, amount, transaction_id):
        self.db_service.remove_pending_bookings()
        if not self.db_service.get_mobile_token_mapping(transaction_id):
            raise InvalidStateException("Invalid transaction token")
        elif not self.db_service.get_pending_booking(transaction_id):
            raise InvalidStateException("<h1>This payment link is expired. "
                                        "Please start new booking from WhatsApp.</h1>")
        else:
            return self.payment_service.generate_payment_link(
                amount, transaction_id
            )


if __name__ == '__main__':
    service = BoxService()
    # service.db_service.get_reserved_slots("13 Jan 2024")
    service.generate_payment_link(200, "9725dc452770493bbb26c7b0869378")
