from typing import Dict, Any, List

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.orden_pagos.application.use_cases import GetPaymentOrderByIdUseCase
from apps.orden_pagos.application.use_cases.convert_program_data_to_instances import \
    ConvertProgramDataToInstancesUseCase
from apps.orden_pagos.application.use_cases.validate_program_duration_type import ValidateProgramDurationTypeUseCase
from apps.orden_pagos.domain.interface.repository.repository_interface import PaymentOrderRepositoryInterface
from apps.orden_pagos.domain.interface.services import PaymentOrderDomainService
from apps.orden_pagos.infrastructure.repository.opportunities import OpportunitiesRepository
from apps.orden_pagos.infrastructure.repository.payment_concept_repository import PaymentConceptRepository
from apps.user.infrastructure.repository.users_repository import UsersRepository


class UpdatePaymentOrderUseCase:
    """
    Caso de uso: Actualizar una orden de pago existente.

    Responsabilidades:
    - Validar que la orden exista
    - Validar cambios de estado
    - Actualizar detalles y programa si es necesario
    """

    def __init__(
            self,
            domain_service: PaymentOrderDomainService,
            payment_concept_uc,
            type_administrative_cost_uc,
            repository_payment_order: PaymentOrderRepositoryInterface,
            repository_category,
            repository_institution,
            repository_country,
            repository_city,
            repository_program,
            repository_material_cost_type,
    ):
        self.domain_service = domain_service
        self.payment_concept_uc = payment_concept_uc
        self.type_administrative_cost_uc = type_administrative_cost_uc
        self.repository_payment_order = repository_payment_order
        self.repository_payment_concept = PaymentConceptRepository
        self.repository_user = UsersRepository
        self.repository_opportunities = OpportunitiesRepository
        self.repository_category = repository_category
        self.repository_institution = repository_institution
        self.repository_country = repository_country
        self.repository_city = repository_city
        self.repository_program = repository_program
        self.repository_material_cost_type = repository_material_cost_type

    @transaction.atomic
    def execute(self, data):
        payment_order = GetPaymentOrderByIdUseCase(self.repository_payment_order).execute(data.order_id)
        
        if not payment_order:
            raise ValidationError({'order_id': _('Orden de pago no encontrada')})

        if not payment_order.status in ['PENDING', 'ACTIVE']:
            raise ValidationError({
                'order': _('Solo se pueden actualizar órdenes en estado PENDING o ACTIVE')
            })

        payload = {}
        if getattr(data, 'suggested_payment_amount', None) is not None:
            payload['suggested_payment_amount'] = data.suggested_payment_amount
        if getattr(data, 'payment_details', None) is not None:
            payload['payment_details'] = self.convert_payment_type_to_instance(data.payment_details)

        if getattr(data, 'program_data', None):

            self._validate_program_duration_type(data.program_data)

            payload['program_data'] = ConvertProgramDataToInstancesUseCase(
                self.repository_category,
                self.repository_institution,
                self.repository_country,
                self.repository_city,
                self.repository_program,
                self.repository_material_cost_type,
            ).execute(data.program_data)

        # 4. Actualizar orden (las señales actualizarán total_order automáticamente)
        payment_order = self.repository_payment_order.update(data.order_id, payload)

        return payment_order

    def convert_payment_type_to_instance(self, details: List[Dict]) -> List[Dict]:
        converted_detailss = []

        for detail in details:
            detail_copy = detail.copy()
            payment_concept = detail.get('payment_concept')
            type_administrative_cost = detail.get('type_administrative_cost')

            instance_payment_concept = self.payment_concept_uc.execute(payment_concept)
            if instance_payment_concept:
                detail_copy['payment_concept'] = instance_payment_concept
            if type_administrative_cost:
                instance_type_administrative_cost = self.type_administrative_cost_uc.execute(type_administrative_cost)
                if instance_type_administrative_cost:
                    detail_copy['type_administrative_cost'] = instance_type_administrative_cost
            converted_detailss.append(detail_copy)

        return converted_detailss

    def _validate_program_duration_type(self, program_data: Dict[str, Any]) -> bool:

        return ValidateProgramDurationTypeUseCase(
            self.repository_category,
            self.domain_service
        ).execute(program_data)
