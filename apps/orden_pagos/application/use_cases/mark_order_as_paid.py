from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.orden_pagos.domain.interface.repository.repository_interface import PaymentOrderRepositoryInterface
from apps.orden_pagos.models import PaymentOrder


class MarkOrderAsPaidUseCase:
    """
   Marca una orden como pagada usando el metodo mark_as_paid() del modelo.
    Transición: PENDING O ACTIVE → PAID
    """

    def __init__(self, repository: PaymentOrderRepositoryInterface):
        self.repository = repository

    @transaction.atomic
    def execute(self, order_id: int) -> PaymentOrder:

        payment_order = self.repository.get_by_id(order_id)

        if not payment_order:
            raise ValidationError({'order_id': _('Orden de pago no encontrada')})

        if payment_order.mark_as_paid():
            # Recargar la orden para obtener los cambios
            return self.repository.get_by_id(order_id)
        else:
            raise ValidationError({
                'status': _(
                    'No se puede marcar como pagada. Solo se pueden marcar como pagadas órdenes en estado PENDING o ACTIVE.')
            })
