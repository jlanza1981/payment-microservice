from apps.instituciones.models import TiposCostoMaterial


class MaterialCostTypeRepository:

    @staticmethod
    def get_by_id(material_cost_type_id) -> TiposCostoMaterial:
        return TiposCostoMaterial.objects.filter(id=material_cost_type_id).first()
