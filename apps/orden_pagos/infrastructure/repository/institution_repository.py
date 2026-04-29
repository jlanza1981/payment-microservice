from django.db.models import QuerySet

from apps.instituciones.models import Institucion


class InstitutionRepository:

    @staticmethod
    def get_all_institutions() -> QuerySet[Institucion]:
        return Institucion.objects.all()

    @staticmethod
    def get_by_id(institution_id:int) -> Institucion:
        return Institucion.objects.filter(id=institution_id).first()
