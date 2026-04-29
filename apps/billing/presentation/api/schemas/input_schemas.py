"""
Schemas de entrada (Input) usando Pydantic para la API de órdenes de pago.
Migración de DRF Serializers a Pydantic Schemas.
"""
from decimal import Decimal
from typing import Optional, Literal

from ninja import Schema
from pydantic import Field


class InvoiceDetailInputSchema(Schema):
    """
    Schema para validar entrada de detalles de orden.
    Equivalente a PaymentOrderDetailInputSerializer.
    """
    payment_concept: int = Field(None, description="ID del concepto de pago")
    quantity: int = Field(..., ge=1, description="Cantidad del concepto de pago")
    unit_price: Decimal = Field(..., ge=Decimal('0.00'), description="Precio unitario del concepto de pago")
    discount_type: Optional[Literal['percentage', 'fixed']] = Field(None, description="Tipo de descuento")
    discount: Optional[Decimal] = Field(default=Decimal('0.00'), description="Monto del descuento")


class InvoiceInputSchema(Schema):
    """
    Schema para validar entrada de detalles de orden.
    Equivalente a PaymentOrderDetailInputSerializer.
    """
    user: int = Field(None, description="ID del estudiante")
    advisor: int = Field(None, description="ID del asesor")
    payment_order: int = Field(None, description="ID de la orden de pago")
    currency: str = Field(None, description="Moneda de la factura")
    status: str = Field(None, description="Estatus de la factura")
    notes: Optional[str] = Field(None, description="Notas adicionales de la factura")
