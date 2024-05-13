from dataclasses import dataclass
from typing import List


@dataclass
class Parameter:
    type: str
    text: str

    def __init__(self, type: str, text: str) -> None:
        self.type = type
        self.text = text


@dataclass
class Component:
    type: str
    parameters: List[Parameter]

    def __init__(self, type: str, parameters: List[Parameter]) -> None:
        self.type = type
        self.parameters = parameters


@dataclass
class Language:
    code: str

    def __init__(self, code: str) -> None:
        self.code = code


@dataclass
class Template:
    name: str
    language: Language
    components: List[Component]

    def __init__(self, name: str, language: Language,
                 components: List[Component]) -> None:
        self.name = name
        self.language = language
        self.components = components


@dataclass
class TemplateMessage:
    messaging_product: str
    recipient_type: str
    to: str
    type: str
    template: Template

    def __init__(self, messaging_product: str,
                 recipient_type: str,
                 to: str,
                 type: str,
                 template: Template) -> None:
        self.messaging_product = messaging_product
        self.recipient_type = recipient_type
        self.to = to
        self.type = type
        self.template = template


class TemplateBuilder:

    @staticmethod
    def build(mobile, template_name, parameters) -> TemplateMessage:

        components = [Component("body", parameters)]

        language = Language("EN")

        template = Template(
            name=template_name,
            language=language,
            components=components
        )

        return TemplateMessage(
            messaging_product="whatsapp",
            recipient_type="individual",
            to=mobile,
            type="template",
            template=template
        )

    @staticmethod
    def get_text_parameter(text_value: str) -> Parameter:
        return Parameter("text", text_value)
