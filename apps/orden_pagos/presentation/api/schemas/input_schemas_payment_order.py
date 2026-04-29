"""
Schemas de entrada (Input) usando Pydantic para la API de órdenes de pago.
Migración de DRF Serializers a Pydantic Schemas.
"""
from datetime import date
from decimal import Decimal
from typing import Optional, Literal, List

from ninja import Schema
from pydantic import Field, field_validator, model_validator


class PaymentOrderDetailInputSchema(Schema):
    """
    Schema para validar entrada de detalles de orden.
    Equivalente a PaymentOrderDetailInputSerializer.
    """
    payment_concept: int = Field(None, description="ID del concepto de pago")
    type_administrative_cost: Optional[int] = Field(None, description="ID del tipo de costo administrativo")
    discount_type: Optional[Literal['percentage', 'fixed']] = Field(None, description="Tipo de descuento")
    discount_amount: Optional[Decimal] = Field(default=Decimal('0.00'), description="Monto del descuento")
    amount: Decimal = Field(..., description="Monto del concepto de pago")
    quantity: int = Field(default=1, description="Cantidad/Duración del concepto")

    @model_validator(mode='after')
    def normalize_and_validate(self):
        """Normaliza alias comunes a payment_concept y valida descuentos."""
        if self.payment_concept is None:
            aliases = (
                getattr(self, 'payment_concept', None),
            )
            for candidate in aliases:
                if isinstance(candidate, int):
                    self.payment_concept = candidate
                    break

        if self.payment_concept is None:
            raise ValueError(
                'El campo "payment_concept" (o alias payment_concept/payment_type_id) es requerido en cada item de payment_details')

        # Validar descuento
        if self.discount_amount > 0 and not self.discount_type:
            raise ValueError('Debe especificar el tipo de descuento si hay monto')

        if self.discount_type and self.discount_amount <= 0:
            raise ValueError('El monto de descuento debe ser mayor a 0')

        if self.discount_type == 'percentage' and self.discount_amount > 100:
            raise ValueError('El porcentaje de descuento no puede ser mayor a 100')

        return self


class PaymentOrderProgramInputSchema(Schema):
    """
    Schema para validar entrada de datos del programa.
    Equivalente a PaymentOrderProgramInputSerializer.
    """
    program_type: int = Field(..., description="ID del tipo de programa")
    institution: int = Field(..., description="ID de la institución")
    country: str = Field(..., description="ID del país")
    city: int = Field(..., description="ID de la ciudad")
    program: Optional[int] = Field(None, description="ID del programa")
    intensity: Optional[int] = Field(None, description="ID de la intensidad")
    another_program: Optional[str] = Field(None, max_length=255, description="Nombre personalizado del programa")
    start_date: date = Field(..., description="Fecha de inicio")
    end_date: Optional[date] = Field(None, description="Fecha de fin")
    duration: int = Field(..., ge=1, description="Duración del programa")
    duration_type: Literal['A', 'S', 'w'] = Field(..., description="Tipo de duración (A=años, S=semestres, w=semanas)")
    price_week: Optional[Decimal] = Field(None, ge=Decimal('0.00'), description="Precio por semana (solo para programas de idiomas)")
    material_cost: Decimal = Field(default=Decimal('0.00'), ge=Decimal('0.00'), description="Costo de materiales")
    material_cost_type: Optional[int] = Field(None, description="ID del tipo de costo de material")

    @model_validator(mode='after')
    def validate_program_and_dates(self):
        """Validar que tenga program_id o another_program y validar fechas"""
        if not self.program and not self.another_program:
            raise ValueError('Debe especificar un programa o ingresar un nombre personalizado')

        # Validar fechas
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValueError('La fecha de fin no puede ser anterior a la fecha de inicio')

        return self


