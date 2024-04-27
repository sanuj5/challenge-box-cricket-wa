class Order:
    status: str
    description: str

    def __init__(self, status: str, description: str) -> None:
        self.status = status
        self.description = description


class Parameters:
    reference_id: str
    order: Order

    def __init__(self, reference_id: str, order: Order) -> None:
        self.reference_id = reference_id
        self.order = order


class Action:
    name: str
    parameters: Parameters

    def __init__(self, name: str, parameters: Parameters) -> None:
        self.name = name
        self.parameters = parameters


class Body:
    text: str

    def __init__(self, text: str) -> None:
        self.text = text


class Interactive:
    type: str
    body: Body
    action: Action

    def __init__(self, type: str, body: Body, action: Action) -> None:
        self.type = type
        self.body = body
        self.action = action


class OrderConfirmation:
    recipient_type: str
    to: str
    type: str
    interactive: Interactive

    def __init__(self,
                 recipient_type: str = "individual",
                 to: str = None,
                 type: str = "interactive",
                 interactive: Interactive = None) -> None:
        self.recipient_type = recipient_type
        self.to = to
        self.type = type
        self.interactive = interactive
