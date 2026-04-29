"""
Caso de Uso: Crear Recibo de Pago

Maneja la creación de recibos para pagos parciales (abonos).
Separado del webhook principal para mantener el código modular.

Author: Sistema LC Mundo
Date: 2026-03-02
"""
import logging

from apps.billing.application.commands import CreatePaymentReceiptCommand
from apps.billing.domain.interface.repository import InvoiceRepositoryInterface
from apps.pagos.domain.interface.repository.payment_repository_interface import PaymentRepositoryInterface

logger = logging.getLogger(__name__)


class CreatePaymentReceiptUseCase:
    """
    Caso de uso para crear recibos de abono.
    """

    def __init__(self, invoice_repository: InvoiceRepositoryInterface, payment_repository: PaymentRepositoryInterface):
        self.invoice_repository = invoice_repository
        self.payment_repository = payment_repository

    def execute(self, payment_id, invoice_id):
        print('payment_id', payment_id)
        print('invoice_id', invoice_id)
        invoice = self.invoice_repository.get_by_id(invoice_id)
        payment = self.payment_repository.get_by_id(payment_id)
        print('invoice', invoice)
        print('payment', payment)
        print('payment', payment)
        # Solo crear recibo si es un ABONO (queda saldo pendiente)
        print('balance_due', invoice.balance_due)
        if invoice.balance_due <= 0:
            logger.info(
                f"Pago {payment.payment_number} completó la factura {invoice.invoice_number}. "
                f"No se genera recibo de abono."
            )
            return None

        previous_balance, new_balance = self.invoice_repository.calculate_receipt_balances(
            invoice=invoice,
            payment_amount=payment.amount
        )

        try:
            # Crear el recibo usando el repositorio
            receipt_data = CreatePaymentReceiptCommand(
                payment=payment.id,
                invoice=invoice.id,
                student=payment.user.id,
                amount_paid=payment.amount,
                previous_balance=previous_balance,
                new_balance=new_balance,
                payment_method=payment.payment_method,
                payment_date=payment.created_at,
                currency=payment.currency,
                notes=f'Recibo de abono generado automáticamente para pago {payment.payment_number}'
            )
            print('receipt_data', receipt_data)
            receipt = self.invoice_repository.create_payment_receipt(receipt_data)

            logger.info(
                f"Recibo de abono {receipt.receipt_number} creado exitosamente. "
                f"Monto: ${payment.amount}"
            )

            return receipt

        except Exception as e:
            logger.error(
                f"Error al crear recibo para pago {payment.payment_number}: {str(e)}",
                exc_info=True
            )
            return None
