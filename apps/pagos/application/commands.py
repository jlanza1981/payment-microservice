from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Any, Dict


@dataclass
class PaymentAllocationCommand:
    payment: int
    invoice_detail: int
    payment_concept: int
    amount_applied: str
    status: str


@dataclass
class CreatePaymentCommand:
    invoice: int
    user: int
    advisor: int
    payment_reference_number: str
    payment_method: str
    amount: Decimal
    amount_paid: Decimal
    currency: str
    status: str
    payer_name: str
    payment_terms_conditions: Optional[bool]
    payment_allocation: List[PaymentAllocationCommand]



# Comandos específicos para cambiar el estado de un pago

@dataclass
class MarkPaymentAsPaidCommand:
    payment_id: int
    created_at: Optional[datetime] = None
    payment_reference_number: Optional[str] = None

@dataclass
class ProcessPaymentCommand:
    payment_order_id: str
    payment_provider: str           # ej. 'paypal', 'stripe'
    provider_transaction_id: str    # capture_id, charge_id, etc.
    amount: Decimal
    currency: str
    additional_data: dict = None    # cualquier info extra del proveedor
    payer_name: str = None          # Nombre del pagador


@dataclass
class ProcessPaymentResult:
    """Resultado del procesamiento de un pago"""
    invoice: Any  # Invoice model instance
    payment: Any  # Payment model instance
    payment_receipt: Optional[Any] = None  # PaymentReceipt model instance


class CreatePaymentReceiptCommand:
    invoice: int
    payment: int
    student: int
    amount_paid: Decimal
    previous_balance: Decimal
    new_balance: Decimal
    payment_method: str
    payment_date: datetime
    currency: str
    notes: str
@dataclass
class CreatePaymentTransactionCommand:
    paypal_order_id: str
    payment_order: Any
    currency: str
    amount: Decimal
    status: str
    gross_amount: Decimal
    paypal_fee: Decimal
    net_amount: Decimal
    payee_email: str
    payee_merchant_id: str
    resource_json: Dict[str, str]
    payment: Optional[int] = None