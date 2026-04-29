"""
Rate limiting middleware para proteger endpoints públicos.
Previene ataques de fuerza bruta en validación de tokens.
"""

import time
from collections import defaultdict
from django.core.cache import cache
from django.http import JsonResponse
from functools import wraps


class RateLimiter:
    """
    Rate limiter usando cache de Django (Redis/Memcached en producción).

    Por defecto permite:
    - 10 intentos por minuto por IP
    - 50 intentos por hora por IP
    """

    def __init__(self, requests_per_minute=10, requests_per_hour=50):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

    @staticmethod
    def get_client_ip(request):
        """Obtiene la IP real del cliente, considerando proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def is_allowed(self, request, endpoint_name='default'):
        """
        Verifica si la request está permitida según los límites.

        Returns:
            tuple: (allowed: bool, retry_after: int or None)
        """
        ip = self.get_client_ip(request)
        current_time = int(time.time())

        # Keys para cache
        minute_key = f"rate_limit:{endpoint_name}:minute:{ip}:{current_time // 60}"
        hour_key = f"rate_limit:{endpoint_name}:hour:{ip}:{current_time // 3600}"

        # Obtener contadores actuales
        minute_count = cache.get(minute_key, 0)
        hour_count = cache.get(hour_key, 0)

        # Verificar límites
        if minute_count >= self.requests_per_minute:
            retry_after = 60 - (current_time % 60)  # Segundos hasta el próximo minuto
            return False, retry_after

        if hour_count >= self.requests_per_hour:
            retry_after = 3600 - (current_time % 3600)  # Segundos hasta la próxima hora
            return False, retry_after

        # Incrementar contadores
        cache.set(minute_key, minute_count + 1, timeout=60)
        cache.set(hour_key, hour_count + 1, timeout=3600)

        return True, None


def rate_limit(requests_per_minute=10, requests_per_hour=50):
    """
    Decorador para aplicar rate limiting a endpoints de Django Ninja.

    Uso:
        @rate_limit(requests_per_minute=5, requests_per_hour=20)
        @router.post("/validate-token/", auth=None)
        def validate_token(request, payload):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            limiter = RateLimiter(requests_per_minute, requests_per_hour)
            endpoint_name = func.__name__

            allowed, retry_after = limiter.is_allowed(request, endpoint_name)

            if not allowed:
                return JsonResponse(
                    {
                        'error': 'Demasiados intentos. Por favor, intente más tarde.',
                        'retry_after': retry_after,
                        'message': f'Has excedido el límite de intentos. Intenta nuevamente en {retry_after} segundos.'
                    },
                    status=429
                )

            return func(request, *args, **kwargs)

        return wrapper
    return decorator

