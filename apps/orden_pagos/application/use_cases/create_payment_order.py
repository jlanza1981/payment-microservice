from dataclasses import asdict
from typing import Dict, Any, List, Optional

from django.db import transaction

from apps.orden_pagos.application.commands import CreatePaymentOrderCommand
from apps.orden_pagos.application.use_cases.check_split_required import CheckSplitRequiredUseCase
from apps.orden_pagos.application.use_cases.prepare_payment_order_data import PreparePaymentOrderDataUseCase
from apps.orden_pagos.application.use_cases.validate_program_duration_type import ValidateProgramDurationTypeUseCase
from apps.orden_pagos.domain.interface.repository.repository_interface import PaymentOrderRepositoryInterface
from apps.orden_pagos.domain.interface.services import PaymentOrderDomainService
from apps.orden_pagos.application.use_cases.convert_program_data_to_instances import \
    ConvertProgramDataToInstancesUseCase
from apps.orden_pagos.infrastructure.repository.opportunities import OpportunitiesRepository
from apps.orden_pagos.infrastructure.repository.payment_concept_repository import PaymentConceptRepository
from apps.user.infrastructure.repository.users_repository import UsersRepository


class CreatePaymentOrderUseCase:

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
    def execute(self, data: Any) -> Dict[str, Any] | List[Any]:

        # Detectar si necesitamos separar las órdenes
        should_split, independent_details, dependent_details = self._check_split_required(data.payment_details)

        if should_split:
            return self._create_split_orders(data, independent_details, dependent_details)
        else:
            # Crear orden normal (única)
            return self._create_single_order(data)

    def _check_split_required(self, payment_details: List[Dict]) -> tuple[bool, List[Dict], List[Dict]]:
        return CheckSplitRequiredUseCase(self.repository_payment_concept).execute(payment_details)

    def _create_single_order(self, data) -> Any:
        """Crea una sola orden con todos los detalles."""
        # Validar tipo de programa y duración si hay programa
        converted_program_data_instance = None
        if data.program_data:
            self._validate_program_duration_type(data.program_data)

            converted_program_data_instance = ConvertProgramDataToInstancesUseCase(
                self.repository_category,
                self.repository_institution,
                self.repository_country,
                self.repository_city,
                self.repository_program,
                self.repository_material_cost_type,
            ).execute(data.program_data)
        # Convertir payment_concept a instancia en todos los detalles
        converted_details = self.convert_payment_type_to_instance(data.payment_details)

        data_dict = asdict(data) if hasattr(data, '__dataclass_fields__') else (
            vars(data).copy() if hasattr(data, '__dict__') else data.copy()
        )
        #data_dict.pop('quotation', None)

        order_data = PreparePaymentOrderDataUseCase(self.repository_user, self.repository_opportunities).execute(data)

        order_data.pop('payment_details', None)
        order_data.pop('program_data', None)
        print('order_data', order_data)
        payment_order = self.repository_payment_order.create(
            order_data=order_data,
            payment_details=converted_details,
            program_data=converted_program_data_instance
        )

        return payment_order

    def _create_split_orders(self, data, independent_details: List[Dict], dependent_details: List[Dict]) -> List[Any]:
        """
        Crea dos órdenes separadas:
        - Una para tipos independientes (sin programa)
        - Otra para tipos dependientes (con programa)
        """
        orders = []

        # Convertir dataclass a dict y eliminar campos temporalmente
        data_dict = asdict(data) if hasattr(data, '__dataclass_fields__') else (
            vars(data).copy() if hasattr(data, '__dict__') else data.copy()
        )
        data_dict.pop('quotation', None)
        data_dict.pop('payment_details', None)
        data_dict.pop('program_data', None)

        order_data = PreparePaymentOrderDataUseCase(self.repository_user, self.repository_opportunities).execute(data)
        independent_details_converted = self.convert_payment_type_to_instance(independent_details)

        order_independent = self.repository_payment_order.create(
            order_data=order_data,
            payment_details=independent_details_converted,
            program_data={}
        )
        orders.append(order_independent)

        if data.program_data:
            self._validate_program_duration_type(data.program_data)

        dependent_details_converted = self.convert_payment_type_to_instance(dependent_details)

        converted_program_data_instance = None
        if data.program_data:
             converted_program_data_instance = self._converted_program_data_instance(data.program_data)

        order_dependent = self.repository_payment_order.create(
            order_data=order_data,
            payment_details=dependent_details_converted,
            program_data=converted_program_data_instance
        )
        orders.append(order_dependent)

        return orders

    def _converted_program_data_instance(self, program_data):
       return ConvertProgramDataToInstancesUseCase(
            self.repository_category,
            self.repository_institution,
            self.repository_country,
            self.repository_city,
            self.repository_program,
            self.repository_material_cost_type,
        ).execute(program_data)

    def convert_payment_type_to_instance(self, details: List[Dict]) -> List[Dict]:
        converted_details = []

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
            converted_details.append(detail_copy)

        return converted_details

    def _validate_program_duration_type(self, program_data: Dict[str, Any]) -> bool:

        return ValidateProgramDurationTypeUseCase(
            self.repository_category,
            self.domain_service
        ).execute(program_data)