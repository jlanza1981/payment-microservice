from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Any

from ninja import Schema


class PaymentAllocationSchema(Schema):
    """
    Schema para los detalles de la orden de pago.
    Equivalente a PaymentOrderDetailSerializer.
    """
    id: int
    payment: int
    invoice_detail: int
    payment_concept: int
    amount_applied: Decimal
    status: str
    payment_concept_name: Optional[str] = None
    payment_concept_code: Optional[str] = None


class PaymentSchema(Schema):
    """
    Schema completo para órdenes de pago.
    Equivalente a PaymentOrderSerializer.
    Incluye detalles y programa anidados.
    """
    id: int
    payment_number: str
    invoice: int
    user: int
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    advisor: int
    payment_method: str
    status: str
    payer_name: str
    currency: str
    amount: Decimal
    advisor_name: Optional[str] = None
    payment_terms_conditions: bool
    payment_allocation: List[PaymentAllocationSchema] = []
    payment_reference_number: Optional[str] = None
    payment_date: Optional[datetime] = None
    verification_date: Optional[datetime] = None
    payment_proof: Optional[str] = None

    @classmethod
    def from_orm(cls, obj):
        """Convierte un modelo Django a schema, manejando relaciones anidadas"""
        # ⚠️ IMPORTANTE: Extraer TODOS los IDs y valores primitivos PRIMERO
        payment_id = obj.id
        invoice = getattr(obj, 'invoice_id', None)
        payment_number = obj.payment_number
        user = getattr(obj, 'user_id', None)
        advisor_id = getattr(obj, 'advisor_id', None)
        currency = getattr(obj, 'currency', 'USD')
        status = getattr(obj, 'status', None)
        amount = getattr(obj, 'amount', None)
        payer_name = getattr(obj, 'payer_name', None)
        payment_method = getattr(obj, 'payment_method', None)
        payment_terms_conditions = getattr(obj, 'payment_terms_conditions', True)

        # Extraer nombres (pueden requerir acceso a relaciones)
        student_name = obj.user.get_full_name() if getattr(obj, 'user', None) else None
        student_email = obj.user.email if getattr(obj, 'user', None) else None
        advisor_name = obj.advisor.get_full_name() if getattr(obj, 'advisor', None) else None

        # Convertir detalles usando from_orm (después de extraer primitivos)
        details = []
        allocations_qs = getattr(obj, 'allocations', None)
        if allocations_qs is not None:
            iterable = allocations_qs.all() if hasattr(allocations_qs, 'all') else allocations_qs
            for alloc in iterable:
                payment_id_fk = getattr(alloc, 'payment_id', None)
                invoice_detail_id = getattr(alloc, 'invoice_detail_id', None)
                concept = getattr(alloc, 'payment_concept', None)
                concept_id = getattr(concept, 'id', None)
                details.append({
                    'id': alloc.id,
                    'payment': payment_id_fk,
                    'invoice_detail': invoice_detail_id,
                    'payment_concept': concept_id,
                    'amount_applied': getattr(alloc, 'amount_applied', Decimal('0.00')),
                    'status': getattr(alloc, 'status', None),
                    'payment_concept_name': getattr(concept, 'name', None),
                    'payment_concept_code': getattr(concept, 'code', None),
                })
        # Construir y loggear payload para Pydantic
        data = {
            'id': payment_id,
            'payment_number': payment_number,
            'invoice': invoice,
            'user': user,
            'user_name': student_name,
            'user_email': student_email,
            'advisor': advisor_id,
            'advisor_name': advisor_name,
            'currency': currency,
            'status': status,
            'amount': amount,
            'payer_name': payer_name,
            'payment_method': payment_method,
            'payment_terms_conditions': payment_terms_conditions,
            'payment_allocation': details,
        }
        # print(f"🧪 PaymentOrderSchema.from_orm payload -> student: {data['student']}, advisor: {data['advisor']}")

        return cls(**data)

    class Config:
        from_attributes = True


class StudentPaymentHistorySchema(Schema):
    """Schema para de pago del estudiante.  """
    id: int
    student_id: int
    amount: Decimal
    currency: str
    status: str
    date: str
    source: str  # "legacy" | "new"
    method: Optional[str]
    invoice_id: Optional[int]
    invoice_number: Optional[str]
    payer_name: Optional[str]
    reference: Optional[str] = None
    file: Optional[str] = None
    total: Optional[Decimal] = None
    amount_paid: Optional[Decimal] = None
    balance_due: Optional[Decimal] = None

    @classmethod
    def from_orm(cls, obj):
        id = obj.id
        student_id = getattr(obj, 'student_id', None)
        invoice_id = getattr(obj, 'invoice_id', None)
        invoice_number = getattr(obj, 'invoice_number', None)
        currency = getattr(obj, 'currency', '')
        amount = getattr(obj, 'amount', None)
        payer_name = getattr(obj, 'payer_name', None)
        # Convert lazy translation proxy to string
        method_value = getattr(obj, 'method', None)
        method = str(method_value) if method_value is not None else None
        source = getattr(obj, 'source', '')
        reference = getattr(obj, 'reference', '')
        file = getattr(obj, 'file', '')
        date = getattr(obj, 'date', None)
        status = getattr(obj, 'status', None)
        total = getattr(obj, 'total', None)
        amount_paid = getattr(obj, 'amount_paid', None)
        balance_due = getattr(obj, 'balance_due', None)

        # Construir y loggear payload para Pydantic
        data = {
            'id': id,
            'student_id':student_id,
            'invoice_number': invoice_number,
            'invoice_id': invoice_id,
            'currency': currency,
            'amount': amount,
            'payer_name': payer_name,
            'method': method,
            'source': source,
            'reference': reference,
            'file': file,
            'date': date,
            'status': status,
            'total': total,
            'amount_paid': amount_paid,
            'balance_due': balance_due,
        }
        #print(f"🧪 StudentPaymentHistorySchema.from_orm payload: {data}")

        return cls(**data)

    class Config:
        from_attributes = True


class PaginatedListSchema(Schema):
    """
    Schema genérico para paginación.
    Puede usarse con cualquier tipo de datos.
    """
    count: int
    next: Optional[str] = None
    previous: Optional[str] = None
    results: List[Any]

    class Config:
        from_attributes = True


