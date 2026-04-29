"""
Router para endpoints de Payment Concepts (Conceptos de Pago).
Maneja consultas de conceptos y categorías de pago.
"""
from typing import List

from django.http import HttpRequest
from ninja import Router

from apps.core.infrastructure.security.auth_bearer import AuthBearer
from apps.orden_pagos.application.use_cases import (
    GetCategoriesWithConceptsUseCase,
    GetAllConceptsUseCase,
    GetConceptsByCategory,
    GetConceptByIdUseCase,
    GetConceptByCodeUseCase,
    GetConceptsGroupedByCategoryUseCase,
    ListAdministrativeCostsByCountryUseCase,
    CalculateRegistrationFeeUseCase,
    CalculateTuitionFeeUseCase,
    CalculateMaterialCostUseCase, GetMultipleConceptsByIdsUseCase, GetBookingFeeCostUseCase,
)
from apps.orden_pagos.application.dto import RegistrationDataRequest
from apps.orden_pagos.domain.exceptions import IntensityRequiredException
from apps.orden_pagos.infrastructure.repository.payment_concept_repository import PaymentConceptRepository
from apps.orden_pagos.presentation.api.schemas import (
    PaymentConceptSchema,
    PaymentCategoryWithConceptsSchema,
)
from apps.orden_pagos.presentation.api.schemas.input_schemas_payment_concepts import AdditionalDataForConceptInputSchema
from apps.administrative_cost_type.infrastructure.repository.administrative_cost_repository import AdministrativeCostRepository
from apps.orden_pagos.infrastructure.repository.registration_fee_repository import RegistrationFeeRepository
from apps.orden_pagos.infrastructure.repository.headquarters_pricing_repository import HeadquartersPriceRepository

# Crear sub-router para conceptos de pago
payment_concepts_router = Router(tags=["Payment Concepts"], auth=AuthBearer())
concept_repository = PaymentConceptRepository()
repository_administrative_cost = AdministrativeCostRepository()
repository_registration_fee = RegistrationFeeRepository()
repository_sede_pricing = HeadquartersPriceRepository()


@payment_concepts_router.get("/categories-with-concepts/", response=List[PaymentCategoryWithConceptsSchema],
                             summary="Obtener categorías con conceptos agrupados")
def get_categories_with_concepts(request: HttpRequest):

    use_case = GetCategoriesWithConceptsUseCase(concept_repository)
    categories = use_case.execute()
    return categories


@payment_concepts_router.get("/", response=List[PaymentConceptSchema],
                             summary="Obtener todos los conceptos de pago")
def get_all_concepts(request: HttpRequest):

    use_case = GetAllConceptsUseCase(concept_repository)
    concepts = use_case.execute()
    return concepts


@payment_concepts_router.get("/by-category/{category_id}/", response=List[PaymentConceptSchema],
                             summary="Obtener conceptos por categoría")
def get_concepts_by_category(request: HttpRequest, category_id: int):

    concept_repository = PaymentConceptRepository()
    use_case = GetConceptsByCategory(concept_repository)
    concepts = use_case.execute(category_id)
    return concepts


@payment_concepts_router.get("/by-id/{concept_id}/", response={200: PaymentConceptSchema, 404: dict},
                             summary="Obtener concepto por ID")
def get_concept_by_id(request: HttpRequest, concept_id: int):

    use_case = GetConceptByIdUseCase(concept_repository)
    concept = use_case.execute(concept_id)

    if concept is None:
        return 404, {'error': f'Concepto de pago con ID {concept_id} no encontrado'}

    return 200, PaymentConceptSchema.from_orm(concept)


@payment_concepts_router.get("/by-code/{code}/", response={200: PaymentConceptSchema, 404: dict},
                             summary="Obtener concepto por código")
def get_concept_by_code(request: HttpRequest, code: str):
    use_case = GetConceptByCodeUseCase(concept_repository)
    concept = use_case.execute(code)

    if concept is None:
        return 404, {'error': f'Concepto de pago con código "{code}" no encontrado'}

    return 200, PaymentConceptSchema.from_orm(concept)


@payment_concepts_router.get("/grouped-by-category/", response=List[dict],
                             summary="Obtener conceptos agrupados por categoría (formato diccionario)")
def get_concepts_grouped_by_category(request: HttpRequest):
    grouped_concepts = GetConceptsGroupedByCategoryUseCase(concept_repository).execute()

    return grouped_concepts


