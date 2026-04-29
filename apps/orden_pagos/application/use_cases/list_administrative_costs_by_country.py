from typing import List, Dict, Any

from apps.administrative_cost_type.infrastructure.repository.administrative_cost_repository import AdministrativeCostRepository

class ListAdministrativeCostsByCountryUseCase:
    def __init__(self, repository: AdministrativeCostRepository):
        self.repository = repository

    def execute(
            self,
            country_origin: str,
            currency_country: str = "USA"
    ) -> List[Dict[str, Any]]:

        return self.repository.list_administrative_cost_by_country(
            country_origin=country_origin,
            currency_country=currency_country
        )
