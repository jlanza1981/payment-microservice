import logging
from dataclasses import asdict
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class PrepareInvoiceDetailsDataUseCase:
    def __init__(
        self,
            payment_concept_repository,
            domain_service
    ):
        self.domain_service = domain_service
        self.payment_concept_repository = payment_concept_repository

    def execute(self, invoice_details: list, payment_order)->List[Dict[str, Any]]:
        validated_details = []

        for detail in invoice_details:

            # Manejar dict o InvoiceDetailCommand
            if isinstance(detail, dict):
                payment_concept_id = detail.get("payment_concept")
                quantity = detail.get("quantity")
                unit_price = detail.get("unit_price")
            else:
                payment_concept_id = getattr(detail, "payment_concept", None)
                quantity = getattr(detail, "quantity", None)
                unit_price = getattr(detail, "unit_price", None)

            # Validaciones básicas
            if not payment_concept_id:
                logger.error("Cada detalle debe tener un concepto de pago (payment_concept)")


            if not quantity:
                logger.error("Cada detalle debe tener una cantidad (quantity)")

            if not unit_price:
                logger.error("Cada detalle debe tener un precio unitario (unit_price)")

            # Obtener concepto
            payment_concept = self.payment_concept_repository.get_concept_by_id(
                payment_concept_id
            )

            if not payment_concept:
                logger.error(f"No se encontró el concepto de pago con ID {payment_concept_id}")

            # Validación de dominio
            self.domain_service.validate_payment_concept_requires_program(
                payment_concept,
                payment_order
            )

            # Crear detalle validado
            if isinstance(detail, dict):
                validated_detail = detail.copy()
                validated_detail["payment_concept"] = payment_concept
            else:
                validated_detail = asdict(detail)
                validated_detail["payment_concept"] = payment_concept

            # Normalizar discount_type
            if not validated_detail.get("discount_type"):
                validated_detail["discount_type"] = None

            validated_details.append(validated_detail)

        return validated_details
