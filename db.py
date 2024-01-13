import datetime

import firebase_admin
from firebase_admin import firestore, credentials
from google.cloud.firestore_v1 import FieldFilter
from logger import Logger
from model.booking import Booking


class DBService:
    def __init__(self):
        Logger.info("Initializing firestore client..")
        cred = credentials.ApplicationDefault()

        firebase_admin.initialize_app(credential=cred, options={
            "projectId": "challenge-cricket-409510"
        })
        # self.app = firebase_admin.initialize_app()
        self.db = firestore.client()
        self.batch = self.db.batch()

    def get_all_slots(self) -> (dict, dict):
        docs = self.db.collection("slots").where(
            filter=FieldFilter("active", "==", True)
        ).order_by("sort_order").stream()
        slots = dict()
        day_wise_slots: dict[int, list: dict] = dict()

        for day in range(0, 7):
            _list = list()
            day_wise_slots[day] = _list

        for doc in docs:
            slots[doc.to_dict().get('id')] = doc.to_dict()
            day_wise_slots.get(doc.get("day_id")).append(doc.to_dict())
        return slots, day_wise_slots

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
        Logger.info(f"Token {token} added token successfully for {mobile}")

    def get_mobile_token_mapping(self, token) -> dict:
        tokens = self.db.collection("booking_token").where(
            filter=FieldFilter("token", "==", token)
        ).stream()
        if not tokens:
            return None
        Logger.info(f"Found mobile for token {token}")
        return {t.to_dict().get("token"): t.to_dict().get("mobile") for t in tokens}

    def create_booking(self, mobile, token, amount, date, slots: list[int]):
        current_ts = datetime.datetime.now()
        ttl_ts = current_ts + datetime.timedelta(minutes=10)
        data = {
            "mobile": mobile,
            "token": token,
            "created_ts": current_ts,
            "amount": float(amount),
            "date": date,
            "slots": slots,
            "ttl_ts": ttl_ts
        }
        self.db.collection("pending_bookings").add(data)
        Logger.info(f"Booking added for {token} and {mobile}")

    def confirm_booking(self, existing_booking, token, payment_response):
        data = {
            "mobile": existing_booking.get("mobile"),
            "token": token,
            "created_ts": datetime.datetime.now(),
            "amount": float(existing_booking.get("amount")),
            "date": existing_booking.get("date"),
            "slots": existing_booking.get("slots"),
            "cancelled": False,
            "payment_response": payment_response
        }
        self.db.collection("confirmed_bookings").add(data)
        Logger.info(f"Booking confirmed for {token}, {existing_booking.get('mobile')}")

    def get_pending_booking(self, token):
        bookings = self.db.collection("pending_bookings").where(
            filter=FieldFilter("token", "==", token)
        ).get()
        return bookings[0]

    def cancel_booking(self, token, mobile):
        booking = self.db.collection("confirmed_bookings").where(
            filter=FieldFilter("token", "==", token)
        )
        booking.update({"cancelled": True})
        Logger.info(f"Booking cancelled for {token} and {mobile}")

    def get_reserved_slots(self, date) -> dict[int]:
        bookings: dict[int] = dict()
        confirmed_bookings = self.db.collection("confirmed_bookings").where(
            filter=FieldFilter("date", "==", date)
        ).where(
            filter=FieldFilter("cancelled", "==", False)
        ).stream()

        pending_bookings = self.db.collection("pending_bookings").where(
            filter=FieldFilter("date", "==", date)
        ).stream()

        for booking in confirmed_bookings:
            b: dict = booking.to_dict()
            for slot in b.get("slots"):
                bookings[slot] = True

        for booking in pending_bookings:
            b: dict = booking.to_dict()
            for slot in b.get("slots"):
                bookings[slot] = True

        return bookings

    def get_confirmed_bookings(self, date) -> list[Booking]:
        confirmed_bookings = self.db.collection("confirmed_bookings").where(
            filter=FieldFilter("date", "==", date)
        ).where(
            filter=FieldFilter("cancelled", "==", False)
        ).stream()
        return Booking.create_booking(confirmed_bookings)

    def get_pending_bookings(self, date) -> list[Booking]:
        pending_bookings = self.db.collection("pending_bookings").where(
            filter=FieldFilter("date", "==", date)
        ).where(
            filter=FieldFilter("cancelled", "==", False)
        ).stream()
        return Booking.create_booking(pending_bookings)

    def remove_pending_bookings(self):
        current_ts = datetime.datetime.now()
        pending_bookings = self.db.collection("pending_bookings").where(
            filter=FieldFilter("ttl_ts", "<", current_ts)
        ).stream()
        for booking in pending_bookings:
            Logger.info(f"Removing pending booking for {booking.to_dict().get('mobile')}")
            self.batch.delete(booking.reference)
        self.batch.commit()
