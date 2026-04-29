from typing import List

from apps.administrador.models import Categorias


class CategoryRepository:

    @staticmethod
    def get_all_categories() -> List[Categorias]:
        return Categorias.objects.all()

    @staticmethod
    def get_by_id(category_id) -> Categorias:
        return Categorias.objects.filter(id=category_id).first()
