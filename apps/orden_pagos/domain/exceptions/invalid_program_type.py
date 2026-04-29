"""
Excepción para tipo de programa inválido.
"""
from .base_exception import DomainException


class InvalidProgramTypeException(DomainException):
    """
    Excepción lanzada cuando el tipo de programa no es válido.
    """
    default_message = "Tipo de programa no válido"
