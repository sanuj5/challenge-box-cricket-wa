from abc import ABC, abstractmethod


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
