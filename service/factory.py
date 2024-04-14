from model.enums import MessageType, Screen, PaymentProvider
from message_processor import TextMessageProcessor, InteractiveMessageProcessor, \
    NfmMessageProcessor
import flow_processing as fp
from payment.phone_pe import PhonepePayment
from payment.razorpay import RazorpayPayment


class MessageFactory:
    def __init__(self):
        self.text_message_processor = TextMessageProcessor()
        self.interactive_message_processor = InteractiveMessageProcessor()
        self.nfm_reply_processor = NfmMessageProcessor()

    def process(self, message, message_type: MessageType):
        match message_type:
            case MessageType.TEXT:
                message_service = self.text_message_processor
            case MessageType.INTERACTIVE:
                message_service = self.interactive_message_processor
            case MessageType.NFM_REPLY:
                message_service = self.nfm_reply_processor
            case _:
                return "Message type not supported", 200
        message_service.process_message(message)
        return "", 200


class FlowFactory:

    def __init__(self):
        self.date_screen_processor = fp.DateScreenProcessor()
        self.slot_screen_processor = fp.SlotScreenProcessor()
        self.booking_confirmation_processor = fp.BookingConfirmationProcessor()

    def process(self, message, screen: Screen):
        match screen:
            case Screen.DATE_SELECTION:
                service = self.date_screen_processor
            case Screen.SLOT_SELECTION:
                service = self.slot_screen_processor
            case Screen.BOOKING_CONFIRMATION:
                service = self.booking_confirmation_processor
            case _:
                raise ValueError("Invalid screen")
        return service.process_flow_request(message)


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
