


class GetByIdWithRelations:
    def __init__(self, repository):
        self.repository = repository

    def execute(self, invoice_id:int):
        return self.repository.get_by_id_with_relations(invoice_id)
