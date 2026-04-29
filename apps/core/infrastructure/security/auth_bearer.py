"""
Autenticación personalizada para Django Ninja.
Reutiliza la lógica de ExpiringTokenAuthentication de DRF.
"""
from typing import Optional

from django.contrib.auth.models import User
from ninja.security import HttpBearer

from api.DRF.Authentication import ExpiringTokenAuthentication


class AuthBearer(HttpBearer):
    """
    Autenticación Bearer para Django Ninja.
    Reutiliza la lógica de ExpiringTokenAuthentication.
    """

    def authenticate(self, request, token: str) -> Optional[User]:
        """
        Autenticar usuario mediante token Bearer.

        Args:
            request: HttpRequest de Django
            token: Token de autenticación

        Returns:
            Usuario autenticado o None si el token es inválido
        """
        # Crear instancia del autenticador DRF
        auth = ExpiringTokenAuthentication()

        try:
            # Validar token usando la lógica existente
            user_auth_tuple = auth.authenticate_credentials(token)

            if user_auth_tuple is not None:
                user, auth_token = user_auth_tuple
                # Asignar usuario y token al request
                request.user = user
                request.auth = auth_token
                return user
        except Exception:
            pass

        return None
