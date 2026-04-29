"""
Excepción cuando no se encuentran precios para el programa solicitado.
"""
from .base_exception import DomainException


class PricingNotFoundException(DomainException):
    """
    Excepción lanzada cuando no se encuentran precios para el programa solicitado.
    """
    default_message = "No se encontraron precios para este programa"