@payment_concepts_router.post("/additional-data/", response={200: dict, 400: dict, 500: dict}, summary="Obtener datos adicionales para un concepto de pago")
def get_additional_data_for_concept(
        request: HttpRequest,
        payload: AdditionalDataForConceptInputSchema,
):
    """
    Obtiene datos adicionales según el tipo de concepto de pago.

    - Código 'C': Costos administrativos por país
    - Código 'I': Cálculo de inscripción por sede
    - Código 'M': Cálculo de matrícula
    - Código 'E': Cálculo de extensión de programa
    - Código 'P': Cálculo de costo de material
    """
    response_data = {}
    print('payload', payload.dict())
    payment_concepts = GetMultipleConceptsByIdsUseCase(concept_repository).execute(payload.payment_concept_ids)

    if not payment_concepts:
        return 404, {'error': f'Concepto de pago con ID {payload.payment_concept_ids} no encontrado'}

    # Si el concepto es de Costos Administrativos (código 'C')
    for c in payment_concepts:
        # Si el concepto es de Costos Administrativos (código 'C')
        if c.code == "C":
            costs_list = ListAdministrativeCostsByCountryUseCase(repository_administrative_cost).execute(
                country_origin=payload.country_origin_id
            )
            response_data['administrative_cost'] = costs_list

        # Si el concepto es de Inscripción (código 'I')
        if c.code == "I":
            if not all([payload.institution_id, payload.city_id, payload.program_type_id]):
                return 400, {
                    'error': 'Para cálculo de inscripción se requieren: institution_id, city_id y program_type_id'
                }

            registration_fee = CalculateRegistrationFeeUseCase(repository_registration_fee).execute(
                institution_id=payload.institution_id,
                city_id=payload.city_id,
                program_type_id=payload.program_type_id
            )
            registration_fee['payment_type_code'] = c.code
            response_data['registration_fee'] = registration_fee

        # Si el concepto es de Matrícula (código 'M') o Extensión (código 'E')
        if c.code in ("M", "E"):
            if not all([payload.weeks, payload.duration_type, payload.institution_id,
                       payload.city_id, payload.country_origin_id, payload.program_type_id]):
                return 400, {
                    'error': 'Para cálculo de matrícula/extensión se requieren: weeks, duration_type, institution_id, city_id, country_origin_id, program_type_id'
                }

            try:
                params = RegistrationDataRequest(
                    program_id=payload.program_id,
                    program_code=payload.program_code,
                    duration_type=payload.duration_type,
                    institution_id=payload.institution_id,
                    city_id=payload.city_id,
                    country_id=payload.country_origin_id,
                    program_type_id=payload.program_type_id,
                    weeks=payload.weeks,
                    intensity_id=payload.intensity_id,
                    is_college=payload.is_college,
                    is_extension=payload.is_extension
                )

                tuition_fee = CalculateTuitionFeeUseCase(repository_sede_pricing).execute(params)
                tuition_fee['payment_type_code'] = c.code
                response_data['tuition_fee'] = tuition_fee
            except IntensityRequiredException as e:
                return 400, {
                    'error': str(e),
                    'requires_intensity': True
                }

        # Si el concepto es de Material (código 'P')
        if c.code == "P":
            # Requiere datos básicos; program_id puede omitirse si program_code='O'
            if not all([payload.institution_id, payload.city_id, payload.program_type_id, payload.weeks]):
                return 400, {
                    'error': 'Para cálculo de material se requieren: institution_id, city_id, program_type_id, weeks (y program_id o program_code="O")'
                }

            try:
                dto = RegistrationDataRequest(
                    program_id=payload.program_id,
                    program_code=payload.program_code,
                    duration_type=payload.duration_type,
                    institution_id=payload.institution_id,
                    city_id=payload.city_id,
                    country_id=payload.country_origin_id,
                    program_type_id=payload.program_type_id,
                    weeks=payload.weeks,
                    intensity_id=payload.intensity_id,
                    is_college=payload.is_college,
                    is_extension=payload.is_extension
                )
                material_cost = CalculateMaterialCostUseCase(repository_sede_pricing).execute(dto)
                material_cost['payment_type_code'] = c.code
                response_data['material_cost'] = material_cost
            except IntensityRequiredException as e:
                return 400, {
                    'error': str(e),
                    'requires_intensity': True
                }
            except ValueError as e:
                return 400, {
                    'error': str(e),
                    'requires_intensity': ('intensity_id' in str(e))
                }
        if c.code == "F":
            if not all([payload.institution_id, payload.city_id, payload.program_type_id]):
                return 400, {
                    'error': 'Para cálculo de booking fee: institution_id, city_id, program_type_id'
                }
            booking_fee_cost = GetBookingFeeCostUseCase(repository_sede_pricing).execute(
                institution_id=payload.institution_id,
                city_id=payload.city_id,
                program_type_id=payload.program_type_id
            )
            booking_fee_cost['payment_type_code'] = c.code
            response_data['booking_fee_cost'] = booking_fee_cost

    return 200, response_data

