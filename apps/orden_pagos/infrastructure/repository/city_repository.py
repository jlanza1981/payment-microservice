from django.db.models import QuerySet

from apps.administrador.models import Ciudades


class CityRepository:

    @staticmethod
    def get_all_cities() -> QuerySet[Ciudades, Ciudades]:
        return Ciudades.objects.all()

    @staticmethod
    def get_by_id(city_id) -> Ciudades:
        return Ciudades.objects.filter(id=city_id).first()
