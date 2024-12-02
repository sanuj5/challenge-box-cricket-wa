import datetime
import json
import re
import uuid
from abc import abstractmethod
from functools import cmp_to_key

from external.payment import BasePayment
from model.payment_status import Payment, PaymentStatus
from service.base_message_processor import BaseProcessor
from logger import Logger
from model.enums import InteractiveRequestType, MessageType
from model.interactive_flow_message_reply import InteractiveFlowMessageReply, \
    InteractiveFlowReply
from model.webhook_interactive import Message as InteractiveMessage, Interactive, \
    ButtonReply
from model.webook_text import Message as TextMessage, Text


class MessageFactory:
    def __init__(self, db_service, payment_service):
        self.text_message_processor = TextMessageProcessor(db_service)
        self.interactive_message_processor = InteractiveMessageProcessor(db_service)
        self.nfm_reply_processor = NfmMessageProcessor(db_service, payment_service)
        self.tournament_nfm_replay_processor = TournamentNfmMessageProcessor(db_service, payment_service)

    def process(self, message, message_type: MessageType, *args, **kwargs):
        match message_type:
            case MessageType.TEXT:
                message_service = self.text_message_processor
            case MessageType.INTERACTIVE:
                message_service = self.interactive_message_processor
            case MessageType.NFM_REPLY:
                token = json.loads(
                    message.interactive.nfm_reply.get("response_json")).get("flow_token")
                if token.startswith("TT-"):
                    message_service = self.tournament_nfm_replay_processor
                else:
                    message_service = self.nfm_reply_processor
            case _:
                return "Message type not supported", 200
        message_service.process_message(message, *args, **kwargs)
        return "", 200


class BaseMessageProcessor(BaseProcessor):
    def __init__(self, db_service):
        super().__init__(db_service)

    @abstractmethod
    def process_message(self, message, *args, **kwargs):
        pass

    def is_under_maintenance(self, mobile) -> bool:
        if (
                self.secrets.get('UNDER_MAINTENANCE')
                and mobile not in self.secrets.get("CBC_TEST_NUMBERS")
        ):
            self.api_service.send_message_request(
                self.mbs.get_final_text_message(
                    mobile=mobile,
                    _id=str(uuid.uuid4()),
                    body=self.secrets.get(
                        'UNDER_MAINTENANCE_MESSAGE') or "System Under Maintenance. Please try later."
                )
            )
            return True
        return False

    def validate_country(self, mobile) -> bool:
        if mobile and mobile.startsWith("91"):
            return True
        self.api_service.send_message_request(
            self.mbs.get_final_text_message(
                mobile=mobile,
                _id=str(uuid.uuid4()),
                body="Yikes! We are currently not serving this country."
            )
        )

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
                interactive=Interactive(
                    ButtonReply(**param.get("interactive").get("button_reply")),
                    param.get("interactive").get("type")
                ),
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
        if message_type == MessageType.PAYMENT:
            return PaymentStatus(
                id=param.get("id"),
                status=param.get("status"),
                timestamp=param.get("timestamp"),
                recipient_id=param.get("recipient_id"),
                type=param.get("type"),
                payment=Payment(**param.get("payment"))
            )

    def get_payment_message(self,
                            mobile,
                            payment_message,
                            token,
                            total_amount,
                            amount_offset,
                            payment_service):
        if self.secrets.get("PAYMENT_TYPE") == "PAYMENT_GATEWAY":
            return_message = self.mbs.get_interactive_payment_message_gw(
                mobile=mobile,
                payment_amount=total_amount * amount_offset,
                reference_id=token,
                amount_offset=100,
                message_body=payment_message
            )
        elif self.secrets.get("PAYMENT_TYPE") == "PAYMENT_GATEWAY_UPI":
            return_message = self.mbs.get_interactive_payment_message(
                mobile=mobile,
                payment_amount=total_amount * amount_offset,
                reference_id=token,
                amount_offset=amount_offset,
                message_body=payment_message,
                payment_configuration=self.secrets.get(
                    "WA_UPI_PAYMENT_CONFIGURATION_NAME"
                )
            )
        elif self.secrets.get("PAYMENT_TYPE") == "DIRECT_PAYMENT_LINK":
            payment_link = payment_service.generate_payment_link(
                amount=total_amount * amount_offset,
                unique_transaction_id=token
            )

            payment_message = f"""
{payment_message}

Pay by clicking this link: 
{payment_link}
"""
            return_message = self.mbs.get_final_text_message(
                mobile=mobile,
                body=payment_message
            )
        else:
            payment_link = payment_service.generate_payment_link(
                amount=total_amount * amount_offset,
                unique_transaction_id=token
            )
            return_message = self.mbs.get_interactive_payment_message(
                mobile=mobile,
                payment_amount=total_amount * amount_offset,
                reference_id=token,
                amount_offset=amount_offset,
                message_body=payment_message,
                payment_uri=payment_link
            )
        return return_message


