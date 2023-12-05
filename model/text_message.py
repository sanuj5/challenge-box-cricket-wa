class Text:
    preview_url: bool
    body: str

    def __init__(self, preview_url: bool = False, body: str = None) -> None:
        self.preview_url = preview_url
        self.body = body


class TextMessage:
    messaging_product: str
    recipient_type: str
    to: str
    type: str
    text: Text

    def __init__(self, messaging_product: str = None, recipient_type: str = None,
                 to: str = None, type: str = None, text: Text = None) -> None:
        self.messaging_product = messaging_product
        self.recipient_type = recipient_type
        self.to = to
        self.type = type
        self.text = text
