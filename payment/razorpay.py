import uuid

from payment.payment import BasePayment
import razorpay
from logger import Logger
import datetime as dt


class RazorpayPayment(BasePayment):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        key_id = kwargs.get("key_id")
        key_secret = kwargs.get("key_secret")
        self.client = razorpay.Client(auth=(key_id, key_secret))
        self.client.set_app_details(
            {"title": "CBC_TEST", "version": "1.0"})
        self.payment_link_expiry_in_minutes = 10
        self.callback_url = "https://challengecricket.in/api/payment"

    def generate_payment_link(self, amount: int, unique_transaction_id, *args, **kwargs) -> str:
        expire_by = dt.datetime.now() + dt.timedelta(
                minutes=self.payment_link_expiry_in_minutes
            )
        customer = kwargs.get('customer', None)
        notes = kwargs.get('customer', {"booking": "CBC"})
        link = self.client.payment_link.create({
            "amount": amount * 100,  # Amount in paisa
            "currency": "INR",
            "accept_partial": False,
            "description": "Test",
            "customer": customer,
            "reminder_enable": False,
            "notes": notes,
            "callback_url": self.callback_url,
            "callback_method": "get",
            "reference_id": unique_transaction_id,
            "expire_by": int(expire_by.timestamp())
        })
        Logger.info(link)
        return link

    def validate_response(self, header, response, *args, **kwargs) -> dict:
        pass

    def is_valid_vpa(self, vpa, *args, **kwargs) -> bool:
        pass

    def send_payment_collection_request(self, vpa, amount,
                                        unique_transaction_id, *args, **kwargs) -> bool:
        pass


if __name__ == '__main__':
    service = RazorpayPayment()
    service.generate_payment_link(100, str(uuid.uuid4())[:-2].replace("-", ""))
