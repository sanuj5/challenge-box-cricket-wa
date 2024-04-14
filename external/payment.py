from abc import ABC, abstractmethod

from external.phone_pe import PhonepePayment
from external.razorpay import RazorpayPayment
from model.enums import PaymentProvider


class PaymentFactory:
    @staticmethod
    def get_payment_service(payment_provider: PaymentProvider, secrets):
        match payment_provider:
            case PaymentProvider.RAZORPAY:
                return RazorpayPayment(key_id=secrets.get("RAZORPAY_KEY_ID"),
                                       key_secret=secrets.get("RAZORPAY_KEY_SECRET"))
            case payment_provider.PHONEPE:
                return PhonepePayment(merchant_id=secrets.get("MERCHANT_ID"),
                                      salt_key=secrets.get("PROD_SALT_KEY"),
                                      salt_index=secrets.get("SALT_INDEX"))

class BasePayment(ABC):
    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def generate_payment_link(self, amount: int, unique_transaction_id, *args, **kwargs) -> str:
        pass

    @abstractmethod
    def validate_response(self, *args, **kwargs) -> bool:
        pass

    @abstractmethod
    def is_valid_vpa(self, vpa, *args, **kwargs) -> bool:
        pass

    @abstractmethod
    def send_payment_collection_request(self, vpa, amount,
                                        unique_transaction_id, *args, **kwargs) -> bool:
        pass
