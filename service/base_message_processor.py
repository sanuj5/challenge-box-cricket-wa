from abc import ABC

from service.db import DBService
from message_builder_service import MessageBuilderService
from model.enums import PaymentProvider
from external.payment import PaymentFactory
from external.whatsapp_api import WhatsappApi


class BaseProcessor(ABC):
    def __init__(self):
        self.db_service = DBService()
        self.slots, self.day_wise_slots = self.db_service.get_all_slots()
        self.mbs = MessageBuilderService()
        secrets = self.db_service.get_all_secrets()
        self.api_service = WhatsappApi(secrets.get("WA_API_TOKEN"),
                                       secrets.get("MOBILE_ID"))
        self.flow_id = secrets.get("FLOW_ID")
        self.payment_service = PaymentFactory.get_payment_service(
            payment_provider=PaymentProvider.RAZORPAY, secrets=secrets
        )