from decimal import Decimal, ROUND_HALF_UP

from rest_framework import serializers

from apps.orden_pagos.models import (
    PaymentOrder,
    PaymentOrderDetails,
    PaymentOrderProgram,
)


class PaymentOrderDetailSerializer(serializers.ModelSerializer):
    """
    Serializer para los detalles de la orden de pago.
    Incluye información de relaciones (payment_type, administrative_cost) y
    calcula el `sub_total` a partir de `amount` y el descuento.
    """
    payment_type_name = serializers.CharField(
        source='payment_type.description',
        read_only=True
    )
    payment_type_code = serializers.CharField(
        source='payment_type.code',
        read_only=True
    )
    administrative_cost_name = serializers.CharField(
        source='type_administrative_cost.nombre',
        read_only=True,
        allow_null=True
    )

    # sub_total calculado en base al tipo de descuento
    sub_total = serializers.SerializerMethodField()

    class Meta:
        model = PaymentOrderDetails
        fields = [
            'id',
            'payment_type',
            'payment_type_name',
            'payment_type_code',
            'type_administrative_cost',
            'administrative_cost_name',
            'discount_type',
            'discount_amount',
            'amount',
            'sub_total',
        ]
        read_only_fields = ['sub_total']

    def get_sub_total(self, obj):
        """Calcula el subtotal aplicando el descuento.

        Asumimos que `discount_type` puede ser:
        - 'P' => porcentaje (0-100)
        - 'F' => fijo (mismo currency que `amount`)
        Si `discount_type` es None o vacío, no aplica descuento.
        """
        try:
            amount = Decimal(obj.amount or 0)
        except Exception:
            return Decimal('0.00')

        discount_type = getattr(obj, 'discount_type', None)
        discount_amount = getattr(obj, 'discount_amount', None) or Decimal('0.00')

        # normalizar a Decimal
        if not isinstance(discount_amount, Decimal):
            try:
                discount_amount = Decimal(discount_amount)
            except Exception:
                discount_amount = Decimal('0.00')

        if discount_type == 'P':
            # porcentaje
            try:
                pct = (discount_amount / Decimal('100'))
                sub = (amount * (Decimal('1') - pct)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            except Exception:
                sub = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        elif discount_type == 'F':
            # descuento fijo
            sub = (amount - discount_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            if sub < Decimal('0.00'):
                sub = Decimal('0.00')
        else:
            sub = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        return sub

    def validate(self, attrs):
        """Validaciones básicas sobre descuentos y montos."""
        amount = attrs.get('amount')
        discount_type = attrs.get('discount_type')
        discount_amount = attrs.get('discount_amount')

        # convertir a Decimal cuando es posible
        try:
            amount_dec = Decimal(amount) if amount is not None else None
        except Exception:
            raise serializers.ValidationError({'amount': 'Invalid amount value'})

        if discount_amount is not None:
            try:
                discount_dec = Decimal(discount_amount)
            except Exception:
                raise serializers.ValidationError({'discount_amount': 'Invalid discount amount'})

            if discount_type == 'P':
                if discount_dec < 0 or discount_dec > 100:
                    raise serializers.ValidationError(
                        {'discount_amount': 'Percentage discount must be between 0 and 100'})
            elif discount_type == 'F':
                if amount_dec is not None and discount_dec > amount_dec:
                    raise serializers.ValidationError({'discount_amount': 'Fixed discount cannot exceed amount'})

        return attrs


class PaymentOrderProgramSerializer(serializers.ModelSerializer):
    """
    Serializer para la información del programa educativo.
    Calcula campos de totales como solo lectura.
    """
    program_type_name = serializers.CharField(
        source='program_type.nombre',
        read_only=True
    )
    institution_name = serializers.CharField(
        source='institution.nombre',
        read_only=True
    )
    country_name = serializers.CharField(
        source='country.nombre',
        read_only=True
    )
    city_name = serializers.CharField(
        source='city.nombre',
        read_only=True
    )
    program_name = serializers.CharField(
        source='program.nombre',
        read_only=True,
        allow_null=True
    )
    intensity_name = serializers.CharField(
        source='intensity.nombre',
        read_only=True,
        allow_null=True
    )
    material_cost_type_name = serializers.CharField(
        source='material_cost_type.nombre',
        read_only=True,
        allow_null=True
    )

    tuition_subtotal = serializers.SerializerMethodField()
    total_material = serializers.SerializerMethodField()
    total_enrollment = serializers.SerializerMethodField()

    class Meta:
        model = PaymentOrderProgram
        fields = [
            'id',
            'program_type',
            'program_type_name',
            'institution',
            'institution_name',
            'country',
            'country_name',
            'city',
            'city_name',
            'program',
            'program_name',
            'intensity',
            'intensity_name',
            'another_program',
            'start_date',
            'end_date',
            'duration',
            'duration_type',
            'price_week',
            'material_cost',
            'material_cost_type',
            'material_cost_type_name',
            'tuition_subtotal',
            'total_material',
            'total_enrollment',
        ]
        read_only_fields = ['tuition_subtotal', 'total_material', 'total_enrollment']

    def _to_decimal(self, value):
        try:
            return Decimal(value)
        except Exception:
            return Decimal('0.00')

    def get_tuition_subtotal(self, obj):
        # Ejemplo: price_week * duration (si existen)
        price_week = self._to_decimal(getattr(obj, 'price_week', 0))
        duration = getattr(obj, 'duration', None)
        if duration is None:
            return Decimal('0.00')
        try:
            return (price_week * Decimal(duration)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except Exception:
            return Decimal('0.00')

    def get_total_material(self, obj):
        return self._to_decimal(getattr(obj, 'material_cost', 0)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def get_total_enrollment(self, obj):
        tuition = self.get_tuition_subtotal(obj)
        material = self.get_total_material(obj)
        try:
            return (tuition + material).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except Exception:
            return Decimal('0.00')


class PaymentOrderSerializer(serializers.ModelSerializer):
    """
    Serializer completo para órdenes de pago.
    Incluye detalles y programa anidados (solo lectura).
    Calcula `calculated_total` sumando detalles y totales del programa.
    """
    student_name = serializers.CharField(
        source='student.get_full_name',
        read_only=True
    )
    student_email = serializers.EmailField(
        source='student.email',
        read_only=True
    )
    advisor_name = serializers.CharField(
        source='advisor.get_full_name',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    payment_order_details = PaymentOrderDetailSerializer(
        many=True,
        read_only=True
    )
    payment_order_program = PaymentOrderProgramSerializer(
        read_only=True
    )
    calculated_total = serializers.SerializerMethodField()

    class Meta:
        model = PaymentOrder
        fields = [
            'id',
            'order_number',
            'student',
            'student_name',
            'student_email',
            'advisor',
            'advisor_name',
            'opportunity',
            'quotation',
            'status',
            'status_display',
            'payment_link_date',
            'total_order',
            'calculated_total',
            'payment_order_file',
            'payment_order_details',
            'payment_order_program',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'order_number',
            'calculated_total',
            'created_at',
            'updated_at',
            'payment_link_date'
        ]

    def get_calculated_total(self, obj):
        """Suma los subtotales de detalles y el total del programa (si existe)."""
        total = Decimal('0.00')

        # detalles
        try:
            details = getattr(obj, 'payment_order_details', [])
            for d in details.all() if hasattr(details, 'all') else details:
                # reutilizar la lógica del serializer de detalle
                sub = PaymentOrderDetailSerializer().get_sub_total(d)
                total += Decimal(sub)
        except Exception:
            pass

        # programa
        try:
            program = getattr(obj, 'payment_order_program', None)
            if program:
                # utilizar el serializer de programa
                program_ser = PaymentOrderProgramSerializer()
                program_total = program_ser.get_total_enrollment(program)
                total += Decimal(program_total)
        except Exception:
            pass

        return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


class PaymentOrderListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listar órdenes (mejor performance).
    """
    student_name = serializers.CharField(
        source='student.get_full_name',
        read_only=True
    )
    advisor_name = serializers.CharField(
        source='advisor.get_full_name',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    details_count = serializers.SerializerMethodField()

    class Meta:
        model = PaymentOrder
        fields = [
            'id',
            'order_number',
            'student',
            'student_name',
            'advisor',
            'advisor_name',
            'status',
            'status_display',
            'total_order',
            'details_count',
            'payment_types',
            'created_at',
        ]

    def get_details_count(self, obj):
        """Cuenta los detalles asociados"""
        # intentar aprovechar prefetched/annotated counts
        if hasattr(obj, 'payment_order_details_count'):
            return getattr(obj, 'payment_order_details_count')
        try:
            return obj.payment_order_details.count()
        except Exception:
            return 0
