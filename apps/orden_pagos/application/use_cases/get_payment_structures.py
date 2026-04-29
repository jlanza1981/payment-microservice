"""
Casos de uso para PaymentStructure y PaymentStructureFields.
"""
from typing import List, Optional

from apps.orden_pagos.infrastructure.repository.payment_structure_repository import PaymentStructureRepository
from apps.orden_pagos.models import PaymentStructure


class GetAllStructuresUseCase:
    """
    Caso de uso para obtener todas las estructuras de pago activas.
    """

    def __init__(self, repository: PaymentStructureRepository):
        self.repository = repository

    def execute(self) -> List[PaymentStructure]:
        """
        Ejecuta el caso de uso.

        Returns:
            Lista de estructuras de pago activas con sus campos.
        """
        return self.repository.get_all_structures()


class GetStructureByIdUseCase:
    """
    Caso de uso para obtener una estructura de pago por ID.
    """

    def __init__(self, repository: PaymentStructureRepository):
        self.repository = repository

    def execute(self, structure_id: int) -> Optional[PaymentStructure]:
        """
        Ejecuta el caso de uso.

        Args:
            structure_id: ID de la estructura.

        Returns:
            PaymentStructure o None si no existe.
        """
        return self.repository.get_structure_by_id(structure_id)


class GetStructureByPaymentTypeUseCase:
    """
    Caso de uso para obtener una estructura de pago por tipo de pago (payment_concept).
    """

    def __init__(self, repository: PaymentStructureRepository):
        self.repository = repository

    def execute(self, payment_type_id: int) -> Optional[PaymentStructure]:
        """
        Ejecuta el caso de uso.

        Args:
            payment_type_id: ID del concepto de pago (PaymentConcept).

        Returns:
            PaymentStructure o None si no existe.
        """
        return self.repository.get_structure_by_payment_type(payment_type_id)


class GetStructuresByPaymentTypesUseCase:
    """
    Caso de uso para obtener múltiples estructuras de pago por lista de IDs de conceptos.
    """

    def __init__(self, repository: PaymentStructureRepository):
        self.repository = repository

    def execute(self, payment_type_ids: List[int]) -> List[PaymentStructure]:
        """
        Ejecuta el caso de uso.

        Args:
            payment_type_ids: Lista de IDs de conceptos de pago.

        Returns:
            Lista de PaymentStructure.
        """
        return self.repository.get_structures_by_payment_types(payment_type_ids)
