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

    def send_message_request(self, data, header: dict = None):
        headers = self.get_headers(header)
        json_data = json.dumps(data, default=lambda o: o.__dict__)
        Logger.info(json_data)
        requests.post(url=f"{self.base_url}/messages",
                      json=json.loads(json_data),
                      headers=headers)

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

if __name__ == '__main__':
    api = WhatsappApi("EAAOXlAJRh9cBOZCSk7kRtRh5UH7ZA0LaeWII2LQdgTgAi01cGYstTWWPqXQ2kEr9Ij6ZBQlRSuaZCP5ZAqcg2TY7ZCVQmQFF6D47OmjK2CHUMmirthFXoPsOjyhInJFgGdJoC2xZAw7eOrym3JdGQwtx1cYIZBVMwpjwjujxRwb15ZAjUDpmRpUDOt7I8UjZBE0RkN", "163821933489146")
    # message = MessageBuilderService.get_order_confirmation_message(
    #                 mobile="918390903001",
    #                 token="87a4e4695e854ce6b24a39e85d919f",
    #                 message="Booking Confirmed")
    # response = api.send_message_request(message)
    response = api.get_payment_status("17dbcf5b0b33463cb3bb392e09d70e")
    print(response)