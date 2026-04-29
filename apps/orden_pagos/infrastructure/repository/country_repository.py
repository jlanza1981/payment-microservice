from django.db.models import QuerySet

from apps.administrador.models import Paises


class CountryRepository:

    @staticmethod
    def get_all_countries() -> QuerySet[Paises, Paises]:
        return Paises.objects.all()

    @staticmethod
    def get_by_id(country_id:str) -> Paises:
        return Paises.objects.filter(id=country_id).first()
