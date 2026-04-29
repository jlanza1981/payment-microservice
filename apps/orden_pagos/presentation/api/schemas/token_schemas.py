"""
Schemas para validación y generación de tokens de pago.
"""
from datetime import date
from decimal import Decimal
from typing import Optional

from ninja import Schema


class ValidatePaymentTokenInputSchema(Schema):
    """
    Schema de entrada para validar un token de pago.
    """
    token: str


class ValidatePaymentTokenOutputSchema(Schema):
    """
    Schema de salida cuando el token es válido.
    Retorna solo la validación y la orden de pago completa.
    """
    valid: bool
    message: str
    expires_at: date
    payment_order: dict
    status: Optional[str] = None


class TokenExpiredErrorSchema(Schema):
    """
    Schema de error cuando el token ha expirado.
    """
    valid: bool = False
    expired: bool = True
    message: str
    error: str


class GeneratePaymentLinkOutputSchema(Schema):
    """
    Schema de salida cuando se genera un enlace de pago.
    """
    success: bool
    token: str
    payment_link: str
    expires_at: date
    order_id: int
    order_number: str
    total_amount: Decimal
    balance_due: Decimal
    message: str

