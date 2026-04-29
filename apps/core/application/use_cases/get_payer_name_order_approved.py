import logging
from typing import List
from apps.pagos.models import InboxEvent
logger = logging.getLogger(__name__)

class GetPayerNameOrderApproved:
    def __init__(self, inbox_repository):
        self.inbox_repository = inbox_repository

    def execute(self, payment_order_id: int) -> List[InboxEvent]:
        payer_name = self.inbox_repository.get_payer_name_from_order_approved(payment_order_id)
        print(f"GetPayerNameOrderApproved: {payer_name}")
        logger.info(f"🔄 Ejecutando caso de uso: Obtener nombre del pagador de la orden de pago")

        return payer_name