import datetime
from abc import ABC

import pytz

from external.whatsapp_api import WhatsappApi
from logger import Logger
from message_builder_service import MessageBuilderService
from service.db import DBService


class BaseProcessor(ABC):
    def __init__(self, db_service):
        self.db_service: DBService = db_service
        self.slots, self.day_wise_slots = self.db_service.get_all_slots()
        self.mbs = MessageBuilderService()
        secrets = self.db_service.get_all_secrets()
        self.api_service = WhatsappApi(secrets.get("WA_API_TOKEN"),
                                       secrets.get("MOBILE_ID"))
        self.flow_id = secrets.get("FLOW_ID")

    def get_available_slots(self, formatted_date) -> list[dict]:
        today_date = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
        date = datetime.datetime.strptime(formatted_date, self.mbs.date_format)
        weekday = date.weekday()
        slots = self.day_wise_slots.get(weekday)
        reserved_slots: dict = self.db_service.get_reserved_slots(formatted_date)
        evening_slot_booked = None
        for _, booking in reserved_slots.items():
            for slot in booking.get("slots"):
                booked_slot = self.slots.get(slot)
                if (booked_slot.get("start_hour") >= 18 and
                        booked_slot.get("preference") == 1):
                    evening_slot_booked = booked_slot
                    Logger.info("Evening booked slot: " + str(evening_slot_booked))
                    continue

        response = list()
        current_hour = today_date.hour

        for slot in slots:
            if (evening_slot_booked and slot.get("start_hour") >= 18 and
                    ((slot.get("preference") == 1 and
                      slot.get("start_hour") != evening_slot_booked.get("start_hour"))
                     or
                     (slot.get("preference") == 2 and
                      evening_slot_booked.get("start_hour") <= slot.get(
                                 "start_hour") < evening_slot_booked.get("end_hour"))
                    )
            ):
                continue
            elif (not evening_slot_booked and slot.get("preference") == 2
                  and slot.get("start_hour") >= 18):
                continue
            item = {
                "id": slot.get("id"),
                "title": f'{slot.get("title")}',
                "description": f'₹ {slot.get("price")}',
                "enabled": True
            }
            if reserved_slots.get(slot.get("id")):
                item["enabled"] = False
            if (today_date.date() == date.date()
                    and slot.get("start_hour") <= current_hour):
                item["enabled"] = False
            response.append(item)
        return response
