"""
Schemas de salida (Output) usando Pydantic para la API de órdenes de pago.
Migración de DRF Serializers a Pydantic Schemas.
"""
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List

from ninja import Schema

from .model_serializers_payment_order import (
    PaymentOrderDetailModelSerializer,
    PaymentOrderProgramModelSerializer,
    PaymentOrderListModelSerializer,
)


class PaymentOrderDetailSchema(Schema):
    """
    Schema para los detalles de la orden de pago.
    Equivalente a PaymentOrderDetailSerializer.
    """
    id: int
    payment_concept: int
    payment_concept_name: Optional[str] = None
    payment_concept_code: Optional[str] = None
    type_administrative_cost: Optional[int] = None
    administrative_cost_name: Optional[str] = None
    discount_type: Optional[str] = None
    discount_amount: Optional[Decimal] = Decimal('0.00')
    amount: Decimal
    quantity: int
    sub_total: Optional[Decimal]

    @classmethod
    def from_orm(cls, obj):
        """Convierte un modelo Django a schema usando el serializer"""
        data = PaymentOrderDetailModelSerializer.serialize(obj)
        return cls(**data)

    class Config:
        from_attributes = True


class PaymentOrderProgramSchema(Schema):
    """
    Schema para la información del programa educativo.
    Equivalente a PaymentOrderProgramSerializer.
    """
    id: int
    program_type: int
    program_type_name: Optional[str] = None
    institution: int
    institution_name: Optional[str] = None
    country: str
    country_name: Optional[str] = None
    city: int
    city_name: Optional[str] = None
    program: Optional[int] = None
    program_name: Optional[str] = None
    intensity: Optional[int] = None
    intensity_name: Optional[str] = None
    another_program: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    duration: int
    duration_type: str
    price_week: Optional[Decimal] = None  # Opcional, solo para programas de idiomas
    material_cost: Optional[Decimal] = Decimal('0.00')
    material_cost_type: Optional[int] = None
    material_cost_type_name: Optional[str] = None
    tuition_subtotal: Optional[Decimal]
    total_material: Optional[Decimal]
    total_enrollment: Optional[Decimal]

    @classmethod
    def from_orm(cls, obj):
        """Convierte un modelo Django a schema usando el serializer"""
        data = PaymentOrderProgramModelSerializer.serialize(obj)
        return cls(**data)

    class Config:
        from_attributes = True


