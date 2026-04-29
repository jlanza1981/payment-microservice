import logging
from typing import Any, Dict

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

from apps.notifications_message.domain.entities.email_data import EmailData
from apps.notifications_message.domain.ports.email_sender import EmailSender

logger = logging.getLogger(__name__)


class EmailSendError(Exception):
    """Excepción lanzada cuando falla el envío de un email"""
    pass


class DjangoEmailSender(EmailSender):
    """
    Implementación del sender de emails usando Django Email.

    Esta implementación utiliza el backend de email configurado
    en Django (SMTP, Console, etc.) para enviar correos.
    """

    def send(self, email_data: EmailData)-> Dict[str, Any] | None:
        """
        Envía un correo electrónico usando Django Email.
        """
        # Renderizar cuerpo del email
        if email_data.template_name:
            try:
                template_context = email_data.template_context
                logger.info(f"data que se envia template_context al template: {template_context}")
                body = render_to_string(email_data.template_name, template_context)
            except Exception as e:
                logger.error(f"Error al renderizar template {email_data.template_name}: {e}")
                raise EmailSendError(f"No se pudo renderizar el template: {e}") from e
        else:
            body = email_data.body or ""

        # Crear email
        email = EmailMultiAlternatives(
            subject=email_data.subject,
            body=body,
            from_email=email_data.from_email or settings.EMAIL_HOST_USER,
            to=email_data.recipients,
            cc=email_data.cc or [],
            bcc=email_data.bcc or []
        )
        emails_sent = ', '.join(email_data.recipients)
        # Agregar versión HTML
        email.attach_alternative(body, "text/html")

        # Agregar adjuntos si existen
        if email_data.attachments:
            for attachment in email_data.attachments:
                email.attach(
                    attachment.filename,
                    attachment.content,
                    attachment.mimetype
                )

        # Enviar email
        try:
            email.send()
            logger.info(
                f"Email enviado exitosamente | "
                f"asunto='{email_data.subject}' | "
                f"destinatarios={emails_sent} | "
                f"adjuntos={len(email_data.attachments or [])}"
            )

            message = f'Email enviado correctamente a {emails_sent} destinatario(s).'
            return self._build_response(email_data, message=message, success=True)

        except Exception as e:
            logger.error(
                f"Error al enviar email | "
                f"asunto='{email_data.subject}' | "
                f"destinatarios={', '.join(email_data.recipients)} | "
                f"error={str(e)}",
                exc_info=True
            )
            message = "Error al enviar email"
            return self._build_response(email_data, message=message, success=False, error=e)


    @staticmethod
    def _build_response(email_result, message: str, success:bool, error=None) -> Dict[str, Any]:
        emails_sent = ', '.join(email_result.recipients)
        return {
            'success': success,
            'message': message,
            'emails_sent': emails_sent,
            'error':str(error)
        }