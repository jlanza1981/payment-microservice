from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError


class PaymentOrderDomainService:

    @staticmethod
    def validate_order_status_transition(current_status: str, new_status: str) -> None:
        """
        Valida que la transición de estado sea válida.

        Args:
            current_status: Estado actual
            new_status: Estado nuevo

        Raises:
            ValidationError: Si la transición no es permitida
        """
        # Transiciones permitidas
        ALLOWED_TRANSITIONS = {
            'PENDING': ['PAID', 'CANCELLED'],
            'PAID': ['VERIFIED', 'CANCELLED'],
            'VERIFIED': ['CANCELLED'],
            'CANCELLED': [],  # No se puede cambiar desde cancelado
        }

        if current_status == new_status:
            return  # No hay cambio

        allowed = ALLOWED_TRANSITIONS.get(current_status, [])
        if new_status not in allowed:
            raise ValidationError({
                'status': _(f'No se puede cambiar de {current_status} a {new_status}')
            })

    @staticmethod
    def validate_program_duration_type(program_type_name: str, duration_type: str) -> None:
        nombre = (program_type_name or '').lower()

        if nombre == 'idiomas' and duration_type != 'w':
            raise ValidationError({
                'duration_type': _('Los programas de idiomas deben tener duración en semanas')
            })