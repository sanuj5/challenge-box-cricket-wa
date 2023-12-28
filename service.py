import datetime
import datetime
import json
import uuid

from phonepe.sdk.pg.env import Env

from db import DBService
from message_builder_service import MessageBuilderService
from model.enums import InteractiveRequestType, Screen
from model.flow import FlowResponse, FlowRequest
from model.interactive_flow_message_reply import InteractiveFlowMessageReply
from model.webhook_interactive import Message as InteractiveWebhookMessage
from model.webook_text import Message as TextWebhookMessage
from payment.phone_pe import PaymentGateway
from whatsapp_api import WhatsappApi


class BoxService:
    def __init__(self):
        self.db_service = DBService()
        self.slots, self.revers_slots_mapping = self.db_service.get_all_slots()
        secrets = self.db_service.get_all_secrets()
        self.api_service = WhatsappApi(secrets.get("WA_API_TOKEN"),
                                       secrets.get("MOBILE_ID"))
        self.flow_id = secrets.get("FLOW_ID")
        self.mbs = MessageBuilderService()
        self.payment_service = PaymentGateway(merchant_id=secrets.get("MERCHANT_ID"),
                                              salt_key=secrets.get("PROD_SALT_KEY"),
                                              salt_index=secrets.get("SALT_INDEX"),
                                              env=Env.PROD)

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
        amount = response.get("amount")
        print(f"Pending payment of amount 100")
        return_message = self.mbs.get_final_text_message(
            mobile,
            "",
            """Please make payment by clicking below link to confirm your booking. 

https://tinyurl.com/558966ej?tx=1234"""
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
                                               tz=datetime.timezone.utc)
        response['selected_date'] = f'{date.strftime(self.mbs.date_format)}'
        #  TODO check available slots
        response['slots'] = [{"id": str(key), "title": value} for key, value in
                             self.slots.items()]
        return response, Screen.SLOT_SELECTION.value

    def process_slot_screen_data(self, flow_request):
        date_selected = flow_request.data.get("selected_date")
        date = datetime.datetime.strptime(date_selected, self.mbs.date_format)
        slots_selected = flow_request.data.get("slots")  # '8', '8 AM - 9 AM'
        response = dict()
        if not slots_selected or len(slots_selected) == 0:
            response['error_messages'] = "Please select at least 1 slot"
            return response, Screen.SLOT_SELECTION.value
        slots_title = [self.slots.get(int(slot)) for slot in slots_selected]
        response['selected_date'] = f"{date_selected}"
        response['slots'] = f"{',  '.join(slots_title)}"
        response['amount'] = "100"
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
        print(f"Response validation {validated_response}")
        if validated_response:
            return_message = self.mbs.get_final_text_message(
                "918390903001",
                "",
                "Your booking is confirmed"
            )
        else:
            return_message = self.mbs.get_final_text_message(
                "918390903001",
                "",
                "Some error has occurred while processing your request."
            )
        self.api_service.send_post_request(return_message)

    def generate_payment_link(self, amount, transaction_id):
        return self.payment_service.generate_payment_link(
            amount, str(uuid.uuid4())[:-2]
        )
