from decimal import Decimal
from typing import List, Optional

from ninja import Schema


class InvoiceDetailSchema(Schema):
    """
    Schema para los detalles de la orden de pago.
    Equivalente a PaymentOrderDetailSerializer.
    """
    id: int
    payment_concept: int
    description: str
    amount: Decimal
    quantity: int
    unit_price: Decimal
    payment_concept_name: Optional[str] = None
    payment_concept_code: Optional[str] = None
    discount_type: Optional[str] = None
    discount: Optional[Decimal] = Decimal('0.00')
    sub_total: Optional[Decimal]


class InvoiceSchema(Schema):
    """
    Schema completo para órdenes de pago.
    Equivalente a PaymentOrderSerializer.
    Incluye detalles y programa anidados.
    """
    id: int
    payment_order: int
    user: int
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    advisor: int
    advisor_name: Optional[str] = None
    currency: str
    status: str
    total: Optional[Decimal]
    invoice_details: List[InvoiceDetailSchema] = []

    @classmethod
    def from_orm(cls, obj):
        """Convierte un modelo Django a schema, manejando relaciones anidadas"""
        invoice_id = obj.id
        invoice_number = getattr(obj, 'invoice_number', None)
        payment_order_id = getattr(obj, 'payment_order_id', None)
        student_id = getattr(obj, 'user_id', None)
        advisor_id = getattr(obj, 'advisor_id', None)
        currency = getattr(obj, 'currency', 'USD')
        status = getattr(obj, 'status', None)
        total = getattr(obj, 'total', None)
        print('total', total)
        # Extraer nombres (pueden requerir acceso a relaciones)
        student_name = obj.user.get_full_name() if getattr(obj, 'user', None) else None
        student_email = obj.user.email if getattr(obj, 'user', None) else None
        advisor_name = obj.advisor.get_full_name() if getattr(obj, 'advisor', None) else None

        # Convertir detalles
        details = []
        details_qs = getattr(obj, 'details', None) or getattr(obj, 'invoice_details', None)
        if details_qs is not None:
            iterable = details_qs.all() if hasattr(details_qs, 'all') else details_qs
            for d in iterable:
                concept = getattr(d, 'payment_concept', None)
                details.append({
                    'id': d.id,
                    'payment_concept': getattr(concept, 'id', None),
                    'description': getattr(d, 'description', ''),
                    'quantity': getattr(d, 'quantity', 1),
                    'unit_price': getattr(d, 'unit_price', Decimal('0.00')),
                    'amount': getattr(d, 'subtotal', Decimal('0.00')),  # compatibilidad con campos esperados
                    'discount_type': getattr(d, 'discount_type', None),
                    'discount': getattr(d, 'discount', Decimal('0.00')),
                    'sub_total': getattr(d, 'subtotal', Decimal('0.00')),
                    'payment_concept_name': getattr(concept, 'name', None),
                    'payment_concept_code': getattr(concept, 'code', None),
                })

        data = {
            'id': invoice_id,
            'invoice_number': invoice_number,
            'payment_order': payment_order_id,
            'user': student_id,
            'user_name': student_name,
            'user_email': student_email,
            'advisor': advisor_id,
            'advisor_name': advisor_name,
            'currency': currency,
            'status': status,
            'total': total,
            'invoice_details': details,
        }
        return cls(**data)

    class Config:
        from_attributes = True
