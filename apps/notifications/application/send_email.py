import logging
from typing import Dict, Any

from apps.notifications_message.domain.entities.email_data import EmailData
from apps.notifications_message.domain.ports.email_sender import EmailSender

logger = logging.getLogger(__name__)


class SendEmailUseCase:
    """
    Orquesta el proceso de envío de emails usando el sender inyectado.
    Maneja logging y respuestas consistentes.
    """

    def __init__(self, email_sender: EmailSender):
        self.email_sender = email_sender

    def execute(self, email_data: EmailData) -> Dict[str, Any]:
        try:
            sent = self.email_sender.send(email_data)

            logger.info(
                f"Correo enviado exitosamente. "
                f"Asunto: '{email_data.subject}' | "
                f"Destinatarios: {', '.join(email_data.recipients)}| "
                f"resultado: {sent}"
            )

            return sent

        except Exception as e:
            logger.error(
                f"Error al enviar correo. "
                f"Asunto: '{email_data.subject}' | "
                f"Destinatarios: {', '.join(email_data.recipients)} | "
                f"Error: {str(e)}",
                exc_info=True
            )

            return {
                "success": False,
                "message": f"Error al enviar correo: {str(e)}",
                "error": str(e),
                "recipients": email_data.recipients,
                "subject": email_data.subject,
            }
