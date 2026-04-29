import logging
from typing import List
from apps.pagos.models import InboxEvent
logger = logging.getLogger(__name__)


class GetPendingInboxEventsUseCase:
    def __init__(self, inbox_repository):
        self.inbox_repository = inbox_repository

    def execute(self) -> List[InboxEvent]:
        pending_events = self.inbox_repository.get_pending_events()
        print(f"GetPendingInboxEventsUseCase: {pending_events}")
        logger.info(f"🔄 Ejecutando caso de uso: Procesar eventos pendientes")

        return pending_events


