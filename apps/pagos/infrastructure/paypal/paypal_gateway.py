from .client import PayPalClient
from ...domain.interface.payments.payments_interface import PaymentGateway


class PayPalGateway(PaymentGateway):

    def __init__(self):
        self.client = PayPalClient()

    def create_order(self, amount, currency, payment_order):
        return self.client.create_order(amount, currency, payment_order)

    def capture_order(self, order_id):
        return self.client.capture_order(order_id)