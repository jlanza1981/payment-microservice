from decimal import Decimal

from apps.orden_pagos.application.use_cases import GetPaymentOrderByIdUseCase
from apps.orden_pagos.domain.interface.repository.repository_interface import PaymentOrderRepositoryInterface


class SavePaymentOrderUseCase:
    def __init__(self, payment_order_repository: PaymentOrderRepositoryInterface):
        self.payment_order_repository = payment_order_repository

    def execute(self,payment_order_id: int, amount:Decimal):

        payment_order = GetPaymentOrderByIdUseCase(self.payment_order_repository).execute(payment_order_id)
        
        # Update the suggested_payment_amount field
        payment_order.suggested_payment_amount = amount

        # Save with only the fields that changed
        saved = self.payment_order_repository.save_order(payment_order, ['suggested_payment_amount', 'updated_at'])

        return saved