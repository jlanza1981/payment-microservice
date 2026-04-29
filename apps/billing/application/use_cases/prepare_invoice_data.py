from typing import Dict, Any

from apps.administrador.models import Usuarios
from apps.orden_pagos.models import PaymentOrder

class PrepareInvoiceDataUseCase:
    def __init__(
            self,
            users_repository,
            payment_order_repository
    ):

        self.repositories = {
            "user": users_repository,
            "advisor": users_repository,
            "payment_order": payment_order_repository
        }

    def execute(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:

        invoice = invoice_data.copy()

        for field, repository in self.repositories.items():

            value = invoice.get(field)

            if not value:
                continue

            if not isinstance(value, (int, str)):
                continue

            instance = repository.get_by_id(value)

            if instance:
                invoice[field] = instance


        return invoice