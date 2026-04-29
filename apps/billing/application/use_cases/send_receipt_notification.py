import logging
from typing import List

from apps.billing.application.use_cases.get_invoice_by_id_with_relations import GetByIdWithRelations
from apps.billing.domain.interface.repository import InvoiceRepositoryInterface
from apps.notifications_message.application.send_email import SendEmailUseCase
from apps.notifications_message.domain.entities.email_data import EmailData, EmailAttachment
from apps.notifications_message.infrastructure.emails.django_email_sender import DjangoEmailSender

logger = logging.getLogger(__name__)

class SendReceiptNotification:
    def __init__(
            self,
            repository: InvoiceRepositoryInterface
    ):
        self.invoice_repository = repository

    def execute(self, invoice_id: int, receipt_id):
        try:

            invoice = GetByIdWithRelations(self.invoice_repository).execute(invoice_id)
            receipt = invoice.receipts.get(id=receipt_id)

            logger.info(f"Enviando receipt {receipt.receipt_number} por email a {invoice.user.email}")

            emails_sent = self._send_email(receipt, invoice) or []

            logger.info(f"Factura {invoice.invoice_number} enviada a {invoice.user.email}")

            return emails_sent

        except Exception as e:
            logger.error(
                f"Error al enviar factura {invoice_id} por email: {str(e)}",
                exc_info=True
            )
            return {
                'success': False,
                'message': f'Error al enviar email: {str(e)}',
                'error': str(e)
            }

    @staticmethod
    def _generate_receipt_pdf(invoice, receipt_id: int) -> bytes:
        from apps.billing.tasks import _generate_receipt_pdf
        # Obtener el recibo específico desde los receipts de la factura
        receipt = invoice.receipts.get(id=receipt_id)

        data = receipt.get_receipt_structure()

        pdf_content, pdf_path = _generate_receipt_pdf(data)

        receipt.receipt_file = pdf_path
        receipt.save()

        return pdf_content

    @staticmethod
    def _generate_invoice_pdf(invoice) -> bytes:
        from apps.billing.tasks import _generate_invoice_pdf

        data = invoice.get_invoice_structure()
        pdf_content, pdf_path = _generate_invoice_pdf(data)

        invoice.invoice_file = pdf_path
        invoice.save()

        return pdf_content
    def _send_email(self, receipt, invoice):
        recipients = [receipt.student.email, receipt.invoice.advisor.email]

        # Preparar datos para la plantilla del recibo
        template_context = {
            'data': receipt.get_receipt_structure()
        }

        subject = str(
            f'Recibo de abono N° {receipt.receipt_number} - Factura {receipt.invoice.invoice_number} - {receipt.student.nombre} {receipt.student.apellido}'
        )
        # Crear el PDF adjunto de la factura
        pdf_content_invoice = self._generate_invoice_pdf(invoice)

        # Crear el PDF adjunto del recibo
        pdf_content_receipt = self._generate_receipt_pdf(invoice, receipt.id)

        # adjuntar los PDF
        attachments = self._create_pdf_attachment(receipt, pdf_content_receipt, pdf_content_invoice)

        # Crear objeto EmailData
        email_data = EmailData(
            subject=subject,
            recipients=recipients,
            template_name='receipts/payment_receipt_email.html',
            template_context=template_context,
            attachments=attachments
        )

        # Enviar correo usando el caso de uso
        result = SendEmailUseCase(DjangoEmailSender()).execute(email_data)

        # Agregar la lista de emails al resultado para mantener compatibilidad
        if result['success']:
            result['emails'] = recipients

        return result

    @staticmethod
    def _create_pdf_attachment(receipt, pdf_content: bytes, pdf_content_invoice: bytes) -> List[EmailAttachment]:
        """Crea el adjunto PDF para el correo."""
        pdf_filename = f"receipt_{receipt.receipt_number}_{receipt.student.nombre}_{receipt.student.apellido}.pdf"
        attachments = [EmailAttachment(
            filename=pdf_filename,
            content=pdf_content,
            mimetype='application/pdf'
        )]
        invoice_pdf_filename = f"invoice_{receipt.invoice.invoice_number}_{receipt.student.nombre}_{receipt.student.apellido}.pdf"
        attachments.append(EmailAttachment(
            filename=invoice_pdf_filename,
            content=pdf_content_invoice,
            mimetype='application/pdf'
        ))
        return attachments