class GetAdminFeeSplitOrderUseCase:
    def __init__(self, repository_payment_concept):
        self.repository_payment_concept = repository_payment_concept
    def execute(self, payment_concept_id):
        return self.repository_payment_concept.get_admin_fee_split_order(payment_concept_id)