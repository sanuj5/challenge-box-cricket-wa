import firebase_admin
from firebase_admin import firestore


class DBService:
    def __init__(self):
        # cred = credentials.ApplicationDefault()
        #
        # firebase_admin.initialize_app(credential=cred, options={
        #     "projectId": "quixotic-booth-407213"
        # })
        self.app = firebase_admin.initialize_app()
        self.db = firestore.client()

    def get_all_slots(self) -> (dict,dict):
        slots_ref = self.db.collection("slots")
        docs = slots_ref.order_by("id").stream()
        slots = dict()
        reverse_mapping = dict()

        for doc in docs:
            slots[doc.to_dict().get('id')] = doc.to_dict().get('title')
            reverse_mapping[doc.to_dict().get('title')] = doc.to_dict().get('id')
        return slots, reverse_mapping
