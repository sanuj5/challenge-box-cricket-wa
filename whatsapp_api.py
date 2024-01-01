import requests
import json
from logger import Logger

class WhatsappApi:
    def __init__(self, wa_api_token, mobile_id):
        self.url = f"https://graph.facebook.com/v18.0/{mobile_id}/messages"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {wa_api_token}"
        }

    def send_post_request(self, data):
        Logger.info(data)
        json_data = json.dumps(data, indent=4,
                               default=lambda o: o.__dict__)
        Logger.info(json_data)
        r = requests.post(url=self.url, json=json.loads(json_data), headers=self.headers)
        Logger.info(r.content)
