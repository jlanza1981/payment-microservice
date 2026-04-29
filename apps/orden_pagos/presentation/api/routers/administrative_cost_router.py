"""
Router para endpoints de Administrative Costs (Costos Administrativos).
Maneja consultas de tipos de costos administrativos por país y moneda.
"""
from typing import List

from django.http import HttpRequest
from ninja import Router

from apps.core.infrastructure.security.auth_bearer import AuthBearer
from apps.orden_pagos.application.use_cases import (
    GetAdministrativeCostByCostTypeUseCase,
    ListAdministrativeCostsByCountryUseCase,
)
from apps.administrative_cost_type.infrastructure.repository.administrative_cost_repository import AdministrativeCostRepository
from apps.orden_pagos.presentation.api.schemas import AdministrativeCostSchema


# Crear sub-router para costos administrativos
administrative_costs_router = Router(tags=["Administrative Costs"], auth=AuthBearer())


@administrative_costs_router.get(
    "/by-cost-type/{cost_type_id}/{country_origin}/",
    response={200: AdministrativeCostSchema, 404: dict},
    summary="Obtener costo administrativo por país y tipo"
)
def get_administrative_cost_by_cost_type(
        request: HttpRequest,
        cost_type_id: int,
        country_origin: str
):
    repository = AdministrativeCostRepository()
    cost = GetAdministrativeCostByCostTypeUseCase(repository).execute(
        cost_type=cost_type_id,
        country_origin=country_origin,
    )

    if not cost:
        return 404, {
            'error': f'No se encontró costo administrativo para país, tipo {cost_type_id}'
        }

    return 200, cost


@administrative_costs_router.get(
    "/list-administrative-costs-by-country/{country_id}/",
    response={200: List[AdministrativeCostSchema]},
    summary="Listar tipos de costos administrativos por país"
)
def list_administrative_costs_by_country(
        request: HttpRequest,
        country_id: str,
        currency_country: str = "USA"
):

    repository = AdministrativeCostRepository()
    costs_list = ListAdministrativeCostsByCountryUseCase(repository).execute(
        country_origin=country_id,
        currency_country=currency_country
    )
    # Construir respuesta serializando cada item correctamente
    response = [AdministrativeCostSchema.from_orm(cost) for cost in costs_list]
    return 200, response