class PaymentOrderSchema(Schema):
    """
    Schema completo para órdenes de pago.
    Equivalente a PaymentOrderSerializer.
    Incluye detalles y programa anidados.
    """
    id: int
    order_number: str
    student: int
    student_name: Optional[str] = None
    student_email: Optional[str] = None
    advisor: int
    advisor_name: Optional[str] = None
    opportunity: Optional[int] = None
    quotation: Optional[int] = None
    currency: str
    status: str
    status_display: Optional[str] = None
    payment_link_date: Optional[datetime] = None
    total_order: Optional[Decimal]
    calculated_total: Optional[Decimal]
    payment_order_file: Optional[str] = None
    suggested_payment_amount: Optional[Decimal] = None
    # Campos calculados para pagos parciales
    total_paid: Optional[Decimal] = None
    balance_due: Optional[Decimal] = None
    is_partially_paid: bool = False
    payment_order_details: List[PaymentOrderDetailSchema] = []
    payment_order_program: Optional[PaymentOrderProgramSchema] = None

    @classmethod
    def from_orm(cls, obj):
        """Convierte un modelo Django a schema, manejando relaciones anidadas"""
        # ⚠️ IMPORTANTE: Extraer TODOS los IDs y valores primitivos PRIMERO
        order_id = obj.id
        order_number = getattr(obj, 'order_number', None)
        student_id = getattr(obj, 'student_id', None)
        advisor_id = getattr(obj, 'advisor_id', None)
        opportunity_id = getattr(obj, 'opportunity_id', None)
        quotation_id = getattr(obj, 'quotation_id', None)
        currency = getattr(obj, 'currency', 'USD')
        status = getattr(obj, 'status', 'PENDING')
        status_display = obj.get_status_display() if hasattr(obj, 'get_status_display') else None
        payment_link_date = getattr(obj, 'payment_link_date', None)
        total_order = getattr(obj, 'total_order', None)
        payment_order_file = getattr(obj, 'payment_order_file', None)

        # Extraer nombres (pueden requerir acceso a relaciones)
        student_name = obj.student.get_full_name() if getattr(obj, 'student', None) else None
        student_email = obj.student.email if getattr(obj, 'student', None) else None
        advisor_name = obj.advisor.get_full_name() if getattr(obj, 'advisor', None) else None

        # Convertir detalles usando from_orm (después de extraer primitivos)
        details = []
        if hasattr(obj, 'payment_order_details'):
            details_qs = obj.payment_order_details.all() if hasattr(obj.payment_order_details,
                                                                    'all') else obj.payment_order_details
            details = [PaymentOrderDetailSchema.from_orm(d) for d in details_qs]

        # Convertir programa usando from_orm
        program = None
        if hasattr(obj, 'payment_order_program') and obj.payment_order_program:
            program = PaymentOrderProgramSchema.from_orm(obj.payment_order_program)

        # Calcular total
        calculated_total = cls.resolve_calculated_total(obj)

        # Campos calculados para pagos parciales
        total_paid = obj.get_total_paid() if hasattr(obj, 'get_total_paid') else None
        balance_due = obj.get_balance_due() if hasattr(obj, 'get_balance_due') else None
        is_partially_paid = obj.is_partially_paid() if hasattr(obj, 'is_partially_paid') else False

        # Construir y loggear payload para Pydantic
        data = {
            'id': order_id,
            'order_number': order_number,
            'student': student_id,
            'student_name': student_name,
            'student_email': student_email,
            'advisor': advisor_id,
            'advisor_name': advisor_name,
            'opportunity': opportunity_id,
            'currency': currency,
            'quotation': quotation_id,
            'status': status,
            'status_display': status_display,
            'payment_link_date': payment_link_date,
            'total_order': total_order,
            'calculated_total': calculated_total,
            'payment_order_file': payment_order_file,
            'suggested_payment_amount': getattr(obj, 'suggested_payment_amount', None),
            'total_paid': total_paid,
            'balance_due': balance_due,
            'is_partially_paid': is_partially_paid,
            'payment_order_details': details,
            'payment_order_program': program,
        }
        # print(f"🧪 PaymentOrderSchema.from_orm payload -> student: {data['student']}, advisor: {data['advisor']}")

        return cls(**data)

    @staticmethod
    def resolve_calculated_total(obj):
        """Obtiene el total calculado de la orden sin duplicar montos del programa.
        Preferir el property del modelo (suma de sub_total de los detalles).
        """
        try:
            # Si el modelo expone el property, úsalo directamente
            total = getattr(obj, 'total_order', None)
            if total is not None:
                return Decimal(total).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except Exception:
            pass

        # Fallback: sumar únicamente los subtotales de los detalles
        total = Decimal('0.00')
        try:
            details = getattr(obj, 'payment_order_details', [])
            for d in details.all() if hasattr(details, 'all') else details:
                sub = getattr(d, 'sub_total', None)
                if sub is None:
                    # Si no hay sub_total precalculado, calcularlo via serializer helper
                    sub = PaymentOrderDetailModelSerializer.calculate_sub_total(d)
                total += Decimal(sub)
        except Exception:
            pass

        return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    class Config:
        from_attributes = True


class PaymentOrderListSchema(Schema):
    """
    Schema simplificado para listar órdenes (mejor performance).
    Equivalente a PaymentOrderListSerializer.
    """
    id: int
    order_number: str
    student: int
    advisor: int
    status: str
    status_display: Optional[str] = None
    student_name: Optional[str] = None
    advisor_name: Optional[str] = None
    total_order: Decimal
    details_count: int = 0
    credit_amount: Optional[Decimal] = None
    payment_types: Optional[str] = None

    @classmethod
    def from_orm(cls, obj):
        data = PaymentOrderListModelSerializer.serialize(obj)
        instance = cls(**data)
        return instance

    class Config:
        from_attributes = True


