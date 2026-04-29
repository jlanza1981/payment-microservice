class ValidateProgramDurationTypeUseCase:
    def __init__(self, repository_category, domain_service):
        self.repository_category = repository_category
        self.domain_service = domain_service
    def execute(self, program_data) -> bool:
        if 'program_type' in program_data and 'duration_type' in program_data:
            program_type = self.repository_category.get_by_id(program_data['program_type'])
            if program_type:
                self.domain_service.validate_program_duration_type(
                    program_type.nombre,
                    program_data['duration_type']
                )
        return True
