from typing import List, Dict, Optional

from apps.orden_pagos.application.use_cases.get_payment_concepts import GetConceptByIdUseCase
from apps.orden_pagos.application.use_cases.get_admin_fee_split_order import GetAdminFeeSplitOrderUseCase


class CheckSplitRequiredUseCase:
    def __init__(self, repository_payment_concept):
        self.repository_payment_concept = repository_payment_concept

    def execute(self, payment_details) -> tuple[bool, List[Dict], List[Dict]]:
        independent_details = []
        dependent_details = []

        for detail in payment_details:
            payment_concept = detail.get('payment_concept')
            if payment_concept:
                instance_payment_concept = GetConceptByIdUseCase(self.repository_payment_concept).execute(payment_concept)
                if instance_payment_concept:
                    split: Optional[bool] = GetAdminFeeSplitOrderUseCase(self.repository_payment_concept).execute(instance_payment_concept.id)
                    if bool(split):
                        independent_details.append(detail)
                    else:
                        dependent_details.append(detail)

        should_split = len(independent_details) > 0 and len(dependent_details) > 0

        return should_split, independent_details, dependent_details