import logging

from celery import shared_task
from rest_framework.exceptions import ValidationError

from api import settings
from apps.documents.application.generate_pdf import GeneratePDFUseCase
from apps.documents.infrastructure.pdf.weasyprint_pdf_generator import WeasyPrintPDFGenerator

from apps.orden_pagos.application.use_cases.send_payment_notification import SendPaymentNotificationUseCase
from apps.orden_pagos.infrastructure.repository.payment_order_repository import PaymentOrderRepository

logger = logging.getLogger(__name__)

url_base = getattr(settings, 'BASE_URL', settings.DOMAIN_NAME)
@shared_task
def send_payment_notification(order_id, base_url=None):
    """
    Tarea Celery para enviar el enlace de pago.
    Registra logs de inicio, parámetros, resultado y errores.
    """
    logger.info(f"[send_payment_link] INICIO | order_id={order_id} | base_url={base_url}")

    try:
        result = SendPaymentNotificationUseCase(
            PaymentOrderRepository(),
            WeasyPrintPDFGenerator(),
        ).execute(order_id)

        logger.info(f"EMAIL_HOST={settings.EMAIL_HOST}, EMAIL_BACKEND={settings.EMAIL_BACKEND}")

        return result

    except Exception as e:
        logger.exception(f"[send_payment_link] EXCEPTION | order_id={order_id} | error={e}")
        return {
            'success': False,
            'message': f"Error inesperado al enviar enlace de pago para orden {order_id}: {str(e)}",
            'error': str(e)
        }
def _generate_payment_order_pdf(data):
    """
    Función interna para generar el PDF de la orden de pago.
    Se puede llamar directamente sin pasar por Celery.
    """
    pdf_content, pdf_path = GeneratePDFUseCase(WeasyPrintPDFGenerator()).execute(
        data_structure=data,
        template_name='payment_orders/pdf_order_payment.html',
        css_filename='pdf_order_payment.css',
        folder='payment_orders',
        document_type='payment_orders',
        base_url=str(url_base)
    )
    return pdf_content, pdf_path