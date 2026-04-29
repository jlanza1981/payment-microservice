from typing import Dict, Any


class ConvertProgramDataToInstancesUseCase:

    def __init__(
        self,
        repository_category,
        repository_institution,
        repository_country,
        repository_city,
        repository_program,
        repository_material_cost_type,
    ):
        self.repositories = {
            "program_type": repository_category,
            "institution": repository_institution,
            "country": repository_country,
            "city": repository_city,
            "program": repository_program,
            "intensity": repository_program,  # Usa el mismo repository_program para intensity
            "material_cost_type": repository_material_cost_type,
        }

    def execute(self, data_program: Dict[str, Any]) -> Dict[str, Any]:

        program = data_program.copy()

        for field, repository in self.repositories.items():

            value = program.get(field)

            if not value:
                continue

            # Si ya es una instancia (no es id)
            if not isinstance(value, (int, str)):
                continue

            if field == 'intensity':
                instance = repository.get_intensity_by_id(value)
            else:
                instance = repository.get_by_id(value)

            if instance:
                program[field] = instance

        return program