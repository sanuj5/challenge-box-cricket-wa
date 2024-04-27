import requests
import json
from logger import Logger
from message_builder_service import MessageBuilderService


class WhatsappApi:
    def __init__(self, wa_api_token, mobile_id):
        self.url = f"https://graph.facebook.com/v18.0/{mobile_id}/messages"
        self.default_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {wa_api_token}"
        }
        self.auth_header = {
            "Authorization": f"Bearer {wa_api_token}"
        }

    def send_post_request(self, data, header: dict = None):
        headers = self.get_headers(header)
        json_data = json.dumps(data, default=lambda o: o.__dict__)
        Logger.info(json_data)
        requests.post(url=self.url, json=json.loads(json_data), headers=headers)

    def get_headers(self, header):
        if header:
            header.update(self.auth_header)
            return header
        else:
            return self.default_headers
