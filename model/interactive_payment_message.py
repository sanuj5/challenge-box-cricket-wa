from typing import Optional, List


class Tax:
    value: int
    offset: int
    description: str

    def __init__(self, value: int = 0, offset: int = 100,
                 description: str = "") -> None:
        self.value = value
        self.offset = offset
        self.description = description


class Discount:
    value: int
    offset: int
    description: str
    discount_program_name: Optional[str]

    def __init__(self, value: int = 0, offset: int = 100, description: str = "",
                 discount_program_name: Optional[str] = None) -> None:
        self.value = value
        self.offset = offset
        self.description = description
        self.discount_program_name = discount_program_name


class Expiration:
    timestamp: str
    description: str

    def __init__(self, timestamp: str, description: str) -> None:
        self.timestamp = timestamp
        self.description = description


class TotalAmount:
    value: int
    offset: int

    def __init__(self, value: int = None, offset: int = 100) -> None:
        self.value = value
        self.offset = offset


class ImporterAddress:
    address_line1: str
    address_line2: str
    city: str
    zone_code: str
    postal_code: int
    country_code: str

    def __init__(self, address_line1: str = "The Challenge Cricket Academy",
                 address_line2: str = "Jitodia", city: str = "Anand",
                 zone_code: str = "GJ", postal_code: int = "388001",
                 country_code: str = "IN") -> None:
        self.address_line1 = address_line1
        self.address_line2 = address_line2
        self.city = city
        self.zone_code = zone_code
        self.postal_code = postal_code
        self.country_code = country_code


class Item:
    retailer_id: int
    name: str
    amount: TotalAmount
    quantity: int
    sale_amount: TotalAmount
    country_of_origin: str
    importer_name: str
    importer_address: ImporterAddress

    def __init__(self, retailer_id: int = 0,
                 name: str = "Booking Slots",
                 amount: TotalAmount = None,
                 quantity: int = 0,
                 sale_amount: TotalAmount = None,
                 country_of_origin: str = "India",
                 importer_name: str = "Challenge Box Cricket",
                 importer_address: ImporterAddress = ImporterAddress()) -> None:
        self.retailer_id = retailer_id
        self.name = name
        self.amount = amount
        self.quantity = quantity
        self.sale_amount = sale_amount
        self.country_of_origin = country_of_origin
        self.importer_name = importer_name
        self.importer_address = importer_address


class Order:
    status: str
    expiration: Expiration
    items: List[Item]
    subtotal: TotalAmount
    tax: Tax
    shipping: Discount
    discount: Discount

    def __init__(self, status: str = "pending",
                 expiration: Expiration = None,
                 items: List[Item] = None,
                 subtotal: TotalAmount = None,
                 tax: Tax = Tax(
                     value=0,
                     offset=100,
                     description=""
                 ),
                 shipping: Discount = None,
                 discount: Discount = None) -> None:
        self.status = status
        self.expiration = expiration
        self.items = items
        self.subtotal = subtotal
        self.tax = tax
        self.shipping = shipping
        self.discount = discount


class PaymentLink:
    uri: str

    def __init__(self, uri: str = None) -> None:
        self.uri = uri


class PaymentSetting:
    type: str
    payment_link: PaymentLink

    def __init__(self, type: str = "payment_link",
                 payment_link: PaymentLink = None) -> None:
        self.type = type
        self.payment_link = payment_link


class Parameters:
    reference_id: str
    type: str
    payment_type: str
    currency: str
    total_amount: TotalAmount
    order: Order

    def __init__(self, reference_id: str = "",
                 type: str = "digital-goods",
                 payment_type: str = "upi",
                 currency: str = "INR",
                 total_amount: TotalAmount = None,
                 order: Order = None) -> None:
        self.reference_id = reference_id
        self.type = type
        self.payment_type = payment_type
        self.currency = currency
        self.total_amount = total_amount
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


class Header:
    type: str
    text: str

    def __init__(self, type: str = None, text: str = None) -> None:
        self.type = type
        self.text = text


class Interactive:
    type: str
    header: Header
    body: Body
    footer: Body
    action: Action

    def __init__(self, type: str = None, header: Header = None, body: Body = None,
                 footer: Body = None, action: Action = None) -> None:
        self.type = type
        self.header = header
        self.body = body
        self.footer = footer
        self.action = action


class InteractivePaymentMessage:
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
