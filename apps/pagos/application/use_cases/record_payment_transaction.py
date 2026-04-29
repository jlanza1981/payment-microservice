from apps.orden_pagos.domain.interface.repository.repository_interface import PaymentOrderRepositoryInterface
from apps.pagos.application.use_cases.create_payment_transaction import CreatePaymentTransactionUseCase
from apps.pagos.domain.interface.repository.payment_repository_interface import PaymentRepositoryInterface


class RecordPaymentTransaction:
    def __init__(self, payment_repository: PaymentRepositoryInterface, payment_order_repository: PaymentOrderRepositoryInterface):
        self.payment_repository = payment_repository
        self.payment_order_repository = payment_order_repository

    def execute(self, command):
        payment_transaction = self.payment_repository.get_payment_transaction(
            command.paypal_order_id,
            command.payment_order
        )

        if not payment_transaction:
            return CreatePaymentTransactionUseCase(
                self.payment_repository,
                self.payment_order_repository
            ).execute(command)

        return  None

