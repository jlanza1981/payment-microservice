from django.db.models import QuerySet

from apps.orden_pagos.infrastructure.repository.payment_order_repository import PaymentOrderRepository


class ListPaymentOrdersStudentUseCase:
    def __init__(self, repository: PaymentOrderRepository):
        self.repository = repository

    def execute(self, student_id:int, filters: dict = None) -> QuerySet:
        payment_order_list = self.repository.get_by_student(student_id, filters)

        return payment_order_list
