"""
Caso de uso: Enviar enlace de pago de una orden.

Este caso de uso maneja el envío del enlace de pago de una orden
al estudiante y asesor, incluyendo la generación del PDF adjunto.
"""
import datetime
import logging
from typing import Optional, Dict, Any

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.documents.application.generate_pdf import GeneratePDFUseCase
from apps.notifications_message.domain.entities.email_data import EmailAttachment, EmailData
from apps.notifications_message.application.send_email import SendEmailUseCase
from apps.notifications_message.domain.entities.email_data import EmailData, EmailAttachment
from apps.notifications_message.infrastructure.emails.django_email_sender import DjangoEmailSender
from apps.orden_pagos.application.use_cases import GetPaymentOrderByIdUseCase
from apps.orden_pagos.domain.interface.repository.repository_interface import PaymentOrderRepositoryInterface
from apps.orden_pagos.models import PaymentOrder

logger = logging.getLogger(__name__)


class SendPaymentNotificationUseCase:
    """
    Caso de uso: Enviar enlace de pago al estudiante y asesor.
    """

    def __init__(
            self,
            repository: PaymentOrderRepositoryInterface,
            pdf_generator
    ):
        self.repository = repository
        self.pdf_generator = pdf_generator

    def execute(self, order_id: int) -> Dict[str, Any]:

        payment_order = GetPaymentOrderByIdUseCase(self.repository).execute(
            order_id=order_id
        )

        if not payment_order:
            logger.error(f"Orden de pago con ID {order_id} no encontrada.")


        if payment_order.status not in ['PENDING', 'ACTIVE']:
            logger.error(f'La orden debe estar en estado PENDING o ACTIVE. Estado actual: {payment_order.status}')

        emails_sent = self._prepare_and_send_emails(payment_order)

        return emails_sent

    def _prepare_and_send_emails(self, payment_order):
        """Genera PDF y envía correo con el enlace de pago."""
        token = self.repository.generate_token(payment_order)
        payment_order.refresh_from_db()

        data = payment_order.get_order_structure()

        data_email = self._prepare_email_data(data, token)

        emails_sent = self._send_email(payment_order, data_email, data) or []

        return emails_sent

    @staticmethod
    def generate_and_save_pdf(payment_order, data) -> bytes:
        """Genera el PDF de la orden y lo guarda en payment_order_file."""
        from apps.orden_pagos.tasks import _generate_payment_order_pdf

        pdf_content, pdf_path = _generate_payment_order_pdf(data)

        payment_order.payment_order_file = pdf_path
        payment_order.save()

        return pdf_content

    @staticmethod
    def _prepare_email_data(data, token: str) -> dict:
        """Prepara los datos para la plantilla del correo."""
        return {
            'data': data,
            'enlace': f"https://www.lcmundo.com/pay/{token}/"
        }

    @staticmethod
    def _get_payment_types_description(payment_order) -> str:
        """Obtiene la descripción de los tipos de pago de la orden."""
        payment_concept_desc = []
        for detail in payment_order.payment_order_details.all():
            if detail.payment_concept.name not in payment_concept_desc:
                payment_concept_desc.append(detail.payment_concept.name)
        return ', '.join(payment_concept_desc) if payment_concept_desc else 'Pago'

    @staticmethod
    def _create_pdf_attachment(payment_order: PaymentOrder, pdf_content: bytes) -> EmailAttachment:
        """Crea el adjunto PDF para el correo."""
        pdf_filename = f"invoice_{payment_order.order_number}_{payment_order.student.nombre}_{payment_order.student.apellido}.pdf"
        return EmailAttachment(
            filename=pdf_filename,
            content=pdf_content,
            mimetype='application/pdf'
        )

    def _send_email(self, payment_order: PaymentOrder, template_context, data):
        """Envía el correo al estudiante y asesor."""
        recipients = [payment_order.student.email, payment_order.opportunity.asesor.email]

        payment_types_desc = self._get_payment_types_description(payment_order)

        subject = str(
            f'Realiza tu pago de {payment_types_desc} - Orden N° {payment_order.order_number} a través de nuestro sistema- LC Mundo'
        )

        pdf_content = self.generate_and_save_pdf(payment_order, data)

        pdf_attachment = self._create_pdf_attachment(payment_order, pdf_content)

        # Crear objeto EmailData
        email_data = EmailData(
            subject=subject,
            recipients=recipients,
            template_name='payment_orders/email_payment_link_order.html',
            template_context=template_context,
            attachments=[pdf_attachment]
        )

        email_sender = DjangoEmailSender()
        result = SendEmailUseCase(email_sender).execute(email_data)
        result['emails'] = recipients

        return result
