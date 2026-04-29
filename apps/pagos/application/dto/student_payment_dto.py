from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Any


@dataclass(frozen=True)
class StudentPaymentDTO:
    """
    DTO inmutable para representar un pago de estudiante.
    """
    id: int
    student_id: int
    amount: Decimal
    currency: str
    date: str
    source: str  # "legacy" | "new"
    status: str
    method: Optional[str]
    invoice_id: Optional[int]
    invoice_number: Optional[str]
    invoice: Any
    payer_name: Optional[str]
    reference: Optional[str] = None
    file: Optional[str] = None
    total: Optional[Decimal] = None
    amount_paid: Optional[Decimal] = None
    balance_due: Optional[Decimal] = None
