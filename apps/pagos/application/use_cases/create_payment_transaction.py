from apps.orden_pagos.application.use_cases import GetPaymentOrderByIdUseCase
from apps.orden_pagos.domain.interface.repository.repository_interface import PaymentOrderRepositoryInterface
from apps.pagos.application.commands import CreatePaymentTransactionCommand
from apps.pagos.domain.interface.repository.payment_repository_interface import PaymentRepositoryInterface


class CreatePaymentTransactionUseCase:
    def __init__(self, payment_repository: PaymentRepositoryInterface, payment_order_repository: PaymentOrderRepositoryInterface):
        self.payment_repository = payment_repository
        self.payment_order_repository = payment_order_repository
    def execute(self, payload: CreatePaymentTransactionCommand):
        print(f"Ejecutando CreatePaymentTransactionUseCase con payload: {payload}")
        payment_order = GetPaymentOrderByIdUseCase(self.payment_order_repository).execute(payload.payment_order)
        payload.payment_order = payment_order

        return self.payment_repository.save_payment_transaction(payload)