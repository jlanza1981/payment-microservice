"""
Caso de uso: Validar token de pago y obtener la orden correspondiente.

Este caso de uso:
1. Valida el token firmado
2. Extrae el order_id del token
3. Verifica que la orden exista
4. Verifica que el link no haya expirado
5. Retorna la orden de pago si todo es válido
"""
from typing import Dict, Any
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.orden_pagos.domain.interface.repository.repository_interface import PaymentOrderRepositoryInterface
from apps.orden_pagos.infrastructure.services.payment_token_service import PaymentTokenService


class ValidatePaymentTokenUseCase:
    """
    Caso de uso: Validar token de enlace de pago.

    Valida que el token sea válido, no esté expirado, y retorna la orden de pago.
    """

    def __init__(self, repository: PaymentOrderRepositoryInterface, token_service: PaymentTokenService):
        self.repository = repository
        self.token_service = token_service

    def execute(self, token: str) -> Dict[str, Any]:
        """
        Valida el token y retorna la orden de pago si es válida.
        """
        # 1. Validar y decodificar el token
        try:
            token_data = self.token_service.validate_token(token)

        except ValueError as e:
            raise ValidationError({
                'token': str(e),
                'expired': True,
                'message': 'El enlace de pago ha expirado. Por favor, contacte a su asesor.'
            })

        # 2. Obtener el order_id del token
        order_id = token_data.get('order_id')

        # 3. Buscar la orden en la base de datos
        payment_order = self.repository.get_by_id(order_id)

        if not payment_order:
            raise ValidationError({
                'valid': False,
                'token': _('Orden de pago no encontrada'),
                'message': 'La orden de pago asociada a este enlace no existe.'
            })

        # 4. Validar que la orden pueda recibir pagos
        if payment_order.status == 'CANCELLED':
            raise ValidationError({
                'valid': False,
                'status': _(payment_order.status),
                'message': 'Esta orden de pago ha sido cancelada. Por favor, contacte a su asesor.'
            })

        if payment_order.status in ('PAID','EXONERATED','VERIFIED'):
            raise ValidationError({
                'valid': False,
                'status': _(payment_order.status),
                'message': 'Esta orden ya ha sido pagada en su totalidad.'
            })

        # 5. Validar que el link no haya sido consumido (si aplica)
        if payment_order.consumed:
            raise ValidationError({
                'valid': False,
                'status': _('consumed'),
                'message': 'Este enlace de pago ya fue utilizado. Contacte a su asesor si necesita un nuevo enlace.'
            })
        structure = payment_order.get_order_structure()
        # 6. Todo válido, retornar la orden
        return {
            'valid': True,
            'payment_order': structure,
            'expires_at': token_data.get('expires_at'),
            'message': 'Token válido'
        }

