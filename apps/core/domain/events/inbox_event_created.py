"""
Evento de dominio que se dispara cuando se crea un nuevo InboxEvent.
"""
from .base_event import DomainEvent


class InboxEventCreated(DomainEvent):
    """
    Evento emitido cuando un webhook guarda un evento en InboxEvent.

    Este evento permite que el WebhookEventProcessor reaccione y procese
    el evento de forma desacoplada del webhook.
    """

    def __init__(
        self,
        inbox_event_id: int,
        provider: str,
        event_type: str,
        event_id: str,
        payment_order_id: int,
        payer_name: str = None
    ):
        super().__init__()
        self.inbox_event_id = inbox_event_id
        self.provider = provider
        self.provider_event_type = event_type  # Renombrado para evitar conflicto con propiedad base
        self.event_id = event_id
        self.payment_order_id = payment_order_id
        self.payer_name = payer_name

    def __str__(self):
        return f"InboxEventCreated(id={self.inbox_event_id}, provider={self.provider}, type={self.provider_event_type}, payment_order_id={self.payment_order_id})"

