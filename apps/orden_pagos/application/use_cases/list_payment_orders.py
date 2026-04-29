from django.db.models import QuerySet

from apps.orden_pagos.infrastructure.repository.payment_order_repository import PaymentOrderRepository


class ListPaymentOrdersUseCase:
    def __init__(self, repository: PaymentOrderRepository):
        self.repository = repository

    def execute(self, filters: dict = None) -> QuerySet:
        payment_order_list = self.repository.list_all(filters)

        return payment_order_list