class CreatePaymentOrderSchema(Schema):
    """
    Schema para crear una nueva orden de pago.
    Equivalente a CreatePaymentOrderSerializer.

    Nota: total_order NO se recibe del frontend, se calcula automáticamente
    en el backend sumando los subtotales de payment_details.
    """
    student: int = Field(..., description="ID del estudiante")
    advisor: int = Field(..., description="ID del asesor")
    currency: str = Field(..., description="Moneda de la orden de pago")
    opportunity: int = Field(..., description="ID de la oportunidad CRM")
    quotation: Optional[int] = Field(None, description="ID de la cotización")
    payment_details: List[PaymentOrderDetailInputSchema] = Field(..., min_length=1, description="Detalles de pago")
    program_data: Optional[PaymentOrderProgramInputSchema] = Field(None, description="Datos del programa académico")
    send_payment_link: bool = Field(False, description="Indica si se debe enviar el enlace de pago al estudiante")
    status: Optional[str] = Field(None, description="Estatus para la orden de pago en caso de exoneración")
    allows_partial_payment: bool = Field(True, description="Indica si la orden permite pagos parciales")
    minimum_payment_amount: Optional[Decimal] = Field(None, ge=Decimal('50.00'), description="Monto mínimo de abono permitido")
    suggested_payment_amount: Optional[Decimal] = Field(None, ge=Decimal('0.00'), description="Monto del abono inicial sugerido")

    @model_validator(mode='after')
    def validate_partial_payment_fields(self):
        """Validar campos de pagos parciales"""
        if self.allows_partial_payment:
            # Validar minimum_payment_amount si está presente
            if self.minimum_payment_amount is not None and self.minimum_payment_amount <= 0:
                raise ValueError('El monto mínimo de abono debe ser mayor a 0')

            # Validar initial_payment_amount si está presente
            if self.suggested_payment_amount is not None:
                if self.suggested_payment_amount <= 0:
                    raise ValueError('El monto del abono inicial debe ser mayor a 0')

                # Si hay monto mínimo, el inicial debe ser >= al mínimo
                if self.minimum_payment_amount and self.suggested_payment_amount < self.minimum_payment_amount:
                    raise ValueError(f'El monto inicial debe ser mayor o igual al monto mínimo ({self.minimum_payment_amount})')

        return self

    @field_validator('payment_details')
    @classmethod
    def validate_payment_details(cls, v):
        """Validar que haya al menos un detalle"""
        if not v or len(v) == 0:
            raise ValueError('Debe incluir al menos un concepto de pago')
        return v


class UpdatePaymentOrderSchema(Schema):
    """
    Schema para actualizar una orden de pago.
    Equivalente a UpdatePaymentOrderSerializer.
    """
    payment_details: Optional[List[PaymentOrderDetailInputSchema]] = Field(None, description="Detalles de pago")
    program_data: Optional[PaymentOrderProgramInputSchema] = Field(None, description="Datos del programa académico")


class ChangeOrderStatusSchema(Schema):
    """
    Schema para cambiar el estado de una orden.
    Equivalente a ChangeOrderStatusSerializer.
    """
    new_status: Literal['PENDING', 'PAID', 'VERIFIED', 'CANCELLED'] = Field(..., description="Nuevo estado de la orden")


class MarkOrderAsPaidSchema(Schema):
    """
    Schema para marcar una orden como pagada.
    Equivalente a MarkOrderAsPaidSerializer.
    Todos los campos son opcionales.
    """
    payment_date: Optional[date] = Field(None, description="Fecha del pago")
    payment_reference: Optional[str] = Field(None, max_length=100, description="Referencia del pago")
    notes: Optional[str] = Field(None, description="Notas adicionales")


class CancelOrderSchema(Schema):
    """
    Schema para anular una orden de pago.
    Equivalente a CancelOrderSerializer.
    """
    cancellation_reason: str = Field(..., min_length=10, description="Razón de la cancelación")

    @field_validator('cancellation_reason')
    @classmethod
    def validate_cancellation_reason(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('La razón de cancelación debe tener al menos 10 caracteres')
        return v.strip()


class VerifyOrderSchema(Schema):
    """
    Schema para verificar una orden por tesorería.
    Equivalente a VerifyOrderSerializer.
    """
    verified_by: int = Field(..., description="ID del usuario que verifica")
    verification_notes: Optional[str] = Field(None, description="Notas de verificación")


class MinimalUpdatePaymentOrderSchema(Schema):
    """
    Schema mínimo para actualizar una orden de pago.
    Usa order_id de la ruta y permite actualizar opcionalmente:
    - payment_details: lista de dicts (reemplaza todos los detalles)
    - program_data: dict (reemplaza datos del programa)

    La validación y normalización interna de estos dicts se delega al caso de uso/repositorio.
    """
    send_payment_link: Optional[bool] = False
    payment_details: Optional[List[dict]] = None
    program_data: Optional[dict] = None
    suggested_payment_amount: Optional[Decimal] = None

    @model_validator(mode='after')
    def validate_at_least_one(self):
        if not self.payment_details and not self.program_data:
            raise ValueError('Debe enviar al menos uno de: payment_details o program_data')
        return self