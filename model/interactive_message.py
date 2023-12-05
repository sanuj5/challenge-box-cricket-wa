from dataclasses import dataclass
from typing import List


@dataclass
class Row:
    id: str
    title: str
    description: str

    def __init__(self, id: str = None, title: str = None,
                 description: str = "") -> None:
        self.id = id
        self.title = title
        self.description = description


@dataclass
class Section:
    title: str
    rows: List[Row]

    def __init__(self, title: str = None, rows: List[Row] = None) -> None:
        self.title = title
        self.rows = rows


@dataclass
class Action:
    button: str
    sections: List[Section]

    def __init__(self, button: str = None, sections: List[Section] = None) -> None:
        self.button = button
        self.sections = sections


@dataclass
class Body:
    text: str

    def __init__(self, text: str = None) -> None:
        self.text = text


@dataclass
class Header:
    type: str
    text: str

    def __init__(self, type: str = "text", text: str = "CBC") -> None:
        self.type = type
        self.text = text


@dataclass
class Interactive:
    type: str
    header: Header
    body: Body
    action: Action

    def __init__(self, type: str = None, header: Header = None, body: Body = None,
                 action: Action = None) -> None:
        self.type = type
        self.header = header
        self.body = body
        self.action = action


@dataclass
class InteractiveMessage:
    messaging_product: str
    to: str
    type: str
    interactive: Interactive

    def __init__(self,
                 messaging_product: str = "whatsapp",
                 to: str = None,
                 type: str = "interactive",
                 interactive: Interactive = None) -> None:
        self.messaging_product = messaging_product
        self.to = to
        self.type = type
        self.interactive = interactive
