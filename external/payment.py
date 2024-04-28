import base64
import datetime as dt
import json
from abc import ABC, abstractmethod

from phonepe.sdk.pg.common.exceptions import ExpectationFailed
from phonepe.sdk.pg.env import Env
from phonepe.sdk.pg.payments.v1.models.request.pg_pay_request import PgPayRequest
from phonepe.sdk.pg.payments.v1.payment_client import PhonePePaymentClient

import razorpay
from logger import Logger
from model.enums import PaymentProvider


class PaymentFactory:
    @staticmethod
    def get_payment_service(payment_provider: PaymentProvider, secrets):
        match payment_provider:
            case PaymentProvider.RAZORPAY:
                return RazorpayPayment(key_id=secrets.get("RAZORPAY_KEY_ID"),
                                       key_secret=secrets.get("RAZORPAY_KEY_SECRET"),
                                       webhook_secret=secrets.get("RAZORPAY_WEBHOOK_SECRET"))
            case payment_provider.PHONEPE:
                return PhonepePayment(merchant_id=secrets.get("MERCHANT_ID"),
                                      salt_key=secrets.get("PROD_SALT_KEY"),
                                      salt_index=secrets.get("SALT_INDEX"))


class BasePayment(ABC):
    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def generate_payment_link(self, amount: int, unique_transaction_id, *args,
                              **kwargs) -> str:
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

    @abstractmethod
    def get_payment(self, token):
        pass


class PhonepePayment(BasePayment):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        merchant_id = kwargs.get("merchant_id")
        salt_key = kwargs.get("salt_key")
        salt_index = kwargs.get("salt_index")
        env = Env.PROD
        should_publish_events = True
        self.phonepe_client = PhonePePaymentClient(
            merchant_id, salt_key, salt_index, env, should_publish_events
        )
        self.s2s_callback_url = "https://challengecricket.in/api/payment"

    def generate_payment_link(self, amount: int, unique_transaction_id, *args,
                              **kwargs) -> str:
        # ui_redirect_url = "http://localhost:8080/success" =
        s2s_callback_url = "https://challengecricket.in/api/payment"
        amount = amount  # In PAISE
        id_assigned_to_user_by_merchant = "test_user_1"
        pay_page_request = PgPayRequest.pay_page_pay_request_builder(
            merchant_transaction_id=unique_transaction_id,
            amount=amount,
            merchant_user_id=id_assigned_to_user_by_merchant,
            callback_url=s2s_callback_url,
            redirect_mode="POST")
        pay_page_response = self.phonepe_client.pay(pay_page_request)
        pay_page_url = pay_page_response.data.instrument_response.redirect_info.url
        Logger.info(pay_page_url)
        return pay_page_url

    def validate_response(self, *args, **kwargs) -> dict:
        header = kwargs.get("header")
        response = kwargs.get("response")
        status = self.phonepe_client.verify_response(x_verify=header,
                                                     response=response)
        response_string = base64.b64decode(
            json.loads(response).get("response"))
        Logger.info(response_string)
        response_dict = json.loads(response_string)
        if not status:
            return None
        return {
            "success": response_dict.get("code") == "PAYMENT_SUCCESS",
            "amount": response_dict.get("data").get("amount"),
            "order_id": response_dict.get("data").get("merchantTransactionId"),
            "original_response": response_dict
        }

    def is_valid_vpa(self, vpa, *args, **kwargs) -> bool:
        Logger.info(f"Validating vpa {vpa}")
        try:
            pay_page_response = self.phonepe_client.validate_vpa(vpa)
            Logger.info(f"Status {pay_page_response.success}")
        except ExpectationFailed:
            return False
        return pay_page_response.success

    def send_payment_collection_request(self, vpa, amount,
                                        unique_transaction_id, *args, **kwargs) -> bool:
        Logger.info(f"Sending request to vpa {vpa} for amount {amount}")
        upi_collect_request_data = PgPayRequest.upi_collect_pay_request_builder(
            merchant_transaction_id=unique_transaction_id,
            merchant_order_id=unique_transaction_id,
            merchant_user_id=unique_transaction_id,
            amount=int(amount),
            vpa=vpa,
            callback_url=self.s2s_callback_url,
            device_os="IOS",
            callback_mode="POST",
            auto_failure_timeout=300)
        try:
            pay_page_response = self.phonepe_client.pay(upi_collect_request_data)
            Logger.info(f"Status {pay_page_response}")
        except ExpectationFailed:
            return False
        return pay_page_response.success

    def get_payment(self, token):
        pass


class RazorpayPayment(BasePayment):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        key_id = kwargs.get("key_id")
        key_secret = kwargs.get("key_secret")
        self.webhook_secret = kwargs.get("webhook_secret")
        self.client = razorpay.Client(auth=(key_id, key_secret))
        self.client.set_app_details(
            {"title": "CBC_TEST", "version": "1.0"})
        self.payment_link_expiry_in_minutes = 10
        self.callback_url = "https://challengecricket.in/api/payment"

    def generate_payment_link(self, amount: int, unique_transaction_id, *args,
                              **kwargs) -> str:
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
        result = self.client.utility.verify_webhook_signature(
            response, header, self.webhook_secret
        )
        if not result:
            return None
        return {
            "success": True,
            "amount": 1,
            "order_id": "xxx",
            "original_response": response
        }

    def is_valid_vpa(self, vpa, *args, **kwargs) -> bool:
        pass

    def send_payment_collection_request(self, vpa, amount,
                                        unique_transaction_id, *args, **kwargs) -> bool:
        pass

    def get_payment(self, token):
        return self.client.payment.fetch(token)
