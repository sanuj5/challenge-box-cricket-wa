import logging
from types import SimpleNamespace

from flask import Flask, request, abort

from encryption_service import Encryption
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
        return self.encryption_service.encrypt_data("{}", key, iv)

    def webhook(self):
        hub_mode = request.args.get("hub.mode")
        hub_challenge = request.args.get("hub.challenge")
        hub_verify_token = request.args.get("hub.verify_token")

        if hub_mode == "subscribe" and hub_verify_token == "dc6bf63a-2b58-40b6-87b8-096b5e4e8479":
            return hub_challenge
        else:
            abort(403)

    def process_request(self):
        logging.info(request.json)
        request_body = SimpleNamespace(**request.json)
        message_type = \
            request_body.entry[0].get("changes")[0].get("value").get("messages")[0].get(
                "type")
        message = self.parse_message(
            request_body.entry[0].get("changes")[0].get("value").get("messages")[0],
            message_type)
        if message_type == "text":
            self.service.process_text_message("918390903001", message)
        elif message_type == "interactive":
            self.service.process_interactive_message("918390903001", message)
        else:
            return "Message type not supported", 505
        return "", 200

    @staticmethod
    def parse_message(param, message_type):
        if message_type == "text":
            return TextMessage(
                id=param.get("id"),
                message_from=param.get("from"),
                timestamp=param.get("timestamp"),
                text=Text(**param.get("text")),
                type=param.get(type)
            )
        if message_type == "interactive":
            return InteractiveMessage(
                id=param.get("id"),
                message_from=param.get("from"),
                timestamp=param.get("timestamp"),
                interactive=Interactive(**param.get("interactive")),
                type=param.get(type)
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
