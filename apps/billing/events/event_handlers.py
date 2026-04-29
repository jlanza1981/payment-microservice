"""
Event Handlers para Billing.
Handlers que reaccionan a eventos de otros bounded contexts.
"""
import logging
from apps.billing.tasks import send_invoice_email_task, send_receipt_email_task
from apps.core.domain.events.payment_captured_event import PaymentCapturedEvent

logger = logging.getLogger(__name__)
def handle_payment_captured(event: PaymentCapturedEvent):

    """
    Responsabilidades:
    - Si es pago completo: Enviar factura completa por email
    - Si es pago parcial (abono): Generar y enviar recibo de abono
    """
    logger.info(
        f"[Billing Event Handler] Payment captured - "
        f"Invoice: {event.invoice_number} (ID: {event.invoice_id}), "
        f"Payment: {event.payment_id}, "
        f"Amount: {event.amount} {event.currency}, "
        f"Full Payment: {event.is_full_payment}"
    )

    if event.is_full_payment:
        _handle_full_payment(event)
    else:
        _handle_partial_payment(event)


def _handle_full_payment(event: PaymentCapturedEvent):

    logger.info(
        f"[Billing Event Handler] Programando envío de factura completa "
        f"para invoice {event.invoice_number}"
    )

    try:
        result = send_invoice_email_task.delay(event.invoice_id)

        logger.info(
            f"[Billing Event Handler] Tarea de factura completa encolada. "
            f"Task ID: {result.id}, Invoice: {event.invoice_number}"
        )

    except Exception as e:
        logger.error(
            f"[Billing Event Handler] Error al encolar tarea de factura "
            f"para invoice {event.invoice_number}: {str(e)}",
            exc_info=True
        )


def _handle_partial_payment(event: PaymentCapturedEvent):
    try:

        email_task = send_receipt_email_task.delay(event.invoice_id, event.payment_receipt_id)

        logger.info(
            f"[Billing Event Handler] Tareas de recibo encoladas. "
            f"Email Task ID: {email_task.id}"
        )
    except Exception as e:
        logger.error(
            f"[Billing Event Handler] Error al procesar pago parcial "
            f"para invoice {event.invoice_number}: {str(e)}",
            exc_info=True
        )

