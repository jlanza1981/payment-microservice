from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.orden_pagos.domain.interface.repository.repository_interface import PaymentOrderRepositoryInterface
from apps.orden_pagos.models import PaymentOrder


class GetPaymentOrderByTokenUseCase:
    """
    Caso de uso: Obtener una orden de pago por ID.

    Delega la consulta al repositorio para mantener la separación de responsabilidades.
    """

    def __init__(self, repository: PaymentOrderRepositoryInterface):
        self.repository = repository

    def execute(self, token: str) -> PaymentOrder:
        payment_order = self.repository.get_payment_order_by_token(token)

        if not payment_order:
            raise ValidationError({'token': _('Orden de pago no encontrada')})

        return payment_order
