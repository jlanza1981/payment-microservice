from decimal import Decimal

from rest_framework import serializers


class PaymentOrderDetailInputSerializer(serializers.Serializer):
    """
    Serializer para validar entrada de detalles de orden.
    """
    payment_type = serializers.IntegerField(required=True)
    type_administrative_cost = serializers.IntegerField(required=False, allow_null=True)
    discount_type = serializers.ChoiceField(
        choices=['percentage', 'fixed'],
        required=False,
        allow_null=True,
        allow_blank=True
    )
    discount_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        default=Decimal('0.00')
    )
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True
    )

    def validate(self, attrs):
        """Validar que si hay descuento, tenga tipo y monto"""
        discount_type = attrs.get('discount_type')
        discount_amount = attrs.get('discount_amount', Decimal('0.00'))

        if discount_amount > 0 and not discount_type:
            raise serializers.ValidationError({
                'discount_type': 'Debe especificar el tipo de descuento si hay monto'
            })

        if discount_type and discount_amount <= 0:
            raise serializers.ValidationError({
                'discount_amount': 'El monto de descuento debe ser mayor a 0'
            })

        # Validar porcentaje no mayor a 100
        if discount_type == 'percentage' and discount_amount > 100:
            raise serializers.ValidationError({
                'discount_amount': 'El porcentaje de descuento no puede ser mayor a 100'
            })

        return attrs


class PaymentOrderProgramInputSerializer(serializers.Serializer):
    """
    Serializer para validar entrada de datos del programa.
    """
    program_type = serializers.IntegerField(required=True)
    institution = serializers.IntegerField(required=True)
    country = serializers.IntegerField(required=True)
    city = serializers.IntegerField(required=True)
    program = serializers.IntegerField(required=False, allow_null=True)
    intensity = serializers.IntegerField(required=False, allow_null=True)
    another_program = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=True,
        allow_blank=True
    )
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    duration = serializers.IntegerField(required=True, min_value=1)
    duration_type = serializers.ChoiceField(
        choices=['A', 'S', 'w'],
        required=True
    )
    price_week = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        min_value=Decimal('0.00')
    )
    material_cost = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        default=Decimal('0.00'),
        min_value=Decimal('0.00')
    )
    material_cost_type = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        """Validar que tenga program_id o another_program"""
        program_id = attrs.get('program')
        another_program = attrs.get('another_program')

        if not program_id and not another_program:
            raise serializers.ValidationError({
                'program': 'Debe especificar un programa o ingresar un nombre personalizado'
            })

        # Validar fechas
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')

        if end_date and start_date and end_date < start_date:
            raise serializers.ValidationError({
                'end_date': 'La fecha de fin no puede ser anterior a la fecha de inicio'
            })

        return attrs


class CreatePaymentOrderSerializer(serializers.Serializer):
    """
    Serializer para crear una nueva orden de pago.
    Valida todos los datos de entrada.

    Nota: total_order NO se recibe del frontend, se calcula automáticamente
    en el backend sumando los subtotales de payment_details.

    Campos obligatorios:
    - student_id, advisor_id: Identificadores requeridos
    - payment_details: Mínimo 1 concepto de pago
    - program_data: Información del programa académico (obligatorio)
    """
    student = serializers.IntegerField(required=True)
    advisor = serializers.IntegerField(required=True)
    opportunity = serializers.IntegerField(required=False, allow_null=True)
    quotation = serializers.IntegerField(required=False, allow_null=True)
    payment_details = PaymentOrderDetailInputSerializer(many=True, required=True)
    program_data = PaymentOrderProgramInputSerializer(required=False)

    def validate_payment_details(self, value):
        """Validar que haya al menos un detalle"""
        if not value or len(value) == 0:
            raise serializers.ValidationError('Debe incluir al menos un concepto de pago')
        return value


class UpdatePaymentOrderSerializer(serializers.Serializer):
    payment_details = PaymentOrderDetailInputSerializer(many=True, required=False)
    program_data = PaymentOrderProgramInputSerializer(required=False, allow_null=True)


class ChangeOrderStatusSerializer(serializers.Serializer):
    """
    Serializer para cambiar el estado de una orden.
    """
    new_status = serializers.ChoiceField(
        choices=['PENDING', 'PAID', 'VERIFIED', 'CANCELLED'],
        required=True
    )


class MarkOrderAsPaidSerializer(serializers.Serializer):
    """
    Serializer para marcar una orden como pagada.
    Todos los campos son opcionales.
    """
    payment_date = serializers.DateField(required=False, allow_null=True)
    payment_reference = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class CancelOrderSerializer(serializers.Serializer):
    """
    Serializer para anular una orden de pago.
    """
    cancellation_reason = serializers.CharField(required=True, min_length=10)

    def validate_cancellation_reason(self, value):
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError(
                'La razón de cancelación debe tener al menos 10 caracteres'
            )
        return value.strip()


class VerifyOrderSerializer(serializers.Serializer):
    """
    Serializer para verificar una orden por tesorería.
    """
    verified_by = serializers.IntegerField(required=True)
    verification_notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
