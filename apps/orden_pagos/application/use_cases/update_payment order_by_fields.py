from apps.orden_pagos.application.use_cases import GetPaymentOrderByIdUseCase
from apps.orden_pagos.domain.interface.repository.repository_interface import PaymentOrderRepositoryInterface


class UpdatePaymentOrderByIdUseCase:
    def __init__(self, payment_repository: PaymentOrderRepositoryInterface):
        self.payment_order_repository = payment_repository

    def execute(self, payment_order_id, update_data):

        payment_order = GetPaymentOrderByIdUseCase(self.payment_order_repository).execute(payment_order_id)
        if not payment_order:
            raise ValueError(f"Payment with id {payment_order_id} not found")

        # Update the payment record with the new data
        payment_order_updated = self.payment_order_repository.save_order(payment_order, update_fields=update_data)
        return payment_order_updated