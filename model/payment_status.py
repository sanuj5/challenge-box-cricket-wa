import json


class Amount:
    value: int
    offset: int

    def __init__(self, value: int, offset: int) -> None:
        self.value = value
        self.offset = offset


class Transaction:
    id: str
    type: str
    status: str
    created_timestamp: int
    updated_timestamp: int
    amount: Amount
    currency: str

    def __init__(self, id: str, type: str, status: str, created_timestamp: int,
                 updated_timestamp: int, amount: Amount, currency: str) -> None:
        self.id = id
        self.type = type
        self.status = status
        self.created_timestamp = created_timestamp
        self.updated_timestamp = updated_timestamp
        self.amount = amount
        self.currency = currency


class Payment:
    reference_id: str
    amount: Amount
    currency: str
    transaction: Transaction

    def __init__(self, reference_id: str, amount: Amount, currency: str,
                 transaction: Transaction = None) -> None:
        self.reference_id = reference_id
        self.amount = amount
        self.currency = currency
        self.transaction = transaction

    def __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__)


class PaymentStatus:
    id: str
    status: str
    timestamp: int
    recipient_id: str
    type: str
    payment: Payment

    def __init__(self, id: str, status: str, timestamp: int, recipient_id: str,
                 type: str, payment: Payment) -> None:
        self.id = id
        self.status = status
        self.timestamp = timestamp
        self.recipient_id = recipient_id
        self.type = type
        self.payment = payment

    def __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__)
