from phonepe.sdk.pg.common.exceptions import ExpectationFailed
from phonepe.sdk.pg.env import Env
from phonepe.sdk.pg.payments.v1.models.request.pg_pay_request import PgPayRequest
from phonepe.sdk.pg.payments.v1.payment_client import PhonePePaymentClient
from logger import Logger


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
        self.s2s_callback_url = "https://challengecricket.in/api/payment"

    def generate_payment_link(self, amount: int, unique_transaction_id) -> str:
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

    def validate_response(self, header, response) -> bool:
        return self.phonepe_client.verify_response(x_verify=header,
                                                   response=response)

    def is_valid_vpa(self, vpa) -> bool:
        Logger.info(f"Validating vpa {vpa}")
        try:
            pay_page_response = self.phonepe_client.validate_vpa(vpa)
            Logger.info(f"Status {pay_page_response.success}")
        except ExpectationFailed:
            return False
        return pay_page_response.success

    def send_payment_collection_request(self, vpa, amount,
                                        unique_transaction_id) -> bool:
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


if __name__ == '__main__':
    pg = PaymentGateway(merchant_id="CHALLENGECRONLINE",
                        salt_index=1,
                        salt_key="58414416-e374-4f71-be36-e21d70db8f79",
                        env=Env.PROD)
    # vpa = "1.sanuj-1@okhdfcbank"
    # if pg.is_valid_vpa(vpa):
    #     pay_page_response = pg.send_payment_collection_request(
    #         amount=100, vpa=vpa, unique_transaction_id=str(uuid.uuid4())[:-2]
    #     )
    #     Logger.info(f"Status {pay_page_response}")

    # pg.generate_payment_link(200, str(uuid.uuid4())[:-2])
    response = "{'response': 'eyJzdWNjZXNzIjp0cnVlLCJjb2RlIjoiUEFZTUVOVF9TVUNDRVNTIiwibWVzc2FnZSI6IllvdXIgcGF5bWVudCBpcyBzdWNjZXNzZnVsLiIsImRhdGEiOnsibWVyY2hhbnRJZCI6IkNIQUxMRU5HRUNST05MSU5FIiwibWVyY2hhbnRUcmFuc2FjdGlvbklkIjoiMTIzNCIsInRyYW5zYWN0aW9uSWQiOiJUMjMxMjI3MjMwODU5OTgzODY3NTcyMyIsImFtb3VudCI6MjAwLCJzdGF0ZSI6IkNPTVBMRVRFRCIsInJlc3BvbnNlQ29kZSI6IlNVQ0NFU1MiLCJwYXltZW50SW5zdHJ1bWVudCI6eyJ0eXBlIjoiVVBJIiwidXRyIjoiMzM2MTY2Mjk4OTc4IiwiY2FyZE5ldHdvcmsiOm51bGwsImFjY291bnRUeXBlIjoiU0FWSU5HUyJ9fX0='}"
    pg.validate_response(
        "fef4e02c688367b3fe5437ac710e626e9e3a788f58486053724130ccc1bf693f###1",
        response)
