from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.orden_pagos.domain.interface.repository.repository_interface import PaymentOrderRepositoryInterface
from apps.orden_pagos.models import PaymentOrder


class GetPaymentOrderByNumberUseCase:
    """
    Caso de uso: Obtener una orden de pago por número de orden.

    Delega la consulta al repositorio para mantener la separación de responsabilidades.
    """

    def __init__(self, repository: PaymentOrderRepositoryInterface):
        self.repository = repository

    def execute(self, order_number: str) -> PaymentOrder:
        """
        Obtiene una orden de pago por su número.

        Args:
            order_number: Número de orden a buscar

        Returns:
            PaymentOrder: Orden encontrada

        Raises:
            ValidationError: Si la orden no existe
        """
        payment_order = self.repository.get_by_order_number(order_number)

        if not payment_order:
            raise ValidationError({'order_number': _('Orden de pago no encontrada')})

        return payment_order
