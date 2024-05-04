from typing import List
from dataclasses import dataclass


@dataclass
class Profile:
    name: str

    def __init__(self, name: str) -> None:
        self.name = name


@dataclass
class Contact:
    profile: Profile
    wa_id: str

    def __init__(self, profile: Profile, wa_id: str) -> None:
        self.profile = profile
        self.wa_id = wa_id


@dataclass
class ButtonReply:
    id: str
    title: str

    def __init__(self, id: str, title: str) -> None:
        self.id = id
        self.title = title


@dataclass
class Interactive:
    button_reply: ButtonReply
    type: str

    def __init__(self, button_reply: ButtonReply, type: str) -> None:
        self.button_reply = button_reply
        self.type = type


@dataclass
class Message:
    message_from: str
    id: str
    timestamp: str
    interactive: Interactive
    type: str

    def __init__(self, message_from: str, id: str, timestamp: str,
                 interactive: Interactive, type: str) -> None:
        self.message_from = message_from
        self.id = id
        self.timestamp = timestamp
        self.interactive = interactive
        self.type = type


@dataclass
class Metadata:
    display_phone_number: str
    phone_number_id: str

    def __init__(self, display_phone_number: str, phone_number_id: str) -> None:
        self.display_phone_number = display_phone_number
        self.phone_number_id = phone_number_id


@dataclass
class Value:
    messaging_product: str
    metadata: Metadata
    contacts: List[Contact]
    messages: List[Message]

    def __init__(self, messaging_product: str, metadata: Metadata,
                 contacts: List[Contact], messages: List[Message]) -> None:
        self.messaging_product = messaging_product
        self.metadata = metadata
        self.contacts = contacts
        self.messages = messages


@dataclass
class Change:
    value: Value
    field: str

    def __init__(self, value: Value, field: str) -> None:
        self.value = value
        self.field = field


@dataclass
class Entry:
    id: str
    changes: List[Change]

    def __init__(self, id: str, changes: List[Change]) -> None:
        self.id = id
        self.changes = changes


@dataclass
class WebhookInteractive:
    object: str
    entry: List[Entry]

    def __init__(self, object: str, entry: List[Entry]) -> None:
        self.object = object
        self.entry = entry

    def __str__(self) -> str:
        return super().__str__()
