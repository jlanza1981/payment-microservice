from typing import List

from django.db.models import Prefetch

from apps.orden_pagos.models import PaymentConcept, PaymentCategory


class PaymentConceptRepository:

    @staticmethod
    def get_all_concepts() -> List[PaymentConcept]:
        """
        Obtiene todos los conceptos de pago activos.
        """
        return list(PaymentConcept.objects.filter(is_active=True).select_related('category'))

    @staticmethod
    def get_concept_by_id(concept_id: int) -> PaymentConcept:
        """
        Obtiene un concepto de pago por ID.
        """
        return PaymentConcept.objects.select_related('category').filter(id=concept_id).first()

    @staticmethod
    def get_admin_fee_split_order(concept_id: int) -> bool:
        """
        Obtiene un concepto de pago por ID.
        """
        return PaymentConcept.objects.filter(id=concept_id).values_list('split_order', flat=True).first()

    @staticmethod
    def get_concept_by_code(code: str) -> PaymentConcept:
        """
        Obtiene un concepto de pago por código.
        """
        return PaymentConcept.objects.select_related('category').get(code=code)

    @staticmethod
    def get_all_categories() -> List[PaymentCategory]:
        """
        Obtiene todas las categorías de pago.
        """
        return list(PaymentCategory.objects.all())

    @staticmethod
    def get_category_by_id(category_id: int) -> PaymentCategory:
        """
        Obtiene una categoría por ID.
        """
        return PaymentCategory.objects.get(id=category_id)

    @staticmethod
    def get_categories_with_concepts() -> List[PaymentCategory]:
        """
        Obtiene todas las categorías con sus conceptos de pago activos.
        Optimizado con prefetch_related para evitar N+1 queries.
        """
        return list(
            PaymentCategory.objects.prefetch_related(
                Prefetch(
                    'concepts',
                    queryset=PaymentConcept.objects.filter(is_active=True).order_by('name')
                )
            ).order_by('name')
        )

    @staticmethod
    def get_concepts_by_category(category_id: int) -> List[PaymentConcept]:
        """
        Obtiene todos los conceptos de una categoría específica.
        """
        return list(
            PaymentConcept.objects.filter(
                category_id=category_id,
                is_active=True
            ).select_related('category').order_by('name')
        )

    @staticmethod
    def get_concepts_grouped_by_category():
        categories = PaymentCategory.objects.prefetch_related(
            Prefetch(
                'concepts',
                queryset=PaymentConcept.objects.filter(is_active=True).order_by('name')
            )
        ).order_by('name')

        result = []
        for category in categories:
            concepts_data = []
            for concept in category.concepts.all():
                concepts_data.append({
                    'id': concept.id,
                    'code': concept.code,
                    'name': concept.name,
                    'category_id': concept.category_id,
                    'category_code': category.code,
                    'category_name': category.name,
                    'is_active': concept.is_active,
                    'description': concept.description,
                    'requires_program': concept.requires_program,
                    'created_at': concept.created_at,
                    'updated_at': concept.updated_at,
                })

            # Solo agregar categoría si tiene conceptos
            if concepts_data:
                result.append({
                    "category": category.code,
                    "concepts": concepts_data
                })

        return result

    @staticmethod
    def get_concepts_by_ids(concept_ids: List[int]) -> List[PaymentConcept]:
        return list(
            PaymentConcept.objects.filter(
                id__in=concept_ids,
                is_active=True
            ).select_related('category').order_by('name')
        )
