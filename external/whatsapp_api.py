import requests
import json
from logger import Logger


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

    def send_post_request(self, data, header=None):
        if header:
            header.update(self.auth_header)
            headers = header
        else:
            headers = self.default_headers
        json_data = json.dumps(data, default=lambda o: o.__dict__)
        Logger.info(json_data)
        r = requests.post(url=self.url, json=json.loads(json_data), headers=headers)
        Logger.info(r.content)
