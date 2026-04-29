import logging
from decimal import Decimal

from django.core.exceptions import ValidationError

from apps.administrador.models import Usuarios
from apps.billing.application.commands import InvoiceDetailCommand
from apps.orden_pagos.infrastructure.repository.payment_order_repository import PaymentOrderRepository
from apps.user.infrastructure.repository.users_repository import UsersRepository
from apps.orden_pagos.models import PaymentOrder, PaymentConcept
logger = logging.getLogger(__name__)

class InvoiceDomainService:
    """
    Servicio de dominio para Invoice.
    Contiene lógica de negocio y validaciones relacionadas con facturas.
    """

    def __init__(self):
        self.repository_user = UsersRepository()
        self.repository_payment_order = PaymentOrderRepository()

    @staticmethod
    def validate_invoice_creation(
          student: Usuarios,
          payment_order: PaymentOrder,
          invoice_details: list[InvoiceDetailCommand]
    ) -> bool:
        # Validar que el estudiante esté activo
        if not student.is_active:
            error_msg = f"Validación fallida: El estudiante {student.get_full_name()} no está activo"
            logger.error(error_msg)
            return False
            
        # Validar que la orden de pago no esté cancelada
        if payment_order.status == 'CANCELLED':
            error_msg = f"La orden de pago {payment_order.order_number} está cancelada"
            logger.error(error_msg)
            return False
            
        # Validar que la orden de pago no esté completamente pagada
        if payment_order.status == 'PAID':
            error_msg = f"La orden de pago {payment_order.order_number} ya está completamente pagada"
            logger.error(error_msg)
            return False

        # Validar que haya al menos un detalle
        if not invoice_details or len(invoice_details) == 0:
            error_msg = "La factura debe tener al menos un detalle"
            logger.error(error_msg)
            return False

        # Validar montos positivos
        for detail in invoice_details:
            quantity = detail.quantity
            unit_price = detail.unit_price or Decimal('0.00')

            if quantity <= 0:
                error_msg = f"La cantidad debe ser mayor a 0 (detalle: {detail.payment_concept_id})"
                logger.error(error_msg)
                return False

            if unit_price <= 0:
                error_msg = f"El precio unitario debe ser mayor a 0 (detalle: {detail.payment_concept_id})"
                logger.error(error_msg)
                return False

        return True

    @staticmethod
    def validate_invoice_cancellation(invoice) -> bool:
        # No se puede anular una factura ya anulada
        if invoice.status == 'A':
            raise ValidationError(f"La factura {invoice.invoice_number} ya está anulada")

        # No se puede anular una factura completamente pagada sin reembolso
        if invoice.status == 'P' and invoice.balance_due <= 0:
            raise ValidationError(
                f"La factura {invoice.invoice_number} está completamente pagada. "
                "Para anularla debe procesarse un reembolso primero."
            )

        return True

    @staticmethod
    def calculate_invoice_total(
          subtotal: Decimal,
          taxes: Decimal,
          total_discounts: Decimal = Decimal('0.00')
    ) -> Decimal:
        return subtotal - total_discounts + taxes

    @staticmethod
    def validate_payment_concept_requires_program(
          payment_concept: PaymentConcept,
          payment_order: PaymentOrder
    ) -> bool:
        if payment_concept.requires_program:
            # Verificar si la orden tiene programa asociado
            has_program = hasattr(payment_order, 'payment_order_program') and \
                          payment_order.payment_order_program is not None

            if not has_program:
                raise ValidationError(
                    f"El concepto '{payment_concept.name}' requiere que la orden de pago "
                    f"tenga un programa asociado."
                )

        return True
