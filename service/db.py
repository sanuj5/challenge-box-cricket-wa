import datetime
import os

import firebase_admin
from firebase_admin import firestore, credentials
from google.cloud.firestore_v1 import FieldFilter

from logger import Logger
from message_builder_service import MessageBuilderService
from model.booking import Booking


class DBService:

    def __init__(self):
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        Logger.info("Initializing firestore client for project {}".format(project))
        cred = credentials.ApplicationDefault()

        firebase_admin.initialize_app(credential=cred, options={
            "projectId": project,
        })
        # self.app = firebase_admin.initialize_app()
        self.db = firestore.client()
        self.batch = self.db.batch()
        self.mbs = MessageBuilderService()

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

    def save_flow_token(self, mobile: str, token: str) -> None:
        _id = self.generate_id(mobile)
        data = {
            "mobile": mobile,
            "token": token,
            "created_ts": datetime.datetime.now(),
            "ttl_ts": datetime.datetime.now() + datetime.timedelta(days=30)
        }
        self.db.collection("booking_token").document(_id).set(data)
        Logger.info(f"Token {token} added token successfully for {mobile}")

    @staticmethod
    def generate_id(mobile: str) -> str:
        current_ts = datetime.datetime.now()
        return f'{mobile}_{current_ts.strftime("%Y%m%d%H%M%S")}'

    def get_mobile_token_mapping(self, token: str) -> dict:
        tokens = self.db.collection("booking_token").where(
            filter=FieldFilter("token", "==", token)
        ).stream()
        if not tokens:
            return None
        Logger.info(f"Found mobile for token {token}")
        return {t.to_dict().get("token"): t.to_dict().get("mobile") for t in tokens}

    def create_booking(self,
                       mobile: str,
                       token: str,
                       amount: int,
                       date: str,
                       slots: list[int]
                       ) -> None:
        _id = self.generate_id(mobile)
        data = {
            "mobile": mobile,
            "token": token,
            "created_ts": datetime.datetime.now(),
            "amount": float(amount),
            "date": date,
            "actual_date": datetime.datetime.strptime(date, self.mbs.date_format),
            "slots": slots,
            "ttl_ts": datetime.datetime.now() + datetime.timedelta(minutes=7)
        }
        self.db.collection("pending_bookings").document(_id).set(data)
        self.db.collection("pending_bookings_history").document(_id).set(data)
        Logger.info(f"Booking added for {token} and {mobile}")

    def confirm_booking(self, existing_booking, token, payment_response) -> None:
        _id = self.generate_id(existing_booking.get("mobile"))
        data = {
            "mobile": existing_booking.get("mobile"),
            "token": token,
            "created_ts": datetime.datetime.now(),
            "amount": float(existing_booking.get("amount")),
            "date": existing_booking.get("date"),
            "actual_date": existing_booking.get("actual_date"),
            "slots": existing_booking.get("slots"),
            "cancelled": False,
            "payment_response": payment_response
        }
        self.db.collection("confirmed_bookings").document(_id).set(data)
        Logger.info(f"Booking confirmed for {existing_booking.id}, {token}, "
                    f"{existing_booking.get('mobile')}")

    def get_pending_booking(self, token=None, mobile=None) -> dict:
        bookings = self.db.collection("pending_bookings")
        if token:
            bookings = bookings.where(
                filter=FieldFilter("token", "==", token)
            )
        if mobile:
            bookings = bookings.where(
                filter=FieldFilter("mobile", "==", mobile)
            )
        all_pending_bookings = bookings.get()
        if all_pending_bookings and len(all_pending_bookings) > 0:
            Logger.info(
                f"Pending booking {all_pending_bookings[0].to_dict()} for {mobile}")
            return all_pending_bookings[0]
        else:
            return None

    def cancel_booking(self, token, mobile) -> None:
        booking = self.db.collection("confirmed_bookings").where(
            filter=FieldFilter("token", "==", token)
        )
        booking.update({"cancelled": True})
        Logger.info(f"Booking cancelled for {token} and {mobile}")

    def get_reserved_slots(self, date) -> dict:
        bookings: dict = dict()
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
                bookings[slot] = booking.to_dict()

        for booking in pending_bookings:
            b: dict = booking.to_dict()
            for slot in b.get("slots"):
                bookings[slot] = booking.to_dict()

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

    def remove_pending_bookings(self) -> None:
        current_ts = datetime.datetime.now()
        pending_bookings = self.db.collection("pending_bookings").where(
            filter=FieldFilter("ttl_ts", "<", current_ts)
        ).stream()
        for booking in pending_bookings:
            Logger.info(
                f"Removing pending booking for {booking.to_dict().get('mobile')}")
            self.batch.delete(booking.reference)
        self.batch.commit()

    def get_user_future_bookings(self, mobile, date) -> list[Booking]:
        Logger.info("Getting future bookings for {} and date {}".format(mobile, date))
        future_bookings = self.db.collection("confirmed_bookings").where(
            filter=FieldFilter("mobile", "==", mobile)
        ).where(
            filter=FieldFilter("actual_date", ">=", date)
        ).stream()
        return Booking.create_booking(future_bookings)

    def get_notification_eligible_numbers(self, new_booking_only=True) -> list[str]:
        collection = self.db.collection("booking_notification_numbers").where(
                filter=FieldFilter("active", "==", True)
            )
        if new_booking_only:
            mobiles = collection.where(
                filter=FieldFilter("new_booking", "==", True)
            )
        else:
            mobiles = collection.where(
                filter=FieldFilter("scheduled", "==", True)
            )
        return [mobile.get("number") for mobile in mobiles.stream()]

    def update_user_details(self, mobile, name):
        _id = mobile
        data = {
            "mobile": mobile,
            "name": name,
            "last_updated_ts": datetime.datetime.now()
        }
        self.db.collection("users").document(_id).set(data)

    def get_user_details(self, mobile) -> str:
        user = self.db.collection("users").where(
            filter=FieldFilter("mobile", "==", mobile)
        ).stream()
        return user.get("name")
