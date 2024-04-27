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
        Logger.info(headers)
        json_data = json.dumps(data, default=lambda o: o.__dict__)
        Logger.info(json_data)
        r = requests.post(url=self.url, json=json.loads(json_data), headers=headers)
        Logger.info(r.content)

    def send_post_request_url_encoded(self, data, header: dict = None):
        headers = self.get_headers(header)
        json_data = json.dumps(data, default=lambda o: o.__dict__)
        Logger.info(json_data)
        r = requests.post(url=self.url, json=json_data, headers=headers)
        Logger.info(r.content)

    def get_headers(self, header):
        if header:
            header.update(self.auth_header)
            return header
        else:
            return self.default_headers


if __name__ == '__main__':
    api = WhatsappApi("EAAOXlAJRh9cBOZCSk7kRtRh5UH7ZA0LaeWII2LQdgTgAi01cGYstTWWPqXQ2kEr9Ij6ZBQlRSuaZCP5ZAqcg2TY7ZCVQmQFF6D47OmjK2CHUMmirthFXoPsOjyhInJFgGdJoC2xZAw7eOrym3JdGQwtx1cYIZBVMwpjwjujxRwb15ZAjUDpmRpUDOt7I8UjZBE0RkN", "163821933489146")
    message = MessageBuilderService.get_interactive_payment_message_gw(
                mobile="918390903001",
                payment_amount=100,
                slots=["1-4"],
                reference_id="de3e0146cf4d4010ba278fe5ad6b1e",
                message_body=f"""
Almost there for your below booking! Please pay to confirm your booking.

Date: 23-Apr-2023
Slots: 6-7 AM

"""
            )
    response = api.send_post_request(message)
    print(response)
