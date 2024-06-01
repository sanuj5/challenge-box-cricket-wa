import time
import datetime

from dateutil.relativedelta import relativedelta

import model.interactive_message as im
import model.interactive_payment_message as ipm
import model.interactive_payment_message_gw as ipm_gw
import model.interactive_flow_message as ifm
import model.text_message as tm
import model.order_confirmation as oc
from model.enums import Screen, InteractiveRequestType


class MessageBuilderService:
    date_format = "%d %b %Y"
    final_confirmation_message = """
Your booking is confirmed.

*Date:* {selected_date}
*Slots:* 
{slots}

_Enjoy the game!_
"""

    def __init__(self):
        pass

    @staticmethod
    def get_interactive_message(mobile: str,
                                message_body: str) -> im.InteractiveMessage:
        buttons = list()
        buttons.append(
            im.Button(reply=im.Reply(
                id=InteractiveRequestType.NEW_BOOKING.value, title="New Booking"
            ))
        )
        buttons.append(
            im.Button(reply=im.Reply(
                id=InteractiveRequestType.VIEW_BOOKING.value, title="View Bookings"
            ))
        )
        # buttons.append(
        #     im.Button(reply=im.Reply(id="CANCEL_BOOKING", title="Cancel Bookings"))
        # )

        action = im.Action()
        action.buttons = buttons

        body = im.Body()
        body.text = message_body

        interactive = im.Interactive()
        interactive.type = "button"
        interactive.body = body
        interactive.action = action

        message = im.InteractiveMessage()
        message.to = mobile
        message.type = "interactive"
        message.messaging_product = "whatsapp"
        message.interactive = interactive
        return message

    @staticmethod
    def get_interactive_flow_message(mobile: str,
                                     message_body: str,
                                     parameters: ifm.Parameter) -> ifm.InteractiveFlowMessage:
        action = ifm.Action()
        action.name = "flow"
        action.parameters = parameters

        body = ifm.Body()
        body.text = message_body

        interactive = ifm.Interactive()
        interactive.type = "flow"
        interactive.body = body
        interactive.action = action

        message = ifm.InteractiveFlowMessage()
        message.to = mobile
        message.type = "interactive"
        message.messaging_product = "whatsapp"
        message.interactive = interactive
        return message

    @staticmethod
    def get_final_text_message(mobile, _id, body):
        text = tm.Text()
        text.body = body
        text_message = tm.TextMessage()
        text_message.messaging_product = "whatsapp"
        text_message.recipient_type = "individual"
        text_message.to = mobile
        text_message.type = "text"
        text_message.text = text
        return text_message

    # https://developers.facebook.com/docs/whatsapp/flows/gettingstarted/sendingaflow
    @staticmethod
    def get_initial_screen_param(flow_id, flow_token, mode: str = "draft"):
        payload = dict()
        data = dict()
        current_date = datetime.datetime.today()
        max_date = current_date + relativedelta(months=+2)
        data["min_date"] = str(int(time.mktime(current_date.timetuple()) * 1000))
        data["max_date"] = str(int(time.mktime(max_date.timetuple()) * 1000))
        payload["screen"] = Screen.DATE_SELECTION.value
        payload["data"] = data
        parameter = ifm.Parameter()
        parameter.mode = mode
        parameter.flow_message_version = "3"
        parameter.flow_token = flow_token
        parameter.flow_cta = "Book New Slot"
        parameter.flow_id = flow_id
        parameter.flow_action = "navigate"
        parameter.flow_action_payload = payload
        return parameter

    @staticmethod
    def get_interactive_payment_message(mobile: str,
                                        message_body: str,
                                        payment_uri: str,
                                        payment_amount: int,
                                        slots: list,
                                        reference_id: str) -> ipm.InteractivePaymentMessage:
        total_amount = ipm.TotalAmount(value=payment_amount)
        tax_discount = ipm.Discount()

        item = ipm.Item()
        item.amount = total_amount
        item.quantity = len(slots)

        order = ipm.Order()
        order.subtotal = total_amount
        order.tax = tax_discount
        order.items = [item]

        parameters = ipm.Parameters()
        parameters.total_amount = total_amount
        parameters.order = order
        parameters.payment_settings = [
            ipm.PaymentSetting(payment_link=ipm.PaymentLink(payment_uri))
        ]
        parameters.reference_id = reference_id

        action = ipm.Action(name="review_and_pay", parameters=parameters)
        header = ipm.Header("text", "Almost there for your booking!")
        body = ipm.Body(message_body)
        interactive = ipm.Interactive(type="order_details",
                                      header=header,
                                      body=body,
                                      footer=None,
                                      action=action)

        message = ipm.InteractivePaymentMessage()
        message.to = mobile
        message.interactive = interactive
        return message

    @staticmethod
    def get_interactive_payment_message_gw(
            mobile: str,
            message_body: str,
            payment_amount: int,
            reference_id: str,
            amount_offset: int) -> ipm_gw.InteractivePaymentMessage:

        total_amount = ipm_gw.TotalAmount(value=payment_amount, offset=amount_offset)
        tax_discount = ipm_gw.Tax()

        item = ipm_gw.Item()
        item.amount = total_amount
        item.quantity = 1
        expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=5)

        expiration = ipm_gw.Expiration(
            timestamp=str(int(time.mktime(expiry_time.timetuple()))),
            description="Payment not completed within 5 minutes, hence expired!!"
        )

        order = ipm_gw.Order()
        order.subtotal = total_amount
        order.tax = tax_discount
        order.items = [item]
        order.expiration = expiration

        parameters = ipm_gw.Parameters()
        parameters.total_amount = total_amount
        parameters.order = order
        parameters.payment_settings = [ipm_gw.PaymentSetting(
            payment_gateway=ipm_gw.PaymentGateway())
        ]
        parameters.reference_id = reference_id

        action = ipm_gw.Action(name="review_and_pay", parameters=parameters)
        header = ipm_gw.Header()
        body = ipm_gw.Body(message_body)
        interactive = ipm_gw.Interactive(type="order_details",
                                         header=header,
                                         body=body,
                                         footer=None,
                                         action=action)

        message = ipm_gw.InteractivePaymentMessage()
        message.to = mobile
        message.interactive = interactive
        return message

    @staticmethod
    def get_order_confirmation_message(mobile: str, message: str, token: str):
        order = oc.Order(status="completed", description="Slot booking is confirmed.")
        parameters = oc.Parameters(reference_id=token, order=order)
        action = oc.Action(name="review_order", parameters=parameters)
        interactive = oc.Interactive(type="order_status",
                                     body=oc.Body(message),
                                     action=action)
        message = oc.OrderConfirmation()
        message.to = mobile
        message.interactive = interactive
        return message
