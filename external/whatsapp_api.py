import requests
import json
from logger import Logger
from model.enums import Constants


class WhatsappApi:
    def __init__(self, wa_api_token, mobile_id):
        self.base_url = f"https://graph.facebook.com/v18.0/{mobile_id}"
        self.default_headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(wa_api_token)
        }
        self.auth_header = {
            "Authorization": "Bearer {}".format(wa_api_token)
        }

    def send_message_request(self, data, header: dict = None) -> None:
        headers = self.get_headers(header)
        json_data = json.dumps(data, default=lambda o: o.__dict__)
        Logger.info(json_data)
        result = requests.post(url=f"{self.base_url}/messages",
                               json=json.loads(json_data),
                               headers=headers)
        Logger.info(f"status_code={result.status_code}, response={result.text}")

    def get_payment_status(self, token: str):
        url = "{}/payments/{}/{}".format(
            self.base_url, Constants.PAYMENT_CONFIGURATION.value, token
        )
        Logger.info(url)
        result = requests.get(url=url, headers=self.auth_header)
        return result.json()

    def get_headers(self, header):
        if header:
            header.update(self.auth_header)
            return header
        else:
            return self.default_headers
