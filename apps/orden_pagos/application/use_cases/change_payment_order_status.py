from django.db import transaction
from pip._internal.utils._jaraco_text import _
from rest_framework.exceptions import ValidationError

from apps.orden_pagos.models import PaymentOrder


class ChangeOrderStatusUseCase:
    """
    Caso de uso: Cambiar el estado de una orden de pago.

    Valida que la transición de estado sea permitida.
    """

    @transaction.atomic
    def execute(self, command):
        """
        Cambia el estado de una orden.

        Args:
            command: ChangeOrderStatusCommand

        Returns:
            PaymentOrder: Orden con estado actualizado

        Raises:
            ValidationError: Si la transición no es válida
        """
        from apps.orden_pagos.domain.interface.services import PaymentOrderDomainService

        try:
            payment_order = PaymentOrder.objects.select_for_update().get(id=command.order_id)
        except PaymentOrder.DoesNotExist:
            raise ValidationError({'order_id': _('Orden de pago no encontrada')})

        # Validar transición de estado
        domain_service = PaymentOrderDomainService()
        domain_service.validate_order_status_transition(
            payment_order.status,
            command.new_status
        )

        payment_order.status = command.new_status
        payment_order.save(update_fields=['status', 'updated_at'])

        return payment_order
