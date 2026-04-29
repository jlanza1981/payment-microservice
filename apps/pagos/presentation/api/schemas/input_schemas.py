"""
Schemas de entrada (Input) usando Pydantic para la API de órdenes de pago.
Migración de DRF Serializers a Pydantic Schemas.
"""
from decimal import Decimal
from typing import Optional, Literal

from ninja import Schema
from pydantic import Field


class PaymentAllocationInputSchema(Schema):
    """
    Schema para validar entrada de detalles de orden.
    Equivalente a PaymentOrderDetailInputSerializer.
    """
    payment: int = Field(None, description="ID del pago")
    payment_concept: int = Field(None, description="ID del concepto de pago")
    description: str = Field(None, description="Descripción del concepto de pago")
    quantity: int = Field(..., ge=1, description="Cantidad del concepto de pago")
    unit_price: Decimal = Field(..., ge=Decimal('0.00'), description="Precio unitario del concepto de pago")
    discount_type: Optional[Literal['percentage', 'fixed']] = Field(None, description="Tipo de descuento")
    discount: Optional[Decimal] = Field(default=Decimal('0.00'), description="Monto del descuento")


class PaymentInputSchema(Schema):
    """
    Schema para validar entrada de detalles de orden.
    Equivalente a PaymentOrderDetailInputSerializer.
    """
    invoice: int = Field(None, description="ID de la factura")
    user: int = Field(None, description="ID del estudiante")
    advisor: int = Field(None, description="ID del asesor")
    payment_reference_number: Optional[str] = Field(None, description="Número de referencia del pago")
    payment_method: str = Field(None, description="Método de pago")
    amount: Decimal = Field(..., ge=Decimal('0.00'), description="Monto del pago")
    currency: str = Field(None, description="Moneda de la factura")
    status: str = Field(None, description="Estatus de la factura")
    payer_name: str = Field(None, description="Nombre del pagador")
    payment_terms_conditions: Optional[bool] = Field(..., description="Aceptó términos y condiciones")

class PartialPaymentInputSchema(Schema):
   invoice:int = Field(..., description="Invoice del pago")
   amount:Decimal = Field(..., description="Monto del pago")