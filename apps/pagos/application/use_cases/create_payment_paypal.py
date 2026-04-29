from apps.orden_pagos.infrastructure.repository.payment_order_repository import PaymentOrderRepository


class CreatePaymentPaypalUseCase:
    def __init__(self, gateway):
        self.gateway = gateway
        self.payment_order_repository = PaymentOrderRepository()
    def execute(self, amount: float, currency: str, payment_order: int):
        return self.gateway.create_order(amount, currency, payment_order)