from apps.billing.domain.interface.repository import InvoiceRepositoryInterface


class GetPaymentReceiptById:
    def __init__(self, payment_receipt_repository: InvoiceRepositoryInterface):
        self.payment_receipt_repository = payment_receipt_repository

    def execute(self, payment_receipt_id:int):
        return self.payment_receipt_repository.get_by_id(payment_receipt_id)