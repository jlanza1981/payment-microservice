from decimal import Decimal

from apps.billing.application.use_cases.get_invoice_by_id_with_relations import GetByIdWithRelations
from apps.billing.domain.interface.repository import InvoiceRepositoryInterface
from apps.orden_pagos.application.use_cases.save_payment_order import SavePaymentOrderUseCase
from apps.orden_pagos.domain.interface.repository.repository_interface import PaymentOrderRepositoryInterface
from apps.orden_pagos.models import PaymentOrder


class CreatePartialPaymentUsoCase:
    def __init__(self, invoice_repository: InvoiceRepositoryInterface, payment_order_repository: PaymentOrderRepositoryInterface):
        self.invoice_repository = invoice_repository
        self.payment_order_repository = payment_order_repository

    def execute(self, invoice_id:int, amount: Decimal):
        invoice = GetByIdWithRelations(self.invoice_repository).execute(invoice_id)
        payment_order_id = invoice.payment_order.id
        payment_order = SavePaymentOrderUseCase(self.payment_order_repository).execute(payment_order_id, amount)

        return payment_order