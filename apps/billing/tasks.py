import logging

from celery import shared_task
from django.conf import settings

from apps.billing.application.use_cases.send_invoice_notification import SendInvoiceNotification
from apps.billing.application.use_cases.send_receipt_notification import SendReceiptNotification
from apps.billing.infrastructure.repository import InvoiceRepository
from apps.documents.application.generate_pdf import GeneratePDFUseCase
from apps.documents.infrastructure.pdf.weasyprint_pdf_generator import WeasyPrintPDFGenerator
from apps.pagos.infrastructure.repository.payment_repository import PaymentRepository

logger = logging.getLogger(__name__)

# URL base para recursos estáticos en PDFs (NO usar BASE_DIR que es un path)
base_url = getattr(settings, 'BASE_URL', settings.DOMAIN_NAME)

@shared_task
def send_invoice_email_task(invoice_id: int):
    """
    Envía la factura completa por email cuando se termina de pagar.
    """

    try:
        result = SendInvoiceNotification(
            InvoiceRepository(),
            PaymentRepository()
        ).execute(invoice_id)

        logger.info(f"[send_payment_link] FIN OK | invoice_id={invoice_id} | result={result}")
        return result

    except Exception as e:
        logger.exception(f"[send_payment_link] EXCEPTION | invoice_id={invoice_id} | error={e}")
        return {
            'success': False,
            'message': f"Error inesperado al enviar enlace de pago para el inovice {invoice_id}: {str(e)}",
            'error': str(e)
        }

@shared_task
def send_receipt_email_task(invoice_id: int, receipt_id: int):
    """
    Envía el recibo de abono por email al estudiante.
    Reutiliza SendEmailUseCase de orden_pagos.
    """

    try:

        result = SendReceiptNotification(
            InvoiceRepository()
        ).execute(invoice_id, receipt_id)

        logger.info(f"[send_payment_link] FIN OK | invoice_id={invoice_id}  | receipt_id={receipt_id} | result={result}")

        return result

    except Exception as e:
        logger.error(
            f"Error al enviar recibo {receipt_id} por email: {str(e)}",
            exc_info=True
        )
        return {
            'success': False,
            'message': f'Error al enviar email: {str(e)}',
            'error': str(e)
        }

def _generate_invoice_pdf(data):
    """
    Función interna para generar el PDF de la factura.
    Se puede llamar directamente sin pasar por Celery.
    """
    pdf_content, pdf_path = GeneratePDFUseCase(WeasyPrintPDFGenerator()).execute(
        data_structure=data,
        template_name='invoices/pdf_invoice.html',
        css_filename='pdf_invoice.css',
        folder='invoices',
        document_type='invoice',
        base_url=str(base_url)
    )
    return pdf_content, pdf_path

@shared_task
def save_pdf_payment_task(data):
    """
    Genera el PDF de la factura y retorna el contenido y ruta.
    Tarea de Celery que envuelve la función interna.
    """
    return _generate_invoice_pdf(data)

def _generate_receipt_pdf(data: dict):
    """
    Función interna para generar el PDF del recibo.
    Se puede llamar directamente sin pasar por Celery.
    """
    pdf_content, pdf_path = GeneratePDFUseCase(WeasyPrintPDFGenerator()).execute(
        data_structure=data,
        template_name='receipts/payment_receipt.html',  # Template específico para recibos
        css_filename='receipts.css',
        folder='receipts',
        document_type='receipt',
        base_url=str(base_url)
    )
    return pdf_content, pdf_path

@shared_task
def save_pdf_receipt_task(data: dict):
    """
    Genera el PDF del recibo y retorna el contenido y ruta.
    Tarea de Celery que envuelve la función interna.
    """
    return _generate_receipt_pdf(data)

