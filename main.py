import json
from types import SimpleNamespace

from flask import Flask, request, abort

from encryption_service import Encryption
from model.enums import MessageType
from model.interactive_flow_message_reply import InteractiveFlowMessageReply, \
    InteractiveFlowReply
from service import BoxService
from model.webhook_interactive import Message as InteractiveMessage, Interactive
from model.webook_text import Message as TextMessage, Text


class BoxBooking:

    def __init__(self):
        self.app = Flask(__name__)
        self._setup_routes()
        self.service = BoxService()
        self.encryption_service = Encryption()

    def _setup_routes(self):
        self.app.add_url_rule(
            rule="/webhook",
            view_func=self.webhook,
            endpoint="webhook",
            methods=["GET"],
        )
        self.app.add_url_rule(
            rule="/webhook",
            view_func=self.process_request,
            endpoint="process_request",
            methods=["POST"],
        )
        self.app.add_url_rule(
            rule="/flow",
            view_func=self.health_check,
            endpoint="heal_check",
            methods=["GET"],
        )
        self.app.add_url_rule(
            rule="/flow",
            view_func=self.process_flow_request,
            endpoint="process_flow_request",
            methods=["POST"],
        )
        self.app.add_url_rule(
            rule="/payment",
            view_func=self.process_payment_response,
            endpoint="process_payment_response",
            methods=["POST"],
        )

    def health_check(self):
        return ""

    def process_flow_request(self):
        encrypted_flow_data_b64 = request.json.get("encrypted_flow_data")
        encrypted_aes_key_b64 = request.json.get("encrypted_aes_key")
        initial_vector_b64 = request.json.get("initial_vector")
        decrypted_data, key, iv = self.encryption_service.decrypt_data(
            encrypted_flow_data_b64,
            encrypted_aes_key_b64, initial_vector_b64)
        print(decrypted_data, key, iv)
        response_data = self.service.process_flow_request(decrypted_data)
        response = json.dumps(response_data, indent=4, default=lambda o: o.__dict__)
        print(json.dumps(response_data, indent=None, default=lambda o: o.__dict__))
        return self.encryption_service.encrypt_data(response, key, iv)

    def webhook(self):
        hub_mode = request.args.get("hub.mode")
        hub_challenge = request.args.get("hub.challenge")
        hub_verify_token = request.args.get("hub.verify_token")

        if hub_mode == "subscribe" and hub_verify_token == "dc6bf63a-2b58-40b6-87b8-096b5e4e8479":
            return hub_challenge
        else:
            abort(403)

    def process_request(self):
        request_body = request.json
        print(request_body)
        message_type: MessageType = MessageType.TEXT
        parsed_message = None
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
            if not messages.get("type"):
                return "Message Not Supported", 200
            message_type = MessageType(messages.get("type"))
            if (message_type == MessageType.INTERACTIVE
                    and messages.get("interactive").get("type")
                    == MessageType.NFM_REPLY.value):
                message_type = MessageType.NFM_REPLY
            parsed_message = self.parse_message(messages, message_type)
        if message_type == MessageType.TEXT:
            self.service.process_text_message(parsed_message)
        elif message_type == MessageType.INTERACTIVE:
            self.service.process_interactive_message(parsed_message)
        elif message_type == MessageType.NFM_REPLY:
            self.service.process_nfm_reply_message(parsed_message)
        else:
            return "Message type not supported", 505
        return "", 200

    def process_payment_response(self):
        header = request.headers.get("X-VERIFY")
        response = request.json
        print(f"{header}, \n {response}")
        self.service.validate_payment_response(header, response)
        return "", 200

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
