import firebase_admin
from firebase_admin import firestore


class DBService:
    def __init__(self):
        self.app = firebase_admin.initialize_app()
        self.db = firestore.client()

    def get_all_slots(self) -> (dict,dict):
        users_ref = self.db.collection("slots")
        docs = users_ref.stream()
        slots = dict()
        reverse_mapping = dict()

        for doc in docs:
            slots[doc.to_dict().get('id')] = doc.to_dict().get('title')
            reverse_mapping[doc.to_dict().get('title')] = doc.to_dict().get('id')
        return slots, reverse_mapping
