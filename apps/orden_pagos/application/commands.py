from dataclasses import dataclass
from typing import List, Optional
from decimal import Decimal


@dataclass
class CreatePaymentOrderCommand:
    student: int
    advisor: int
    opportunity: int
    currency: str
    payment_details: List[dict]
    program_data: dict = None
    quotation: Optional[int] = None
    status: Optional[str] = None
    allows_partial_payment: bool = True
    minimum_payment_amount: Optional[Decimal] = None
    suggested_payment_amount: Optional[Decimal] = None


@dataclass
class UpdatePaymentOrderCommand:
    order_id: int
    suggested_payment_amount: Optional[Decimal] = None
    payment_details: Optional[List[dict]] = None
    program_data: Optional[dict] = None


@dataclass
class DeletePaymentOrderCommand:
    """
    Comando para eliminar una orden de pago.
    """
    order_id: int


# Comandos específicos para cambiar el estado de una orden

@dataclass
class MarkOrderAsPaidCommand:
    order_id: int


@dataclass
class CancelOrderCommand:
    order_id: int
    cancellation_reason: str


@dataclass
class VerifyOrderCommand:
    """
    Comando para verificar una orden por tesorería.
    Transición: PAID → VERIFIED
    """
    order_id: int
    verified_by: int
    verification_notes: Optional[str] = None


@dataclass
class CreateExoneratedPaymentCommand:
    """
    Comando para crear un pago exonerado (gratuito).
    Permite crear orden nueva o exonerar orden existente.
    """
    payer_name: str
    # Para orden nueva
    student_id: Optional[int] = None
    concepts: Optional[List[dict]] = None
    # Para orden existente
    order_payment_id: Optional[int] = None
    # Opcionales
    advisor_id: Optional[int] = None
    notes: Optional[str] = ""
