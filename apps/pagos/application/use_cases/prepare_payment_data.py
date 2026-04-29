import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PreparePaymentDataUseCase:

    def __init__(
        self,
        users_repository,
        invoice_repository
    ):
        self.users_repository = users_repository
        self.invoice_repository = invoice_repository
        self.repositories = {
            "user": users_repository,
            "advisor": users_repository,
            "invoice": invoice_repository
        }

    def execute(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:

        payment = payment_data.copy()
        print('payment_data en prepare_payment_data:', payment)
        for field, repository in self.repositories.items():

            value = payment.get(field)

            if not value:
                continue

            if not isinstance(value, (int, str)):
                continue

            instance = repository.get_by_id(value)

            if instance:
                payment[field] = instance

        return payment