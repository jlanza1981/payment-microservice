from apps.billing.domain.interface.repository import InvoiceRepositoryInterface
from apps.pagos.domain.interface.repository.payment_repository_interface import PaymentRepositoryInterface


class CreateInvoiceCreditDetail:
    def __init__(self, invoice_repository: InvoiceRepositoryInterface, payment_repository: PaymentRepositoryInterface):
        self.invoice_repository = invoice_repository
        self.payment_repository = payment_repository

    def execute(self, invoice_id, payment_id, payment_receipt= None):
        invoice = self.invoice_repository.get_by_id(invoice_id)
        payment = self.payment_repository.get_by_id(payment_id)

        credit_detail = self.invoice_repository.create_invoice_credit_detail(
            invoice=invoice,
            payment=payment,
            payment_receipt=payment_receipt
        )
        return credit_detail