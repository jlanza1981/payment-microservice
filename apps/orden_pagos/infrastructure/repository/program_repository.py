from apps.instituciones.models import Cursos, Intensidad


class ProgramRepository:

    @staticmethod
    def get_by_id(program_id) -> Cursos:
        return Cursos.objects.filter(id=program_id).first()

    @staticmethod
    def get_intensity_by_id(intensity_id) -> Intensidad:
        return Intensidad.objects.filter(id=intensity_id).first()
