from dataclasses import dataclass


class Reply:
    id: str
    title: str

    def __init__(self, id: str, title: str):
        self.id = id
        self.title = title

@dataclass
class Button:
    type: str
    reply: Reply

    def __init__(self, type: str = "button", reply: Reply = None) -> None:
        self.type = type
        self.reply = reply




@dataclass
class Action:
    buttons: list[Button]

    def __init__(self, buttons: list[Button] = None) -> None:
        self.buttons = buttons


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
