import json
from flask import Flask, request, abort, redirect, render_template
from service.encryption_service import Encryption
from model.enums import MessageType, Screen
from model.flow import FlowRequest
from model.exceptions import InvalidStateException
from logger import Logger
from service.message_processor import MessageFactory, BaseMessageProcessor
from service.flow_processing import FlowFactory
from service.payment_processor import PaymentProcessor


class BoxBooking:

    def __init__(self):
        self.app = Flask(__name__)
        self._setup_routes()
        self.encryption_service = Encryption()
        self.flow_factory = FlowFactory()
        self.message_factory = MessageFactory()
        self.payment_processor = PaymentProcessor()

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
            rule="/api/payment",
            view_func=self.process_payment_response,
            endpoint="process_payment_response",
            methods=["POST"],
        )
        self.app.add_url_rule(
            rule="/api/razorpay/payment",
            view_func=self.process_razorpay_payment,
            endpoint="process_payment_response",
            methods=["POST"],
        )
        self.app.add_url_rule(
            rule="/api/pay",
            view_func=self.payment_redirect,
            endpoint="payment_redirect",
            methods=["GET"],
        )
        self.app.add_url_rule(
            rule="/",
            view_func=self.index_page,
            endpoint="index_page",
            methods=["GET"],
        )

    def health_check(self):
        return ""

    def index_page(self):
        return render_template('index.html')

    def payment_redirect(self):
        transaction_id = request.args.get("tx")
        Logger.info(transaction_id)
        try:
            url = self.payment_processor.generate_payment_link(200, transaction_id)
        except InvalidStateException as e:
            return str(e), 500
        if not url:
            return "Internal Server Error", 500
        return redirect(url, code=302)

    def webhook(self):
        hub_mode = request.args.get("hub.mode")
        hub_challenge = request.args.get("hub.challenge")
        hub_verify_token = request.args.get("hub.verify_token")

        if hub_mode == "subscribe" and hub_verify_token == "dc6bf63a-2b58-40b6-87b8-096b5e4e8479":
            return hub_challenge
        else:
            abort(403)

    def process_message_request(self):
        request_body = request.json
        Logger.info(request_body)
        if (request_body.get("entry") and
                request_body.get("entry")[0] and
                request_body.get("entry")[0].get("changes") and
                request_body.get("entry")[0].get("changes")[0].get("value") and
                request_body.get("entry")[0].get("changes")[0].get("value").get(
                    "messages")):
            messages = (
                request_body.get("entry")[0]
                .get("changes")[0]
                .get("value")
                .get("messages")[0]
            )
            message_type = MessageType(messages.get("type"))
            if (message_type == MessageType.INTERACTIVE
                    and messages.get("interactive").get("type")
                    == MessageType.NFM_REPLY.value):
                message_type = MessageType.NFM_REPLY
            parsed_message = BaseMessageProcessor.parse_message(messages,
                                                                  message_type)
            return self.message_factory.process(parsed_message, message_type)
        return "Message type not supported", 200

    def process_flow_request(self):
        encrypted_flow_data_b64 = request.json.get("encrypted_flow_data")
        encrypted_aes_key_b64 = request.json.get("encrypted_aes_key")
        initial_vector_b64 = request.json.get("initial_vector")
        decrypted_data, key, iv = self.encryption_service.decrypt_data(
            encrypted_flow_data_b64,
            encrypted_aes_key_b64, initial_vector_b64)
        Logger.info(decrypted_data, key, iv)
        flow_request = FlowRequest(**json.loads(decrypted_data))
        response_data = self.flow_factory.process(
            flow_request, Screen(flow_request.screen))
        response = json.dumps(response_data, indent=4, default=lambda o: o.__dict__)
        Logger.info(
            json.dumps(response_data, indent=None, default=lambda o: o.__dict__))
        return self.encryption_service.encrypt_data(response, key, iv)

    def process_payment_response(self):
        header = request.headers.get("X-VERIFY")
        response = request.get_data()
        Logger.info(f"{header} \n {response}")
        self.payment_processor.validate_payment_response(header, response)
        return "", 200

    def process_razorpay_payment(self):
        header = request.headers.get("X-Razorpay-Signature")
        response = request.get_data()
        Logger.info(f"{header} \n {response}")
        self.payment_processor.validate_payment_response(header, response)
        return "", 200


service = BoxBooking()
app = service.app

if __name__ == "__main__":
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run()
