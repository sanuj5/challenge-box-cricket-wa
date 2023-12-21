import base64
import json

from phonepe.sdk.pg.common.exceptions import ExpectationFailed
from phonepe.sdk.pg.payments.v1.models.request.pg_pay_request import PgPayRequest
from phonepe.sdk.pg.payments.v1.payment_client import PhonePePaymentClient
from phonepe.sdk.pg.env import Env


class PaymentGateway:
    def __init__(self, merchant_id, salt_key, salt_index, env: Env):
        self.merchant_id = merchant_id
        self.salt_key = salt_key
        self.salt_index = salt_index
        self.env = env
        should_publish_events = True
        self.phonepe_client = PhonePePaymentClient(
            merchant_id, salt_key, salt_index, env, should_publish_events
        )

    def generate_payment_link(self, amount: int, unique_transaction_id) -> str:
        # ui_redirect_url = "http://localhost:8080/success" =
        s2s_callback_url = "https://quixotic-booth-407213.el.r.appspot.com/payment"
        amount = amount  # In PAISE
        id_assigned_to_user_by_merchant = "test_user_1"
        pay_page_request = PgPayRequest.pay_page_pay_request_builder(
            merchant_transaction_id=unique_transaction_id,
            amount=amount,
            merchant_user_id=id_assigned_to_user_by_merchant,
            callback_url=s2s_callback_url)
        pay_page_response = self.phonepe_client.pay(pay_page_request)
        pay_page_url = pay_page_response.data.instrument_response.redirect_info.url
        print(pay_page_url)
        return pay_page_url

    def validate_response(self, header, response) -> str:
        is_valid = self.phonepe_client.verify_response(x_verify=header, response=response)
        print(f"Payment Request is {is_valid}.")
        if not is_valid:
            return "Invalid request"
        return base64.b64decode(json.loads(response).get("response")).decode("utf-8")

    def is_valid_vpa(self, vpa) -> bool:
        try:
            pay_page_response = self.phonepe_client.validate_vpa(vpa)
        except ExpectationFailed:
            return False
        return pay_page_response.success

