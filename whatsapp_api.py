import requests
import json


class WhatsappApi:
    def __init__(self):
        self.url = "https://graph.facebook.com/v17.0/135439162996517/messages"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer EAAEnDVjByU4BO3pP7lCHlwGWZCXKZAcLs8oYifLX3UYlTs5i6yQFN8xJ67ZBSZClzsGFianAZCGoZCQAqCEjEojmrno95ZC4QUFROeGLsWg2flAmqpZB46kuPzBc3SqTqXHffqGFZB2uFG1q2xl55zyE9GheOctDV9KJ0iOkjdxC5xKMF2bkH5cCBbALayjGH5So5MpjWyyDOLWgeULD6vXJUl2GZC0wZDZD"
        }

    def send_post_request(self, data):
        json_data = json.dumps(data, indent=4,
                               default=lambda o: o.__dict__)
        print(json_data)
        r = requests.post(url=self.url, json=json.loads(json_data), headers=self.headers)
        print(r.content)
