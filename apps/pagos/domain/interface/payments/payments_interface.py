from abc import ABC, abstractmethod
from decimal import Decimal


class PaymentGateway(ABC):

    @abstractmethod
    def create_order(self, amount:float, currency: str, payment_order: int):
        pass

    @abstractmethod
    def capture_order(self, order_id):
        pass