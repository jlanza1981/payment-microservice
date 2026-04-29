"""
Excepción cuando se requiere una intensidad para calcular precios pero no se proporciona.
"""
from .base_exception import DomainException


class IntensityRequiredException(DomainException):
    """
    Excepción lanzada cuando se requiere una intensidad para calcular precios
    pero no se proporciona.
    """
    default_message = "La intensidad es requerida para este programa"
