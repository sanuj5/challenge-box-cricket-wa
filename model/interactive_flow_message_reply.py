from dataclasses import dataclass
from typing import List


@dataclass
class Context:
    context_from: str
    id: str

    def __init__(self, context_from: str, id: str) -> None:
        self.context_from = context_from
        self.id = id


@dataclass
class NfmReply:
    name: str
    response_json: dict

    def __init__(self, name: str, response_json: dict) -> None:
        self.name = name
        self.response_json = response_json


@dataclass
class InteractiveFlowReply:
    type: str
    nfm_reply: NfmReply

    def __init__(self, type: str, nfm_reply: NfmReply) -> None:
        self.type = type
        self.nfm_reply = nfm_reply


@dataclass
class InteractiveFlowMessageReply:
    context: Context
    message_from: str
    id: str
    type: str
    interactive: InteractiveFlowReply
    timestamp: str

    def __init__(self, context: Context, message_from: str, id: str, type: str,
                 interactive: InteractiveFlowReply, timestamp: str) -> None:
        self.context = context
        self.message_from = message_from
        self.id = id
        self.type = type
        self.interactive = interactive
        self.timestamp = timestamp