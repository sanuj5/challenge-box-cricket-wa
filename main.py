import json
from flask import Flask, request, abort, render_template

from external.payment import PaymentFactory
from service.db import DBService
from service.encryption_service import Encryption
from model.enums import MessageType, Screen, PaymentProvider
from model.flow import FlowRequest
from model.exceptions import InvalidStateException
from logger import Logger
from service.message_processor import MessageFactory, BaseMessageProcessor
from service.flow_processing import FlowFactory
from service.notification_processor import NotificationProcessor
from service.payment_processor import PaymentProcessor


class BoxBooking:

    def __init__(self):
        self.db_service = DBService()
        self.secrets = self.db_service.get_all_secrets()
        self.app = Flask(__name__)
        self._setup_routes()
        self.encryption_service = Encryption(secrets=self.secrets)
        payment_service = PaymentFactory.get_payment_service(
            payment_provider=PaymentProvider.RAZORPAY,
            secrets=self.secrets
        )
        self.flow_factory = FlowFactory(self.db_service)
        self.message_factory = MessageFactory(self.db_service)
        self.payment_processor = PaymentProcessor(self.db_service, payment_service)
        self.notification_processor = NotificationProcessor(self.db_service)

    def _setup_routes(self):
        self.app.add_url_rule(
            rule="/api/webhook",
            view_func=self.webhook,
            endpoint="webhook",
            methods=["GET"],
        )
        self.app.add_url_rule(
            rule="/api/webhook",
            view_func=self.process_message_request,
            endpoint="process_request",
            methods=["POST"],
        )
        self.app.add_url_rule(
            rule="/api/flow",
            view_func=self.health_check,
            endpoint="health_check",
            methods=["GET"],
        )
        self.app.add_url_rule(
            rule="/api/flow",
            view_func=self.process_flow_request,
            endpoint="process_flow_request",
            methods=["POST"],
        )
        self.app.add_url_rule(
            rule="/api/razorpay/payment",
            view_func=self.process_razorpay_payment,
            endpoint="process_razorpay_payment",
            methods=["POST"],
        )
        self.app.add_url_rule(
            rule="/",
            view_func=self.index_page,
            endpoint="index_page",
            methods=["GET"],
        )

        self.app.add_url_rule(
            rule="/api/daily_booking_notification",
            view_func=self.scheduled_booking_notification,
            endpoint="scheduled_booking_notification",
            methods=["POST"],
        )

        self.app.add_url_rule(
            rule="/api/remove_pending_bookings",
            view_func=self.remove_pending_bookings,
            endpoint="remove_pending_bookings",
            methods=["POST"],
        )

        self.app.add_url_rule(
            rule="/api/upcoming_booking_notification",
            view_func=self.upcoming_booking_notification,
            endpoint="upcoming_booking_notification",
            methods=["POST"],
        )

    def remove_pending_bookings(self):
        if self.secrets.get("JOB_KEY_SECRET") != request.headers.get("X-Auth-Token"):
            return abort(401)
        self.db_service.remove_pending_bookings()
        return "OK", 200

    def upcoming_booking_notification(self):
        if self.secrets.get("JOB_KEY_SECRET") != request.headers.get("X-Auth-Token"):
            return abort(401)
        self.notification_processor.send_upcoming_booking_notification()
        return "OK", 200

    def scheduled_booking_notification(self):
        if self.secrets.get("JOB_KEY_SECRET") != request.headers.get("X-Auth-Token"):
            return abort(401)
        self.notification_processor.send_scheduled_notifications()
        return "OK", 200

    def health_check(self):
        return ""

    def index_page(self):
        return render_template('index.html')

    def webhook(self):
        hub_mode = request.args.get("hub.mode")
        hub_challenge = request.args.get("hub.challenge")
        hub_verify_token = request.args.get("hub.verify_token")

        if (hub_mode == "subscribe"
                and hub_verify_token == self.secrets.get("WA_WEBHOOK_TOKEN")):
            return hub_challenge
        else:
            abort(403)

    # TODO Authentication
    def process_message_request(self):
        request_body = request.json
        Logger.info(request_body)
        if request_body.get("action") == "ping":
            response = {
                "version": "3.0",
                "data": {
                    "status": "active"
                }
            }
            return json.dumps(response), 200
        if (request_body.get("entry") and
                request_body.get("entry")[0] and
                request_body.get("entry")[0].get("changes") and
                request_body.get("entry")[0].get("changes")[0].get("value")
        ):
            webhook_message = request_body.get("entry")[0].get("changes")[0].get(
                "value")
            if webhook_message.get("messages"):
                messages = webhook_message.get("messages")[0]
                contact = webhook_message.get("contacts")[0] if webhook_message.get("contacts") else None
                message_type = MessageType(messages.get("type"))
                # NFM_REPLY
                if (message_type == MessageType.INTERACTIVE
                        and messages.get("interactive").get("type")
                        == MessageType.NFM_REPLY.value):
                    message_type = MessageType.NFM_REPLY
                parsed_message = BaseMessageProcessor.parse_message(messages,
                                                                    message_type)
                return self.message_factory.process(
                    parsed_message,
                    message_type,
                    contact=contact
                )
            elif webhook_message.get("statuses"):
                messages = webhook_message.get("statuses")[0]
                message_type = MessageType(messages.get("type"))
                parsed_message = BaseMessageProcessor.parse_message(messages,
                                                                    message_type)
                if message_type == MessageType.PAYMENT:
                    return self.payment_processor.validate_status(parsed_message)
                else:
                    Logger.debug("Message type not yet handled")
            else:
                Logger.debug("Message type not yet handled")
        return "Message type not supported", 200


    def process_flow_request(self):
        encrypted_flow_data_b64 = request.json.get("encrypted_flow_data")
        encrypted_aes_key_b64 = request.json.get("encrypted_aes_key")
        initial_vector_b64 = request.json.get("initial_vector")
        try:
            decrypted_data, key, iv = self.encryption_service.decrypt_data(
                encrypted_flow_data_b64,
                encrypted_aes_key_b64, initial_vector_b64)
            json_data = json.loads(decrypted_data)
        except Exception as e:
            Logger.error("Encryption error {}".format(e))
            raise InvalidStateException("Invalid data provided")
        Logger.info(f"Flow request: {json_data}")
        if json_data.get("action") == "ping":
            response_data = {
                "version": "3.0",
                "data": {
                    "status": "active"
                }
            }
        else:
            flow_request = FlowRequest(**json_data)
            response_data = self.flow_factory.process(
                flow_request, Screen(flow_request.screen))
        response = json.dumps(response_data, indent=4, default=lambda o: o.__dict__)
        return self.encryption_service.encrypt_data(response, key, iv)


    """
    Not used while using Whatapp Payment Gateway API
    """


    def process_razorpay_payment(self):
        header = request.headers.get("X-Razorpay-Signature")
        response = request.data.decode()
        Logger.info(f"{header} \n {response}")
        self.payment_processor.validate_payment_response(header, response)
        return "", 200


service = BoxBooking()
app = service.app

if __name__ == "__main__":
    app.run()
