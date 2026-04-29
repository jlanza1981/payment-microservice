from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional
from datetime import datetime


@dataclass
class InvoiceDetailCommand:
    """
    Comando para un detalle de factura.
    """
    payment_concept: int
    description: str
    quantity: int
    unit_price: Decimal
    discount: Optional[Decimal] = Decimal('0.00')


@dataclass
class CreateInvoiceCommand:
    user: int
    advisor: int
    payment_order: int
    invoice_details: List[InvoiceDetailCommand]
    status: Optional[str] = "I"  # Default: Emitida
    currency: str = "USD"
    taxes: Optional[Decimal] = Decimal('0.00')
    notes: Optional[str] = None


@dataclass
class CreateInvoiceFromDictCommand:
    user: int
    advisor: int
    payment_order: int
    invoice_details: List[dict]
    status: Optional[str] = "I"  # I=Emitida, E=Exonerada, B=Borrador
    currency: str = "USD"
    taxes: Decimal = Decimal('0.00')
    notes: Optional[str] = None


@dataclass
class UpdateInvoiceCommand:
    """
    Comando para actualizar una factura existente.
    Solo se pueden actualizar facturas en estado Borrador o Emitida.
    """
    invoice_id: int
    invoice_details: Optional[List[dict]] = None
    currency: Optional[str] = None
    taxes: Optional[Decimal] = None
    notes: Optional[str] = None


@dataclass
class CancelInvoiceCommand:
    """
    Comando para anular una factura.
    """
    invoice_id: int
    cancellation_reason: str
    cancelled_by: Optional[int] = None


@dataclass
class VerifyInvoiceCommand:
    """
    Comando para verificar una factura por tesorería.
    Transición: PV (Pendiente Verificar) → V (Verificada)
    """
    invoice_id: int
    verified_by: int
    verification_notes: Optional[str] = None


@dataclass
class MarkInvoiceAsPaidCommand:
    """
    Comando para marcar una factura como pagada.
    Se usa cuando se registra un pago completo.
    """
    invoice_id: int
    payment_date: Optional[str] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class ApplyCreditToInvoiceCommand:
    """
    Comando para aplicar un crédito/abono a una factura.
    """
    invoice_id: int
    credit_id: int
    amount: Decimal
    applied_by: int
    notes: Optional[str] = None


@dataclass
class GenerateInvoicePDFCommand:
    """
    Comando para generar el PDF de una factura.
    """
    invoice_id: int
    regenerate: bool = False  # Si es True, regenera aunque ya exista
    send_email: bool = False  # Si es True, envía por correo después de generar


@dataclass
class SendInvoiceEmailCommand:
    """
    Comando para enviar una factura por correo electrónico.
    """
    invoice_id: int
    recipient_email: Optional[str] = None  # Si no se especifica, usa el email del estudiante
    cc_emails: Optional[List[str]] = None
    subject: Optional[str] = None
    message: Optional[str] = None


@dataclass
class CreateExoneratedInvoiceCommand:
    """
    Comando para crear una factura exonerada (sin pago).
    Similar a CreateInvoiceCommand pero con status='E' por defecto.
    """
    user: int
    advisor: int
    payment_order: int
    invoice_details: List[dict]
    currency: str = "USD"
    notes: Optional[str] = "Factura exonerada"
    exoneration_reason: Optional[str] = None
    approved_by: Optional[int] = None


@dataclass
class RefundInvoiceCommand:
    """
    Comando para procesar un reembolso de una factura.
    """
    invoice_id: int
    refund_amount: Decimal
    refund_reason: str
    refund_method: str  # 'cash', 'transfer', 'credit'
    processed_by: int
    notes: Optional[str] = None


@dataclass
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