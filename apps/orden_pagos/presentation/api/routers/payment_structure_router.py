"""
Router para endpoints de Payment Structures (Estructuras de Pago).
Maneja consultas de estructuras de pago y sus campos dinámicos.
"""
from typing import List

from django.http import HttpRequest
from ninja import Router

from apps.core.infrastructure.security.auth_bearer import AuthBearer
from apps.orden_pagos.application.use_cases.get_payment_structures import (
    GetAllStructuresUseCase,
    GetStructureByIdUseCase,
    GetStructureByPaymentTypeUseCase,
    GetStructuresByPaymentTypesUseCase,
)
from apps.orden_pagos.infrastructure.repository.payment_structure_repository import PaymentStructureRepository
from apps.orden_pagos.presentation.api.schemas import PaymentStructureDetailSchema

# Crear sub-router para estructuras de pago
payment_structures_router = Router(tags=["Payment Structures"], auth=AuthBearer())


@payment_structures_router.get("/", response=List[PaymentStructureDetailSchema],
                               summary="Obtener todas las estructuras de pago")
def get_all_structures(request: HttpRequest):
    """
    Obtiene todas las estructuras de pago activas con sus campos.

    GET /api/v1/payment-orders/payment-structures/

    Retorna una lista de estructuras de pago, donde cada estructura incluye:
    - Información del concepto de pago (payment_type)
    - Si tiene descuento
    - Notas adicionales
    - Lista de campos dinámicos (fields) ordenados

    Returns:
        Lista de estructuras de pago activas con sus campos

    Example Response:
        [
            {
                "id": 1,
                "payment_type": {
                    "id": 1,
                    "code": "I",
                    "name": "Inscripción"
                },
                "has_discount": true,
                "notes": "Estructura para inscripción de estudiantes",
                "is_active": true,
                "fields": [
                    {
                        "id": 1,
                        "name": "precio",
                        "label": "Precio",
                        "field_type": "number",
                        "choices": null,
                        "required": true,
                        "readonly": false,
                        "order": 1,
                        "default_value": "0",
                        "active": true
                    }
                ]
            }
        ]
    """
    structure_repository = PaymentStructureRepository()
    structures = GetAllStructuresUseCase(structure_repository).execute()

    return [PaymentStructureDetailSchema.from_orm(structure) for structure in structures]


@payment_structures_router.get("/by-id/{structure_id}/", response={200: PaymentStructureDetailSchema, 404: dict},
                               summary="Obtener estructura por ID")
def get_structure_by_id(request: HttpRequest, structure_id: int):
    """
    Obtiene una estructura de pago específica por su ID.

    GET /api/v1/payment-orders/payment-structures/by-id/{structure_id}/

    Args:
        structure_id: ID de la estructura de pago

    Returns:
        200: Estructura de pago encontrada con sus campos
        404: Estructura no encontrada

    Example:
        GET /api/v1/payment-orders/payment-structures/by-id/1/

        Response 200:
        {
            "id": 1,
            "payment_type": {
                "id": 1,
                "code": "I",
                "name": "Inscripción"
            },
            "has_discount": true,
            "notes": "Estructura para inscripción",
            "is_active": true,
            "fields": [...]
        }

        Response 404:
        {
            "error": "Estructura de pago con ID 999 no encontrada"
        }
    """
    structure_repository = PaymentStructureRepository()
    structure = GetStructureByIdUseCase(structure_repository).execute(structure_id)

    if structure is None:
        return 404, {'error': f'Estructura de pago con ID {structure_id} no encontrada'}

    return 200, PaymentStructureDetailSchema.from_orm(structure)


@payment_structures_router.get("/by-payment-concept/{payment_type_id}/",
                               response={200: PaymentStructureDetailSchema, 404: dict},
                               summary="Obtener estructura por tipo de pago")
def get_structure_by_payment_type(request: HttpRequest, payment_type_id: int):
    """
    Obtiene una estructura de pago por su tipo de pago (concepto de pago).

    GET /api/v1/payment-orders/payment-structures/by-payment-type/{payment_type_id}/

    Args:
        payment_type_id: ID del concepto de pago (PaymentConcept)

    Returns:
        200: Estructura de pago encontrada para ese tipo
        404: No existe estructura para ese tipo de pago

    Use case:
        Cuando necesitas saber qué campos se deben mostrar dinámicamente
        para un concepto de pago específico (ej: Inscripción, Matrícula, etc.)

    Example:
        GET /api/v1/payment-orders/payment-structures/by-payment-type/1/

        Response 200:
        {
            "id": 1,
            "payment_type": {
                "id": 1,
                "code": "I",
                "name": "Inscripción"
            },
            "has_discount": true,
            "notes": "Estructura para inscripción de estudiantes",
            "is_active": true,
            "fields": [
                {
                    "id": 1,
                    "name": "precio",
                    "label": "Precio de Inscripción",
                    "field_type": "number",
                    "choices": null,
                    "required": true,
                    "readonly": false,
                    "order": 1,
                    "default_value": "50",
                    "active": true
                },
                {
                    "id": 2,
                    "name": "descuento_pct",
                    "label": "Descuento (%)",
                    "field_type": "number",
                    "choices": null,
                    "required": false,
                    "readonly": false,
                    "order": 2,
                    "default_value": "0",
                    "active": true
                }
            ]
        }

        Response 404:
        {
            "error": "No existe estructura de pago para el tipo de pago con ID 999"
        }
    """
    structure_repository = PaymentStructureRepository()
    structure = GetStructureByPaymentTypeUseCase(structure_repository).execute(payment_type_id)

    if structure is None:
        return 404, {'error': f'No existe estructura de pago para el tipo de pago con ID {payment_type_id}'}

    return 200, PaymentStructureDetailSchema.from_orm(structure)


@payment_structures_router.post("/by-payment-types/", response=List[PaymentStructureDetailSchema],
                                summary="Obtener estructuras por múltiples tipos de pago")
def get_structures_by_payment_types(request: HttpRequest, payment_type_ids: List[int]):
    """
    Obtiene múltiples estructuras de pago por una lista de IDs de conceptos de pago.

    POST /api/v1/payment-orders/payment-structures/by-payment-types/

    Args:
        payment_type_ids: Lista de IDs de conceptos de pago (en el body)

    Returns:
        Lista de estructuras de pago para los tipos solicitados

    Use case:
        Cuando necesitas cargar estructuras para varios conceptos de pago
        a la vez (ej: un formulario con múltiples tipos de pago).

    Request Body:
        [1, 2, 3]

    Example Response:
        [
            {
                "id": 1,
                "payment_type": {"id": 1, "code": "I", "name": "Inscripción"},
                "has_discount": true,
                "is_active": true,
                "fields": [...]
            },
            {
                "id": 2,
                "payment_type": {"id": 2, "code": "M", "name": "Matrícula"},
                "has_discount": false,
                "is_active": true,
                "fields": [...]
            }
        ]
    """
    structure_repository = PaymentStructureRepository()
    structures = GetStructuresByPaymentTypesUseCase(structure_repository).execute(payment_type_ids)

    return [PaymentStructureDetailSchema.from_orm(structure) for structure in structures]
