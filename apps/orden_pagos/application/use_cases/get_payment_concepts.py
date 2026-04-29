"""
Casos de uso para PaymentConcept y PaymentCategory.
"""
from typing import List, Optional

from apps.orden_pagos.infrastructure.repository.payment_concept_repository import PaymentConceptRepository
from apps.orden_pagos.models import PaymentCategory, PaymentConcept


class GetCategoriesWithConceptsUseCase:
    """
    Caso de uso para obtener todas las categorías con sus conceptos agrupados.
    """

    def __init__(self, repository: PaymentConceptRepository):
        self.repository = repository

    def execute(self) -> List[PaymentCategory]:
        """
        Ejecuta el caso de uso.

        Returns:
            Lista de categorías con sus conceptos anidados.
        """
        return self.repository.get_categories_with_concepts()


class GetAllConceptsUseCase:
    """
    Caso de uso para obtener todos los conceptos de pago activos.
    """

    def __init__(self, repository: PaymentConceptRepository):
        self.repository = repository

    def execute(self) -> List[PaymentConcept]:
        """
        Ejecuta el caso de uso.

        Returns:
            Lista de conceptos de pago activos.
        """
        return self.repository.get_all_concepts()


class GetConceptsByCategory:
    """
    Caso de uso para obtener conceptos de una categoría específica.
    """

    def __init__(self, repository: PaymentConceptRepository):
        self.repository = repository

    def execute(self, category_id: int) -> List[PaymentConcept]:
        """
        Ejecuta el caso de uso.

        Args:
            category_id: ID de la categoría.

        Returns:
            Lista de conceptos de la categoría.
        """
        return self.repository.get_concepts_by_category(category_id)


class GetConceptByIdUseCase:
    """
    Caso de uso para obtener un concepto de pago por ID.
    """

    def __init__(self, repository):
        self.repository = repository

    def execute(self, concept_id: int) -> Optional[PaymentConcept]:
        return self.repository.get_concept_by_id(concept_id)


class GetConceptByCodeUseCase:
    """
    Caso de uso para obtener un concepto de pago por código.
    """

    def __init__(self, repository: PaymentConceptRepository):
        self.repository = repository

    def execute(self, code: str) -> Optional[PaymentConcept]:
        """
        Ejecuta el caso de uso.

        Args:
            code: Código del concepto.

        Returns:
            Concepto de pago o None si no existe.
        """
        try:
            return self.repository.get_concept_by_code(code)
        except PaymentConcept.DoesNotExist:
            return None


class GetConceptsGroupedByCategoryUseCase:
    """
    Caso de uso para obtener conceptos agrupados por categoría en formato diccionario.
    """

    def __init__(self, repository: PaymentConceptRepository):
        self.repository = repository

    def execute(self):
        """
        Ejecuta el caso de uso.

        Returns:
            Lista de diccionarios con categorías como keys y conceptos como valores.
            Formato: [{"CATEGORY_CODE": [conceptos...]}, ...]
        """
        return self.repository.get_concepts_grouped_by_category()


class GetMultipleConceptsByIdsUseCase:

    def __init__(self, repository: PaymentConceptRepository):
        self.repository = repository

    def execute(self, concept_ids: List[int]) -> List[PaymentConcept]:

        if not concept_ids:
            return []

        return self.repository.get_concepts_by_ids(concept_ids)
