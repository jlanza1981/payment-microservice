import logging

from apps.billing.application.use_cases.get_invoice_by_id_with_relations import GetByIdWithRelations
from apps.billing.domain.interface.repository import InvoiceRepositoryInterface
from apps.notifications_message.application.send_email import SendEmailUseCase
from apps.notifications_message.domain.entities.email_data import EmailData, EmailAttachment
from apps.notifications_message.infrastructure.emails.django_email_sender import DjangoEmailSender
from apps.pagos.application.use_cases.get_payment_by_id import GetPaymentById
from apps.pagos.domain.interface.repository.payment_repository_interface import PaymentRepositoryInterface

logger = logging.getLogger(__name__)

class SendInvoiceNotification:
    def __init__(
            self,
            invoice_repository: InvoiceRepositoryInterface,
            payment_repository: PaymentRepositoryInterface
    ):
        self.invoice_repository = invoice_repository
        self.payment_repository = payment_repository

    def execute(self, invoice_id: int):
        try:

            invoice = GetByIdWithRelations(self.invoice_repository).execute(invoice_id)

            # Enviar email con el PDF
            emails_sent = self._send_email(invoice) or []

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

    def _send_email(self, invoice):
        """Envía el correo al estudiante y asesor."""
        from apps.billing.tasks import _generate_invoice_pdf
        
        recipients = [invoice.user.email, invoice.advisor.email]
        data = invoice.get_invoice_structure()
        template_context = {
            'data': data
        }
        # Generar PDF
        pdf_content, pdf_path = _generate_invoice_pdf(data)
        # Crear el adjunto PDF
        pdf = self._create_pdf_attachment(invoice, pdf_content)

        invoice.invoice_file = pdf_path
        invoice.save()
        # Preparar el asunto
        subject = str(
            f'Pago registrado con éxito del invoice N° {invoice.invoice_number} por {invoice.user.nombre} {invoice.user.apellido}'
        )

        email_data = EmailData(
            subject=subject,
            recipients=recipients,
            template_name='invoices/invoice_complete_email.html',
            template_context=template_context,
            attachments=[pdf]
        )
        # Enviar correo usando el caso de uso
        email_sender = DjangoEmailSender()
        result = SendEmailUseCase(email_sender).execute(email_data)
        result['emails'] = recipients

        return result

    @staticmethod
    def _create_pdf_attachment(invoice, pdf_content: bytes) -> EmailAttachment:
        """Crea el adjunto PDF para el correo."""
        pdf_filename = f"invoice_{invoice.invoice_number}_{invoice.user.nombre}_{invoice.user.apellido}.pdf"

        return EmailAttachment(
            filename=pdf_filename,
            content=pdf_content,
            mimetype='application/pdf'
        )