class TextMessageProcessor(BaseMessageProcessor):
    def __init__(self, db_service):
        super().__init__(db_service)

    def process_message(self, message, *args, **kwargs):
        if not message:
            raise ValueError("Missing parameter request_body")
        mobile = message.message_from
        contact = kwargs.get("contact")
        name = (contact and contact.get("profile") and contact.get("profile").get("name")) or ""
        self.db_service.update_user_details(mobile, name)

        if self.is_under_maintenance(mobile):
            return
        self.api_service.send_message_request(
            self.mbs.get_interactive_message(
                mobile,
                f"Hi {name}, click below to view existing booking or create new booking."
            )
            if not self.secrets.get('ENABLE_TOURNAMENT_REGISTRATION')
            else
            self.mbs.get_interactive_message_with_tournament(
                mobile,
                f"Hi {name}, click below to register for tournament, view existing booking or create new booking."
            )
        )


"""
This class processes InteractiveMessage response.
New booking --> Start Flow request for new booking
View bookings --> Get existing bookings of yesterday, today and all future days 
Tournament registration --> Start Flow request for tournament
"""


class InteractiveMessageProcessor(BaseMessageProcessor):
    def __init__(self, db_service):
        super().__init__(db_service)

    def process_message(self, message, *args, **kwargs):
        mobile = message.message_from
        if self.is_under_maintenance(mobile):
            return
        request_type = InteractiveRequestType(message.interactive.button_reply.id)
        return_message = None
        if request_type == InteractiveRequestType.VIEW_BOOKING:
            return_message = self.get_view_booking_message(mobile)
        elif request_type == InteractiveRequestType.NEW_BOOKING:
            return_message = self.get_new_booking_message(mobile)
        elif request_type == InteractiveRequestType.TOURNAMENT_REGISTRATION:
            return_message = self.get_tournament_registration_message(mobile)
        self.api_service.send_message_request(return_message)

    def get_new_booking_message(self, mobile):
        pending_booking = self.db_service.get_pending_booking(mobile=mobile)
        if pending_booking:
            return self.mbs.get_interactive_message(
                mobile,
                "Previous booking still in progress. If you have already made the payment, wait for some time till we confirm your payment."
            )
        flow_token = str(uuid.uuid4())[:-2].replace("-", "")
        self.db_service.save_flow_token(mobile, flow_token)
        return self.mbs.get_interactive_flow_message(
            mobile,
            "Click below to start new booking",
            self.mbs.get_initial_screen_param(
                self.flow_id, flow_token, self.flow_mode
            )
        )

    def get_view_booking_message(self, mobile):
        today_date = datetime.datetime.now() \
                         .replace(hour=0, minute=0, second=0, microsecond=0) \
                     - datetime.timedelta(days=1)
        bookings = self.db_service.get_user_future_bookings(mobile, today_date)
        if not bookings or len(bookings) == 0:
            message = "No upcoming booking found."
        else:
            message = ""
            for booking in bookings:
                message = f"""{message}
Date: {booking.date}
Slots: {', '.join([slot.get("title") for slot in sorted([self.slots.get(slot) for slot in booking.slots],key = lambda x: x.get("sort_order"))])}
Amount: {booking.amount}
"""
        return_message = self.mbs.get_final_text_message(mobile, "", message)
        return return_message

    def get_tournament_registration_message(self, mobile):
        existing_registration = self.db_service.get_tournament_registration(mobile=mobile)
        if existing_registration and existing_registration.get("payment_successful"):
            return self.mbs.get_final_text_message(
                mobile=mobile,
                body=f"""
You have already registered your team {existing_registration.get('team_name')}.

For additional team, please register using different mobile number.
"""
            )
        flow_token = f'TT-{str(uuid.uuid4())[:-2].replace("-", "")}'
        self.db_service.save_flow_token(mobile, flow_token)
        return self.mbs.get_interactive_flow_message(
            mobile,
            "Click below to register your team for box cricket tournament",
            self.mbs.get_tournament_initial_screen_param(
                self.tournament_flow_id, flow_token
                # , self.flow_mode  TODO
            )
        )


"""
This class processes user message post flow screen confirmation (NFM Reply Message).
1. A new pending booking will be created once user clicks confirm button
2. Sends whatsapp message of type PaymentGateway to user
"""


