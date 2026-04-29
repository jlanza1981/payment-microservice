"""
Excepción base reutilizable para el dominio con soporte de mensajes dinámicos y código opcional.
"""

class DomainException(Exception):
    """Excepción base del dominio con soporte para mensaje dinámico y opcional código.

    Args:
        message: Texto a mostrar. Si no se indica, se usa el mensaje por defecto de cada subclase.
        code: Código opcional para categorizar el error (p. ej., para mapping en la capa de aplicación/infraestructura).
    """

    default_message = "Ha ocurrido un error en el dominio"

    def __init__(self, message: str | None = None, code: str | None = None):
        self.code = code
        self.message = message or self.default_message
        super().__init__(self.message)

    def __str__(self) -> str:  # Representación legible
        return self.message


class GenericDomainException(DomainException):
    """Excepción genérica para casos donde solo se quiere mostrar un mensaje dinámico."""
    default_message = "Error de dominio"
