from typing import Dict, Any

from apps.administrative_cost_type.infrastructure.repository.administrative_cost_repository import AdministrativeCostRepository


class GetAdministrativeCostByCostTypeUseCase:

    def __init__(self, repository: AdministrativeCostRepository):
        self.repository = repository

    def execute(
            self,
            cost_type: int,
            country_origin: str
    ) -> Dict[str, Any]:
        return self.repository.get_administrative_cost_by_cost_type_and_country(
            cost_type=cost_type,
            country_origin=country_origin
        )