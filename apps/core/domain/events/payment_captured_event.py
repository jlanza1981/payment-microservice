"""
Domain Events para Payment Providers.
Eventos que comunican cambios importantes en el dominio de pagos.
"""
from typing import Optional
from decimal import Decimal

from apps.core.domain.events.base_event import DomainEvent


class PaymentCapturedEvent(DomainEvent):
    """
    Evento emitido cuando un pago es capturado exitosamente por un proveedor.

    Este evento indica que:
    - El dinero fue confirmado por el proveedor (PayPal, Stripe, etc.)
    - Se creó/actualizó una factura
    - Se registró el pago en el sistema

    Otros bounded contexts pueden reaccionar a este evento para:
    - Enviar emails de confirmación (billing)
    - Actualizar reportes (analytics)
    - Registrar auditoría (compliance)
    """

    def __init__(
        self,
        invoice_id: int,
        payment_id: Optional[int],
        payment_receipt_id: Optional[int],
        amount: Decimal,
        currency: str,
        is_full_payment: bool,
        invoice_number: str,
        payment_provider: str = 'paypal',
        capture_id: Optional[str] = None
    ):
        super().__init__()
        self.invoice_id = invoice_id
        self.payment_id = payment_id
        self.payment_receipt_id = payment_receipt_id
        self.amount = amount
        self.currency = currency
        self.is_full_payment = is_full_payment
        self.invoice_number = invoice_number
        self.payment_provider = payment_provider
        self.capture_id = capture_id

    def _get_event_data(self):
        """Override para serialización correcta de Decimal"""
        return {
            'invoice_id': self.invoice_id,
            'payment_id': self.payment_id,
            'payment_receipt_id': self.payment_receipt_id,
            'amount': str(self.amount),  # Convertir Decimal a string para JSON
            'currency': self.currency,
            'is_full_payment': self.is_full_payment,
            'invoice_number': self.invoice_number,
            'payment_provider': self.payment_provider,
            'capture_id': self.capture_id
        }

    def __str__(self):
        return (
            f"PaymentCaptured(invoice={self.invoice_number}, "
            f"amount={self.amount} {self.currency}, "
            f"full_payment={self.is_full_payment})"
        )


class PaymentFailedEvent(DomainEvent):
    """
    Evento emitido cuando un pago falla o es rechazado.

    Permite que otros contextos reaccionen a fallos de pago:
    - Notificar al usuario (notifications)
    - Registrar intentos fallidos (fraud_detection)
    - Actualizar métricas (analytics)
    """

    def __init__(
        self,
        payment_order_id: int,
        reason: str,
        amount: Decimal,
        currency: str,
        payment_provider: str = 'paypal',
        error_code: Optional[str] = None
    ):
        super().__init__()
        self.payment_order_id = payment_order_id
        self.reason = reason
        self.amount = amount
        self.currency = currency
        self.payment_provider = payment_provider
        self.error_code = error_code

    def _get_event_data(self):
        return {
            'payment_order_id': self.payment_order_id,
            'reason': self.reason,
            'amount': str(self.amount),
            'currency': self.currency,
            'payment_provider': self.payment_provider,
            'error_code': self.error_code
        }


class PaymentRefundedEvent(DomainEvent):
    """
    Evento emitido cuando se procesa un reembolso.

    Permite que billing y otros contextos reaccionen a reembolsos:
    - Crear nota de crédito (billing)
    - Notificar al cliente (notifications)
    - Actualizar contabilidad (accounting)
    """

    def __init__(
        self,
        payment_id: int,
        invoice_id: int,
        refund_amount: Decimal,
        currency: str,
        refund_reason: str,
        payment_provider: str = 'paypal',
        refund_id: Optional[str] = None
    ):
        super().__init__()
        self.payment_id = payment_id
        self.invoice_id = invoice_id
        self.refund_amount = refund_amount
        self.currency = currency
        self.refund_reason = refund_reason
        self.payment_provider = payment_provider
        self.refund_id = refund_id

    def _get_event_data(self):
        return {
            'payment_id': self.payment_id,
            'invoice_id': self.invoice_id,
            'refund_amount': str(self.refund_amount),
            'currency': self.currency,
            'refund_reason': self.refund_reason,
            'payment_provider': self.payment_provider,
            'refund_id': self.refund_id
        }

