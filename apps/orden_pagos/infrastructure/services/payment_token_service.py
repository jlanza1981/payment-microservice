"""
Servicio para generar y validar tokens de pago firmados.

Este servicio usa itsdangerous para crear tokens que contienen:
- ID de la orden de pago
- Fecha de expiración

Ventajas:
- No necesita almacenar tokens en BD
- Token contiene toda la información necesaria
- Firmado criptográficamente (no puede ser manipulado)
- Stateless y escalable
"""
from datetime import datetime
from typing import Dict, Optional
from django.conf import settings
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired


class PaymentTokenService:
    """
    Servicio de dominio para manejar tokens de pago firmados.

    Genera tokens que contienen:
    - order_id: ID de la orden de pago
    - expires_at: Fecha de expiración

    El token está firmado con SECRET_KEY de Django para prevenir manipulación.
    """

    def __init__(self):
        # Usar SECRET_KEY de Django como clave de firma
        self.serializer = URLSafeTimedSerializer(
            secret_key=settings.SECRET_KEY,
            salt='payment-order-token'  # Salt adicional para tokens de pago
        )

    def generate_token(self, order_id: int, link_expires_at) -> Dict[str, any]:
        """
        Genera un token firmado que contiene el ID de la orden y la fecha de expiración.

        Args:
            order_id: ID de la orden de pago
            link_expires_at: fecha de expiración (puede ser datetime o date)

        Returns:
            Dict con 'token' y 'expires_at'
        """
        # Convertir a datetime si es date
        if hasattr(link_expires_at, 'date'):
            # Es un datetime
            expires_at_date = link_expires_at.date()
            expires_at_iso = link_expires_at.isoformat()
        else:
            # Es un date
            expires_at_date = link_expires_at
            # Convertir date a datetime para el ISO format
            expires_at_iso = datetime.combine(link_expires_at, datetime.min.time()).isoformat()

        # Payload que se cifra en el token
        payload = {
            'order_id': order_id,
            'expires_at': expires_at_iso
        }

        # Generar token firmado
        token = self.serializer.dumps(payload)

        return {
            'token': token,
            'expires_at': expires_at_date
        }

    def validate_token(self, token: str) -> Dict[str, any]:
        """
        Valida un token y extrae su contenido.

        Args:
            token: Token firmado a validar

        Returns:
            Dict con 'order_id', 'expires_at', 'is_valid'

        Raises:
            ValueError: Si el token es inválido o ha expirado
        """
        try:
            # Decodificar el token
            payload = self.serializer.loads(token)

            # Extraer datos
            order_id = payload.get('order_id')
            expires_at_str = payload.get('expires_at')

            if not order_id or not expires_at_str:
                raise ValueError('Token inválido: datos incompletos')

            # Parsear fecha de expiración
            expires_at = datetime.fromisoformat(expires_at_str)

            # Verificar si el token ha expirado
            if datetime.now() > expires_at:
                raise ValueError('El enlace de pago ha expirado. Por favor, contacte a su asesor.')

            return {
                'order_id': order_id,
                'expires_at': expires_at.date(),
                'is_valid': True
            }

        except SignatureExpired:
            raise ValueError('El token ha expirado por tiempo máximo de firma.')
        except BadSignature:
            raise ValueError('Token inválido o manipulado.')
        except Exception as e:
            raise ValueError(f'Error validando token: {str(e)}')

    def decode_token_without_validation(self, token: str) -> Optional[Dict[str, any]]:
        """
        Decodifica un token sin validar la expiración (útil para debug).

        Args:
            token: Token firmado

        Returns:
            Dict con el payload o None si no se puede decodificar
        """
        try:
            payload = self.serializer.loads(token)
            return payload
        except Exception:
            return None