class NfmMessageProcessor(BaseMessageProcessor):
    def __init__(self, db_service, payment_service):
        super().__init__(db_service)
        self.amount_offset = self.secrets.get("AMOUNT_OFFSET") or 100
        self.payment_service: BasePayment = payment_service

    def process_message(self, message, *args, **kwargs):
        Logger.info(f"Processing nfm reply message.")
        mobile = message.message_from
        if self.is_under_maintenance(mobile):
            return
        response = json.loads(message.interactive.nfm_reply.get("response_json"))
        success = response.get("success")
        if success == "false":
            return_message = self.mbs.get_final_text_message(
                mobile=mobile,
                body=f"You already have another booking in progress. Please complete it or wait for some time to complete it."
            )
            self.api_service.send_message_request(data=return_message)
            return
        amount = re.findall(r'\d+', response.get("amount"))[0]
        token = response.get("token")
        slots_id = response.get("slots")
        date = response.get("selected_date")
        sorted_array = sorted([self.slots.get(slot.strip()) for slot in slots_id.split(',')],
                              key=cmp_to_key(lambda x, y: x.get("sort_order") - y.get(
                                  "sort_order")))
        slots_title = ", ".join([slot.get("title") for slot in sorted_array])
        total_amount = sum(
            [self.slots.get(slot.strip()).get("price") for slot in slots_id.split(',')])
        Logger.info(f"Pending payment amount {total_amount}, actual amount {amount}")
        pending_booking_token = self.db_service.get_mobile_token_mapping(token)
        confirmed_bookings = self.db_service.get_confirmed_bookings(date)
        for booking in confirmed_bookings:
            for slot in slots_id.split(','):
                if slot.strip() in booking.slots:
                    return_message = self.mbs.get_final_text_message(
                        mobile=mobile,
                        body=f"Sorry. One of the slot is already booked. Please start new booking."
                    )
                    self.api_service.send_message_request(data=return_message)
                    return

        # Token expired below
        if not pending_booking_token or pending_booking_token.get(token) != mobile:
            return_message = self.mbs.get_final_text_message(
                mobile,
                "",
                "Request is invalid or expired. "
                "Please start the booking again by sending *Hi*."
            )
        # Check amount received from user vs amount calculated for selected slots
        elif int(amount) != total_amount:
            return_message = self.mbs.get_final_text_message(
                mobile,
                "",
                "Amount does not match."
                "Please start the booking again by sending *Hi*."
            )
        else:
            self.db_service.create_booking(
                mobile, token, total_amount, date,
                [slot.strip() for slot in slots_id.split(",")]
            )
            if mobile and mobile in self.secrets.get("CBC_TEST_NUMBERS"):
                Logger.info(f"Setting amount to {amount} for test number {mobile}")
                total_amount = total_amount // 1000
            payment_message = f"""
Date: {date} 
Slots: {slots_title}
Amount: {total_amount}
Please pay to confirm your booking. 

_Once a booking is confirmed, it cannot be canceled, and no refund will be offered in case of No-Show._
"""
            return_message = self.get_payment_message(
                mobile, payment_message, token, total_amount, self.amount_offset, self.payment_service
            )
        self.api_service.send_message_request(data=return_message)


"""
This class processes user message post flow screen confirmation (NFM Reply Message).
1. A new pending booking will be created once user clicks confirm button
2. Sends whatsapp message of type PaymentGateway to user
"""


class TournamentNfmMessageProcessor(BaseMessageProcessor):
    def __init__(self, db_service, payment_service):
        super().__init__(db_service)
        self.amount_offset = self.secrets.get("AMOUNT_OFFSET") or 100
        self.payment_service: BasePayment = payment_service

    def process_message(self, message, *args, **kwargs):
        Logger.info(f"Processing nfm reply message.")
        mobile = message.message_from
        if self.is_under_maintenance(mobile):
            return
        response = json.loads(message.interactive.nfm_reply.get("response_json"))
        success = response.get("success")
        token = response.get("flow_token")
        existing_registration = self.db_service.get_tournament_registration(token)
        if success == "false" or (
                existing_registration and existing_registration.get("payment_successful")
        ):
            return_message = self.mbs.get_final_text_message(
                mobile=mobile,
                body=f"You have already registered or have another registration in progress. Please complete it or wait for status to be reflected."
            )
            self.api_service.send_message_request(data=return_message)
            return
        amount = re.findall(r'\d+', response.get("amount"))[0]

        team_name = response.get("team_name")
        total_amount = self.db_service.get_tournament_amount()
        Logger.info(f"Pending payment amount {total_amount}, actual amount {amount}")
        # Check amount received from user vs amount set for tournament
        if int(amount) != total_amount:
            return_message = self.mbs.get_final_text_message(
                mobile,
                "",
                "Amount does not match."
                "Please start the registration again by sending *Hi*."
            )
        else:
            self.db_service.create_tournament_registration(
                mobile, token, total_amount, team_name
            )
            if mobile and mobile in self.secrets.get("CBC_TEST_NUMBERS"):
                Logger.info(f"Setting amount to {amount} for test number {mobile}")
                total_amount = total_amount // 1000
            payment_message = f"""
Team Name: {team_name}
Amount: {amount}
Please pay to confirm your registration. 

_Once a registration is confirmed, it cannot be canceled, and no refund will be offered in case of No-Show._
"""
            return_message = self.get_payment_message(
                mobile, payment_message, token, total_amount, self.amount_offset,
                self.payment_service
            )
        self.api_service.send_message_request(data=return_message)