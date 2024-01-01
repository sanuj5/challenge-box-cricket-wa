import datetime

import firebase_admin
from firebase_admin import firestore, credentials
from google.cloud.firestore_v1 import FieldFilter


class DBService:
    def __init__(self):
        cred = credentials.ApplicationDefault()

        firebase_admin.initialize_app(credential=cred, options={
            "projectId": "challenge-cricket-409510"
        })
        # self.app = firebase_admin.initialize_app()
        self.db = firestore.client()

    def get_all_slots(self) -> (dict, dict):
        slots_ref = self.db.collection("slots")
        docs = slots_ref.order_by("id").stream()
        slots = dict()
        reverse_mapping = dict()

        for doc in docs:
            slots[doc.to_dict().get('id')] = doc.to_dict().get('title')
            reverse_mapping[doc.to_dict().get('title')] = doc.to_dict().get('id')
        return slots, reverse_mapping

    def get_all_secrets(self) -> dict:
        slots_ref = self.db.collection("secrets")
        docs = slots_ref.stream()
        for doc in docs:
            if doc.id == "all":
                return doc.to_dict()
        return dict()

    def save_flow_token(self, mobile, token):
        data = {"mobile": mobile, "token": token, "created_ts": datetime.datetime.now()}
        self.db.collection("booking_token").add(data)
        print(f"Token {token} added token successfully for {mobile}")

    def get_mobile_token_mapping(self, token) -> dict:
        tokens = self.db.collection("booking_token").where(
            filter=FieldFilter("token", "==", token)
        ).stream()
        if not tokens:
            return None
        return {t.to_dict().get("token"): t.to_dict().get("mobile") for t in tokens}
