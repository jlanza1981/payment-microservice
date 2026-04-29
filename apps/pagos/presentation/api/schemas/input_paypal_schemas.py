from decimal import Decimal

from ninja import Schema
from pydantic import Field

class CreateOrderPaypalSchema(Schema):
    payment_order_id: int = Field(None, description="ID de la orden de pago.")

class CaptureOrderPaypalSchema(Schema):
    order_id: str = Field(..., description="ID de la orden de PayPal que se desea capturar.")
    payment_order_id: int = Field(None, description="ID de la orden de pago del sistema.")
