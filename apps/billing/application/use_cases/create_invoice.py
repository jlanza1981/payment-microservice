import logging
from dataclasses import asdict
from typing import Optional

from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.billing.application.use_cases.prepare_invoice_data import PrepareInvoiceDataUseCase
from apps.billing.application.use_cases.prepare_invoice_details_data import PrepareInvoiceDetailsDataUseCase
from apps.billing.domain.interface.repository.invoice_repository_interface import InvoiceRepositoryInterface
from apps.billing.domain.interface.services import InvoiceDomainService
from apps.billing.models import Invoice
from apps.orden_pagos.application.use_cases import GetPaymentOrderByIdUseCase
from apps.orden_pagos.domain.interface.repository.repository_interface import PaymentOrderRepositoryInterface
logger = logging.getLogger(__name__)


class CreateInvoiceUseCase:
    def __init__(
          self,
          domain_service: InvoiceDomainService,
          repository: InvoiceRepositoryInterface,
          payment_order_repository:PaymentOrderRepositoryInterface,
          user_repository,
          payment_concept_repository
    ):
        self.domain_service = domain_service
        self.invoice_repository = repository
        self.payment_order_repository = payment_order_repository
        self.user_repository = user_repository
        self.payment_concept_repository = payment_concept_repository
        self.prepare_invoice_data_uc = PrepareInvoiceDataUseCase(user_repository, payment_order_repository)
        self.prepare_invoice_details_data_uc = PrepareInvoiceDetailsDataUseCase(payment_concept_repository, self.domain_service)

    @transaction.atomic
    def execute(self, data) -> Optional[Invoice]:
        # Obtener instancias de las entidades relacionadas
        payment_order = self._get_payment_order(data.payment_order)

        # Validar reglas de negocio
        is_valid = self.domain_service.validate_invoice_creation(
            student=payment_order.student,
            payment_order=payment_order,
            invoice_details=data.invoice_details
        )
        
        if not is_valid:
            logger.error(
                f"❌ No se puede crear la factura para la orden {payment_order.order_number}. "
                "Revisa los logs anteriores para más detalles."
            )
            return None  # Se detiene aquí sin lanzar excepción

        # Crear la factura usando el repositorio
        # ...existing code...
        # Remover invoice_details de data antes de preparar
        data_dict = asdict(data)
        invoice_details = data_dict.pop('invoice_details', None)

        invoice_data = self.prepare_invoice_data_uc.execute(data_dict)
        validated_details = self.prepare_invoice_details_data_uc.execute(invoice_details, payment_order)
        invoice = self.invoice_repository.create(
            invoice_data=invoice_data,
            invoice_details=validated_details
        )

        return invoice

    def _get_payment_order(self, payment_order_id: int):
        """Obtiene la orden de pago y valida que exista."""
        if not payment_order_id:
            raise ValidationError("El ID de la orden de pago es obligatorio")

        payment_order = GetPaymentOrderByIdUseCase(self.payment_order_repository).execute(payment_order_id)
        if not payment_order:
            raise ValidationError(f"No se encontró la orden de pago con ID {payment_order_id}")

        return payment_order