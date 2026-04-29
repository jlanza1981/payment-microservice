from typing import Dict, Any

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.orden_pagos.domain.interface.repository.repository_interface import PaymentOrderRepositoryInterface


class CancelOrderUseCase:
    """
    Caso de uso: Anular una orden de pago.
    Transición: PENDING → CANCELLED
    """

    def __init__(self, repository_payment_order: PaymentOrderRepositoryInterface, payment_order_uc):
        self.repository_payment_order = repository_payment_order
        self.payment_order_uc = payment_order_uc

    @transaction.atomic
    def execute(self, data) -> Dict[str, Any]:

        # Obtener la orden
        payment_order = self.payment_order_uc.execute(data.order_id)

        if not payment_order:
            raise ValidationError({'order_id': _('Orden de pago no encontrada')})

        if payment_order.cancel():
            payment_order.refresh_from_db()
            return payment_order
        else:
            raise ValidationError({
                'status': _('No se puede anular. Solo se pueden anular órdenes en estado PENDING.')
            })
