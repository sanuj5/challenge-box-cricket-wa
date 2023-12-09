from dataclasses import dataclass
from typing import List


@dataclass
class Parameter:
    flow_message_version: str
    mode: str
    flow_token: str
    flow_id: str
    flow_cta: str
    flow_action: str
    flow_action_payload: dict

    def __init__(self, flow_message_version: str = None,
                 mode: str = None,
                 flow_token: str = None,
                 flow_id: str = None,
                 flow_cta: str = None,
                 flow_action: str = None,
                 flow_action_payload: dict = None) -> None:
        self.flow_message_version = flow_message_version
        self.flow_token = flow_token
        self.flow_id = flow_id
        self.flow_cta = flow_cta
        self.mode = mode
        self.flow_action = flow_action
        self.flow_action_payload = flow_action_payload


@dataclass
class Action:
    name: str
    parameters: Parameter

    def __init__(self, name: str = None, parameters: Parameter = None) -> None:
        self.name = name
        self.parameters = parameters


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
class InteractiveFlowMessage:
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
