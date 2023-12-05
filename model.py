from typing import List


class Profile:
    name: str

    def __init__(self, name: str) -> None:
        self.name = name


class Contact:
    profile: Profile
    wa_id: str

    def __init__(self, profile: Profile, wa_id: str) -> None:
        self.profile = profile
        self.wa_id = wa_id


class ListReply:
    id: str
    title: str
    description: str

    def __init__(self, id: str, title: str, description: str) -> None:
        self.id = id
        self.title = title
        self.description = description


class Interactive:
    list_reply: ListReply
    type: str

    def __init__(self, list_reply: ListReply, _type: str) -> None:
        self.list_reply = list_reply
        self.type = _type


class Message:
    message_from: str
    id: str
    timestamp: str
    interactive: Interactive
    type: str

    def __init__(self, message_from: str, _id: str, timestamp: str, interactive: Interactive, type: str) -> None:
        self.message_from = message_from
        self.id = _id
        self.timestamp = timestamp
        self.interactive = interactive
        self.type = type


class Metadata:
    display_phone_number: str
    phone_number_id: str

    def __init__(self, display_phone_number: str, phone_number_id: str) -> None:
        self.display_phone_number = display_phone_number
        self.phone_number_id = phone_number_id


class Value:
    messaging_product: str
    metadata: Metadata
    contacts: List[Contact]
    messages: List[Message]

    def __init__(self, messaging_product: str, metadata: Metadata, contacts: List[Contact], messages: List[Message]) -> None:
        self.messaging_product = messaging_product
        self.metadata = metadata
        self.contacts = contacts
        self.messages = messages


class Change:
    value: Value
    field: str

    def __init__(self, value: Value, field: str) -> None:
        self.value = value
        self.field = field


class Entry:
    id: str
    changes: List[Change]

    def __init__(self, _id: str, changes: List[Change]) -> None:
        self.id = _id
        self.changes = changes


class Model:
    object: str
    entry: List[Entry]

    def __init__(self, _object: str, entry: List[Entry]) -> None:
        self.object = _object
        self.entry = entry
