from django.db.models import QuerySet

from apps.crm.models import Oportunidades


class OpportunitiesRepository:

    @staticmethod
    def get_all_opportunity_id() -> QuerySet[Oportunidades, Oportunidades]:
        return Oportunidades.objects.all()

    @staticmethod
    def get_by_id(opportunity_id) -> Oportunidades:
        if isinstance(opportunity_id, Oportunidades):
            return opportunity_id

        return Oportunidades.objects.filter(id=opportunity_id).first()
