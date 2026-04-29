


class FindInvoiceByPaymentOrder:
    def __init__(self, repository):
        self.repository = repository

    def execute(self, payment_order_id: int):
        return self.repository.get_invoices_by_payment_order(payment_order_id)
