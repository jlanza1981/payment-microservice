"""
Schemas para pagos exonerados (gratuitos).
Permite crear órdenes de pago sin costo y registrar el asiento contable.
"""
from typing import Optional, List

from ninja import Schema
from pydantic import Field, model_validator

from apps.billing.presentation.api.schemas.output_schemas import InvoiceSchema
from apps.orden_pagos.presentation.api.schemas.output_schemas_payment_order import PaymentOrderSchema
from apps.pagos.presentation.api.schemas.output_schemas import PaymentSchema


class ConceptInput(Schema):
    """Concepto para orden de pago exonerada"""
    concept_id: int = Field(..., description="ID del concepto de pago")
    quantity: int = Field(default=1, ge=1, description="Cantidad")


class ExoneratedPaymentInput(Schema):
    """
    Schema para procesar pagos exonerados (gratuitos).
    Puede crear una nueva orden o usar una existente.
    """
    # Para orden nueva
    student_id: Optional[int] = Field(None, description="ID del estudiante para orden nueva")
    concepts: Optional[List[ConceptInput]] = Field(None, description="Lista de conceptos para orden nueva")

    # Para orden existente
    order_payment_id: Optional[int] = Field(None, description="ID de orden existente")

    # Datos del pago
    payer_name: str = Field(..., max_length=50, description="Nombre del pagador")
    advisor_id: Optional[int] = Field(None, description="ID del asesor")
    notes: Optional[str] = Field(default="", description="Notas adicionales")

    @model_validator(mode='after')
    def validate_order_source(self):
        """Valida que se proporcione orden existente O datos para crear nueva"""
        has_new_order = self.student_id is not None and self.concepts is not None
        has_existing_order = self.order_payment_id is not None

        if not (has_new_order or has_existing_order):
            raise ValueError(
                "Debe proporcionar 'order_payment_id' para orden existente o 'student_id' y 'concepts' para orden nueva"
            )

        if has_new_order and has_existing_order:
            raise ValueError(
                "No puede proporcionar orden existente y datos para orden nueva al mismo tiempo"
            )

        return self


class PaymentDataOutput(Schema):
    """Datos del pago exonerado creado"""
    payment_order: PaymentOrderSchema
    invoice: InvoiceSchema
    payment: PaymentSchema


class ExoneratedPaymentOutput(Schema):
    """Respuesta exitosa del endpoint de pago exonerado"""
    success: bool
    message: str
    data: PaymentDataOutput


class ErrorResponse(Schema):
    """Respuesta de error del endpoint"""
    success: bool = False
    message: str
    detail: Optional[str] = None
