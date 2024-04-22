from abc import ABC

from external.whatsapp_api import WhatsappApi
from message_builder_service import MessageBuilderService


class BaseProcessor(ABC):
    def __init__(self, db_service):
        self.db_service = db_service
        self.slots, self.day_wise_slots = self.db_service.get_all_slots()
        self.mbs = MessageBuilderService()
        secrets = self.db_service.get_all_secrets()
        self.api_service = WhatsappApi(secrets.get("WA_API_TOKEN"),
                                       secrets.get("MOBILE_ID"))
        self.flow_id = secrets.get("FLOW_ID")
