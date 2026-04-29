"""
Handlers para eventos de InboxEvent.
Reaccionan cuando llega un nuevo evento de webhook.
"""
import logging

from apps.billing.domain.interface.services import InvoiceDomainService
from apps.billing.infrastructure.repository import InvoiceRepository
from apps.core.domain.events.inbox_event_created import InboxEventCreated
from apps.orden_pagos.infrastructure.repository.payment_concept_repository import PaymentConceptRepository
from apps.orden_pagos.infrastructure.repository.payment_order_repository import PaymentOrderRepository
from apps.user.infrastructure.repository.users_repository import UsersRepository
from apps.pagos.infrastructure.repository.payment_repository import PaymentRepository
from apps.core.infrastructure.inbox.event_processor import WebhookEventProcessor
from apps.core.infrastructure.inbox.repository.inbox_repository import InboxRepository

logger = logging.getLogger(__name__)


def handle_inbox_event_created(event: InboxEventCreated) -> None:
    """
    Handler que se ejecuta cuando llega un nuevo evento al Inbox.

    Procesa el evento de forma síncrona llamando al WebhookEventProcessor.
    Siguiendo DDD, inyecta las dependencias necesarias (repository).

    Args:
        event: Evento InboxEventCreated con el ID del evento a procesar
    """
    logger.info(
        f"📥 Procesando InboxEvent #{event.inbox_event_id} - "
        f"Provider: {event.provider}, Type: {event.provider_event_type}"
    )
    if event.provider_event_type == 'CHECKOUT.ORDER.APPROVED':
        return
    try:
        # Procesar eventos pendientes pasando el created_event
        WebhookEventProcessor(
            inbox_repository=InboxRepository(),
            payment_order_repository=PaymentOrderRepository(),
            invoice_repository=InvoiceRepository(),
            payment_repository=PaymentRepository(),
            payment_concept_repository=PaymentConceptRepository(),
            user_repository=UsersRepository(),
            invoice_service=InvoiceDomainService()

        ).process_pending(created_event=event)

        logger.info(f"✅ InboxEvent #{event.inbox_event_id} procesado exitosamente")

    except Exception as e:
        logger.error(
            f"❌ Error procesando InboxEvent #{event.inbox_event_id}: {str(e)}",
            exc_info=True
        )

