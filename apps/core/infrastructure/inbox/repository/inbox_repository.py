from typing import TYPE_CHECKING, List
import logging

from django.db.models import QuerySet
from django.utils import timezone

from apps.core.domain.events.event_dispatcher import EventDispatcher
from apps.core.domain.events.inbox_event_created import InboxEventCreated
from apps.pagos.models import InboxEvent
logger = logging.getLogger(__name__)


class InboxRepository:
    """
    Repositorio para manejar los eventos entrantes del Inbox.
    """

    @staticmethod
    def save_event(provider: str, event_type: str, event_id: str, payment_order_id: int, payload: dict, payer_name: str = None):
        """
        Guarda un evento del webhook. Si ya existe, retorna el existente.
        Si es nuevo, dispara el evento InboxEventCreated para procesamiento.
        """


        inbox_event, created = InboxEvent.objects.get_or_create(
            event_id=event_id,
            defaults={
                "provider": provider,
                "event_type": event_type,
                "payload": payload,
                "processed": False,
                "payer_name": payer_name,
                "payment_order_id": payment_order_id
            }
        )

        # Si es un evento nuevo, disparar evento de dominio
        if created:
            logger.info(f"📤 Nuevo InboxEvent creado: {inbox_event.id} - {event_type}")
            event = InboxEventCreated(
                inbox_event_id=inbox_event.id,
                provider=provider,
                event_type=event_type,
                event_id=event_id,
                payment_order_id=payment_order_id,
                payer_name= payer_name,
            )
            if event_type == 'CHECKOUT.ORDER.APPROVED':
                inbox_event.processed = True
                inbox_event.save()
                logger.info(f"📤 Disparando evento de dominio para CHECKOUT.ORDER.APPROVED: {event}")
            EventDispatcher.dispatch(event)
        else:
            logger.warning(f"⚠️ InboxEvent duplicado detectado: {event_id}")

        return inbox_event

    @staticmethod
    def get_by_id(inbox_event_id: int):
        """
        Obtiene un InboxEvent por su ID.
        """
        from apps.pagos.models import InboxEvent

        try:
            return InboxEvent.objects.get(id=inbox_event_id)
        except InboxEvent.DoesNotExist:
            return None

    @staticmethod
    def get_pending_events() -> QuerySet[InboxEvent]:
        """
        Retorna todos los eventos no procesados.
        """
        from apps.pagos.models import InboxEvent

        return InboxEvent.objects.filter(processed=False).order_by("created_at")

    @staticmethod
    def mark_as_processed(inbox_event):
        """
        Marca un evento como procesado.
        """
        inbox_event.processed = True
        inbox_event.processed_at = timezone.now()
        inbox_event.save()

    @staticmethod
    def get_payer_name_from_order_approved(payment_order_id: int) -> str | None:
        """
        Busca el nombre del pagador del evento CHECKOUT.ORDER.APPROVED
        para un payment_order_id específico.
        """
        from apps.pagos.models import InboxEvent
        
        try:

            inbox_event = InboxEvent.objects.filter(
                payment_order_id=payment_order_id,
                event_type='CHECKOUT.ORDER.APPROVED',
                provider='paypal'
            ).order_by('-created_at').first()
            
            if inbox_event and inbox_event.payer_name:
                logger.info(f"Nombre del pagador recuperado de InboxEvent: {inbox_event.payer_name}")
                return inbox_event.payer_name
            
            logger.warning(f"No se encontró nombre del pagador para payment_order_id: {payment_order_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error al buscar nombre del pagador: {str(e)}")
            return None
