from typing import Dict, Any

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.orden_pagos.domain.interface.repository.repository_interface import PaymentOrderRepositoryInterface


class VerifyOrderUseCase:
    """
    Caso de uso: Verificar una orden por tesorería.
    Transición: PAID → VERIFIED
    """

    def __init__(self, repository: PaymentOrderRepositoryInterface, payment_order_by_id_uc):
        self.repository = repository
        self.payment_order_by_id_uc = payment_order_by_id_uc

    @transaction.atomic
    def execute(self, command) -> Dict[str, Any]:
        # Obtener la orden
        payment_order = self.payment_order_by_id_uc.execute(command.order_id)

        if not payment_order:
            raise ValidationError({'order_id': _('Orden de pago no encontrada')})

        if payment_order.verify():
            payment_order.refresh_from_db()
            return payment_order
        else:
            raise ValidationError({
                'status': _('No se puede verificar. Solo se pueden verificar órdenes en estado PAID.')
            })
