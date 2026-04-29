from typing import List, Optional

from django.db.models import Prefetch

from apps.orden_pagos.models import PaymentStructure, PaymentStructureFields


class PaymentStructureRepository:

    @staticmethod
    def get_all_structures() -> List[PaymentStructure]:
        return list(
            PaymentStructure.objects.filter(is_active=True)
            .select_related('payment_type', 'payment_type__category')
            .prefetch_related(
                Prefetch(
                    'structure_section_payment_structure',
                    queryset=PaymentStructureFields.objects.filter(active=True).order_by('order')
                )
            )
            .order_by('id')
        )

    @staticmethod
    def get_structure_by_id(structure_id: int) -> Optional[PaymentStructure]:
        return (
            PaymentStructure.objects
            .select_related('payment_type', 'payment_type__category')
            .prefetch_related(
                Prefetch(
                    'structure_section_payment_structure',
                    queryset=PaymentStructureFields.objects.filter(active=True).order_by('order')
                )
            )
            .filter(id=structure_id)
            .first()
        )

    @staticmethod
    def get_structure_by_payment_type(payment_type_id: int) -> Optional[PaymentStructure]:
        return (
            PaymentStructure.objects
            .select_related('payment_type', 'payment_type__category')
            .prefetch_related(
                Prefetch(
                    'structure_section_payment_structure',
                    queryset=PaymentStructureFields.objects.filter(active=True).order_by('order')
                )
            )
            .filter(payment_type_id=payment_type_id, is_active=True)
            .first()
        )

    @staticmethod
    def get_structures_by_payment_types(payment_type_ids: List[int]) -> List[PaymentStructure]:
        return list(
            PaymentStructure.objects
            .filter(payment_type_id__in=payment_type_ids, is_active=True)
            .select_related('payment_type', 'payment_type__category')
            .prefetch_related(
                Prefetch(
                    'structure_section_payment_structure',
                    queryset=PaymentStructureFields.objects.filter(active=True).order_by('order')
                )
            )
            .order_by('payment_type__name')
        )

    @staticmethod
    def get_active_structures_count() -> int:
        return PaymentStructure.objects.filter(is_active=True).count()