class PaginatedPaymentOrderListSchema(Schema):
    """
    Schema para paginación de listas de órdenes de pago.
    """
    count: int
    next: Optional[str] = None
    previous: Optional[str] = None
    results: List[PaymentOrderListSchema]

    class Config:
        from_attributes = True


# Payment Structure
class PaymentStructureFieldSchema(Schema):
    """
    Schema para un campo de estructura de pago.
    """
    id: int
    name: str
    label: str
    field_type: str
    choices: Optional[dict] = None
    required: bool
    readonly: bool
    order: int
    default_value: Optional[str] = None
    active: bool

    class Config:
        from_attributes = True


class PaymentConceptBasicSchema(Schema):
    """
    Schema básico para concepto de pago (sin timestamps).
    """
    id: int
    code: str
    name: str

    class Config:
        from_attributes = True


class PaymentStructureDetailSchema(Schema):
    """
    Schema detallado para la estructura de pago con sus campos.
    """
    id: int
    payment_type: PaymentConceptBasicSchema
    has_discount: bool
    notes: str
    is_active: bool
    fields: List[PaymentStructureFieldSchema] = []

    @classmethod
    def from_orm(cls, obj):
        """Convierte un modelo PaymentStructure a schema"""
        # Extraer datos del payment_type
        payment_type_data = {
            'id': obj.payment_type.id,
            'code': obj.payment_type.code,
            'name': obj.payment_type.name,
        }

        # Extraer campos (fields)
        fields_data = []
        structure_fields = obj.structure_section_payment_structure.all()
        for field in structure_fields:
            fields_data.append({
                'id': field.id,
                'name': field.name,
                'label': field.label,
                'field_type': field.field_type,
                'choices': field.choices,
                'required': field.required,
                'readonly': field.readonly,
                'order': field.order,
                'default_value': field.default_value,
                'active': field.active,
            })

        data = {
            'id': obj.id,
            'payment_type': payment_type_data,
            'has_discount': obj.has_discount,
            'notes': obj.notes,
            'is_active': obj.is_active,
            'fields': fields_data,
        }

        return cls(**data)

    class Config:
        from_attributes = True


class PaymentStructureSchema(Schema):
    """
    Schema para la estructura de pago (usado en órdenes de pago).
    """
    order_details: List[PaymentOrderDetailSchema] = []
    program_details: Optional[PaymentOrderProgramSchema] = None
    total: Decimal

    class Config:
        from_attributes = True


class TokenValidationSchema(Schema):
    """
    Schema para respuesta de validación de token.
    """
    valid: bool
    payment_order: Optional[PaymentOrderSchema] = None
    message: Optional[str] = None

    class Config:
        from_attributes = True


# Payment Concept
class PaymentConceptSchema(Schema):
    """
    Schema para concepto de pago individual.
    """
    id: int
    code: str
    name: str
    category_id: int  # Cambiado de 'category' a 'category_id' para obtener el ID de la FK
    is_active: bool
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentCategorySchema(Schema):
    """
    Schema para categoría de pago.
    """
    id: int
    code: str
    name: str
    requires_program: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentCategoryWithConceptsSchema(Schema):
    """
    Schema para categoría con sus conceptos de pago anidados.
    """
    id: int
    code: str
    name: str
    requires_program: bool
    concepts: List[PaymentConceptSchema] = []

    class Config:
        from_attributes = True


class PaymentConceptDetailSchema(Schema):
    """
    Schema detallado para concepto de pago (todos los campos).
    """
    id: int
    code: str
    name: str
    category_id: int  # Cambiado de 'category' a 'category_id' para obtener el ID de la FK
    category_code: Optional[str] = None
    category_name: Optional[str] = None
    is_active: bool
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentOrderResponseSchema(Schema):
    """
    Schema para la respuesta de creación/actualización de una orden de pago.
    Incluye la orden completa más metadata adicional (mensaje, task_id, etc).
    """
    payment_order: PaymentOrderSchema
    message: str
    send_link_triggered: Optional[bool] = False
    task_id: Optional[str] = None

    class Config:
        from_attributes = True

