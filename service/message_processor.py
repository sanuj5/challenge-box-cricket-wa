import json
import uuid
from abc import abstractmethod

from service.base_message_processor import BaseProcessor
from logger import Logger
from model.enums import InteractiveRequestType, MessageType
from model.interactive_flow_message_reply import InteractiveFlowMessageReply, \
    InteractiveFlowReply
from model.webhook_interactive import Message as InteractiveMessage, Interactive
from model.webook_text import Message as TextMessage, Text


class MessageFactory:
    def __init__(self):
        self.text_message_processor = TextMessageProcessor()
        self.interactive_message_processor = InteractiveMessageProcessor()
        self.nfm_reply_processor = NfmMessageProcessor()

    def process(self, message, message_type: MessageType):
        match message_type:
            case MessageType.TEXT:
                message_service = self.text_message_processor
            case MessageType.INTERACTIVE:
                message_service = self.interactive_message_processor
            case MessageType.NFM_REPLY:
                message_service = self.nfm_reply_processor
            case _:
                return "Message type not supported", 200
        message_service.process_message(message)
        return "", 200


class BaseMessageProcessor(BaseProcessor):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def process_message(self, message, *args, **kwargs):
        pass

    @staticmethod
    def parse_message(param, message_type):
        if message_type == MessageType.TEXT:
            return TextMessage(
                id=param.get("id"),
                message_from=param.get("from"),
                timestamp=param.get("timestamp"),
                text=Text(**param.get("text")),
                type=param.get("type")
            )
        if message_type == MessageType.INTERACTIVE:
            return InteractiveMessage(
                id=param.get("id"),
                message_from=param.get("from"),
                timestamp=param.get("timestamp"),
                interactive=Interactive(**param.get("interactive")),
                type=param.get("type")
            )
        if message_type == MessageType.NFM_REPLY:
            return InteractiveFlowMessageReply(
                context=param.get("context"),
                id=param.get("id"),
                message_from=param.get("from"),
                timestamp=param.get("timestamp"),
                interactive=InteractiveFlowReply(**param.get("interactive")),
                type=param.get("type")
            )


class TextMessageProcessor(BaseMessageProcessor):
    def __init__(self):
        super().__init__()

    def process_message(self, message, *args, **kwargs):
        if not message:
            raise ValueError("Missing parameter request_body")

        mobile = message.message_from
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


class InteractiveMessageProcessor(BaseMessageProcessor):
    def __init__(self):
        super().__init__()

    def process_message(self, message, *args, **kwargs):
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


class NfmMessageProcessor(BaseMessageProcessor):
    def __init__(self):
        super().__init__()

    def process_message(self, message, *args, **kwargs):
        mobile = message.message_from
        response = json.loads(message.interactive.nfm_reply.get("response_json"))
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
                "Request is invalid or expired. "
                "Please start the booking again by sending 'Hi'."
            )
        else:
            self.db_service.create_booking(
                mobile, token, total_amount, date,
                [slot.strip() for slot in slots_id.split(",")]
            )
            return_message = self.mbs.get_interactive_payment_message_gw(
                mobile=mobile,
                payment_amount=total_amount,
                slots=[slot.strip() for slot in slots_id.split(",")],
                reference_id=token,
                message_body=f"""
Almost there for your below booking!
Date: {date}
Slots: {slots_title}

Please pay using below link!
"""
            )
        #     return_message = self.mbs.get_final_text_message(
        #         mobile,
        #         "",
        #         f"""Almost there for your below booking!
        #
        # Date: {date}
        # Slots: {slots_title}
        # Amount: ₹ {total_amount}/-
        #
        # Please make payment by clicking below link to confirm your booking.
        #
        # https://challengecricket.in/api/pay?tx={token}
        #
        # If booking is not done in 10 minutes, it will be cancelled.
        # """
        #     )
        self.api_service.send_post_request(return_message)
