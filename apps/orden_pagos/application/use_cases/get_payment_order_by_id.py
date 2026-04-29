from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.orden_pagos.domain.interface.repository.repository_interface import PaymentOrderRepositoryInterface
from apps.orden_pagos.models import PaymentOrder


class GetPaymentOrderByIdUseCase:
    """
    Caso de uso: Obtener una orden de pago por ID.

    Delega la consulta al repositorio para mantener la separación de responsabilidades.
    """

    def __init__(self, repository: PaymentOrderRepositoryInterface):
        self.repository = repository

    def execute(self, order_id: int) -> PaymentOrder:
        """
        Obtiene una orden de pago con todas sus relaciones.
        """
        payment_order = self.repository.get_by_id(order_id)

        if not payment_order:
            raise ValidationError({'order_id': _('Orden de pago no encontrada')})

        return payment_order
