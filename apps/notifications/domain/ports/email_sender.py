from typing import Protocol, Dict, Any

from apps.notifications_message.domain.entities.email_data import EmailData


class EmailSender(Protocol):
    """
    Este puerto define el contrato para enviar correos electrónicos
    desde templates HTML o texto plano, con adjuntos opcionales.
    """

    def send(self, email_data: EmailData) -> Dict[str, Any] | None:
        """
        Envía un correo electrónico.
        """
        ...
