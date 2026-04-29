from decimal import Decimal

from apps.billing.application.commands import CreatePaymentReceiptCommand
from apps.pagos.models import Payment
from apps.billing.models import Invoice


class PaymentReceiptDomainService:

    def create_receipt(self, payment: Payment, invoice: Invoice, previous_balance: Decimal, new_balance: Decimal):


        receipt = CreatePaymentReceiptCommand(
            payment=payment,
            invoice=invoice,
            student=payment.user,
            amount_paid=payment.amount,
            previous_balance=previous_balance,
            new_balance=new_balance,
            payment_method=payment.payment_method,
            payment_date=payment.created_at,
            currency=payment.currency,
        )

        return receipt