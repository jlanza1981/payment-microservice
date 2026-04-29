"""
Model Serializers personalizados para Pydantic.
Estos serializers transforman instancias de modelos Django en diccionarios
con IDs en lugar de instancias, para que Pydantic pueda validarlos correctamente.
"""
from decimal import Decimal, ROUND_HALF_UP


class PaymentOrderDetailModelSerializer:

    @staticmethod
    def serialize(obj) -> dict:
        """Serializa PaymentOrderDetails a un diccionario con IDs"""
        payment_concept = getattr(obj, 'payment_concept', None)
        payment_concept_id = payment_concept.id if hasattr(payment_concept, 'id') else payment_concept

        type_admin = getattr(obj, 'type_administrative_cost', None)
        type_admin_id = type_admin.id if hasattr(type_admin, 'id') else type_admin

        sub_total = PaymentOrderDetailModelSerializer.calculate_sub_total(obj)

        data = {
            'id': obj.id,
            'payment_concept': payment_concept_id,
            'payment_concept_name': payment_concept.name if payment_concept else None,
            'payment_concept_code': payment_concept.code if payment_concept else None,
            'type_administrative_cost': type_admin_id,
            'administrative_cost_name': type_admin.nombre if type_admin else None,
            'discount_type': getattr(obj, 'discount_type', None),
            'discount_amount': getattr(obj, 'discount_amount', Decimal('0.00')),
            'amount': getattr(obj, 'amount', Decimal('0.00')),
            'quantity': getattr(obj, 'quantity', 1),
            'sub_total': sub_total,
        }

        return data

    @staticmethod
    def calculate_sub_total(obj) -> Decimal:
        """Calcula el subtotal aplicando el descuento"""
        try:
            amount = Decimal(obj.amount or 0)
        except Exception:
            return Decimal('0.00')

        discount_type = getattr(obj, 'discount_type', None)
        discount_amount = getattr(obj, 'discount_amount', None) or Decimal('0.00')

        if not isinstance(discount_amount, Decimal):
            try:
                discount_amount = Decimal(discount_amount)
            except Exception:
                discount_amount = Decimal('0.00')

        # Normalizar tipo de descuento
        dt = (discount_type or '').lower()
        if discount_type in ('P', 'F'):
            dt = 'percentage' if discount_type == 'P' else 'fixed'

        if dt == 'percentage':
            try:
                pct = (discount_amount / Decimal('100'))
                sub = (amount * (Decimal('1') - pct)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            except Exception:
                sub = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        elif dt == 'fixed':
            sub = (amount - discount_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            if sub < Decimal('0.00'):
                sub = Decimal('0.00')
        else:
            sub = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        return sub


class PaymentOrderProgramModelSerializer:

    @staticmethod
    def serialize(obj) -> dict:
        """Serializa PaymentOrderProgram a un diccionario con IDs"""
        program_type = getattr(obj, 'program_type', None)
        institution = getattr(obj, 'institution', None)
        country = getattr(obj, 'country', None)
        city = getattr(obj, 'city', None)
        program = getattr(obj, 'program', None)
        intensity = getattr(obj, 'intensity', None)
        material_cost_type = getattr(obj, 'material_cost_type', None)

        tuition_subtotal = PaymentOrderProgramModelSerializer.calculate_tuition_subtotal(obj)
        total_material = PaymentOrderProgramModelSerializer.calculate_total_material(obj)
        total_enrollment = PaymentOrderProgramModelSerializer.calculate_total_enrollment(obj)

        data = {
            'id': obj.id,
            'program_type': program_type.id if program_type else None,
            'program_type_name': program_type.nombre if program_type else None,
            'institution': institution.id if institution else None,
            'institution_name': institution.nombre if institution else None,
            'country': country.id if country else None,
            'country_name': country.pais if country else None,
            'city': city.id if city else None,
            'city_name': city.ciudad if city else None,
            'program': program.id if program else None,
            'program_name': program.nombre if program else None,
            'intensity': intensity.id if intensity else None,
            'intensity_name': intensity.nombre if intensity else None,
            'another_program': getattr(obj, 'another_program', None),
            'start_date': getattr(obj, 'start_date', None),
            'end_date': getattr(obj, 'end_date', None),
            'duration': getattr(obj, 'duration', 0),
            'duration_type': getattr(obj, 'duration_type', ''),
            'price_week': getattr(obj, 'price_week', Decimal('0.00')),
            'material_cost': getattr(obj, 'material_cost', Decimal('0.00')),
            'material_cost_type': material_cost_type.id if material_cost_type else None,
            'material_cost_type_name': material_cost_type.nombre if material_cost_type else None,
            'tuition_subtotal': tuition_subtotal,
            'total_material': total_material,
            'total_enrollment': total_enrollment,
        }

        return data

    @staticmethod
    def _to_decimal(value) -> Decimal:
        """Convierte un valor a Decimal de forma segura"""
        try:
            return Decimal(value)
        except Exception:
            return Decimal('0.00')

    @staticmethod
    def calculate_tuition_subtotal(obj) -> Decimal:
        price_week = PaymentOrderProgramModelSerializer._to_decimal(getattr(obj, 'price_week', 0))
        duration = getattr(obj, 'duration', None)
        if duration is None:
            return Decimal('0.00')
        try:
            return (price_week * Decimal(duration)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except Exception:
            return Decimal('0.00')

    @staticmethod
    def calculate_total_material(obj) -> Decimal:
        return PaymentOrderProgramModelSerializer._to_decimal(getattr(obj, 'material_cost', 0)).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_total_enrollment(obj) -> Decimal:
        tuition = PaymentOrderProgramModelSerializer.calculate_tuition_subtotal(obj)
        material = PaymentOrderProgramModelSerializer.calculate_total_material(obj)
        try:
            return (tuition + material).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except Exception:
            return Decimal('0.00')


class PaymentOrderListModelSerializer:
    """
    Serializer para la vista de lista de órdenes.
    Devuelve solo los campos necesarios por PaymentOrderListSchema
    y calcula el total de forma consistente (sin doble conteo).
    """

    @staticmethod
    def calculate_total_order(obj) -> Decimal:
        total = Decimal('0.00')
        try:
            details = getattr(obj, 'payment_order_details', [])
            iterable = details.all() if hasattr(details, 'all') else details
            for d in iterable:
                sub = getattr(d, 'sub_total', None)
                if sub is None:
                    sub = PaymentOrderDetailModelSerializer.calculate_sub_total(d)
                total += Decimal(sub)
        except Exception:
            return Decimal('0.00')
        return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @staticmethod
    def serialize(obj) -> dict:
        # Determinar si es un dict o un objeto modelo
        is_dict = isinstance(obj, dict)
        
        # Función helper para obtener valores de forma segura
        def get_value(key, default=None):
            if is_dict:
                return obj.get(key, default)
            return getattr(obj, key, default)
        
        # Extraer valores básicos
        id = get_value('id')
        order_number = get_value('order_number')
        status = get_value('status')
        
        # Para objetos modelo, obtener IDs de relaciones ForeignKey
        if is_dict:
            student = obj.get('student') or obj.get('student_id')
            advisor = obj.get('advisor') or obj.get('advisor_id')
        else:
            student = getattr(obj, 'student_id', None)
            advisor = getattr(obj, 'advisor_id', None)
        
        # Nombres (pueden venir pre-calculados o necesitar extracción)
        student_name = get_value('student_name')
        advisor_name = get_value('advisor_name')
        status_display = get_value('status_display')
        
        # Si los nombres no están pre-calculados y tenemos el objeto completo
        if not is_dict:
            if not student_name and hasattr(obj, 'student') and obj.student:
                student_name = obj.student.get_full_name() if hasattr(obj.student, 'get_full_name') else str(obj.student)
            if not advisor_name and hasattr(obj, 'advisor') and obj.advisor:
                advisor_name = obj.advisor.get_full_name() if hasattr(obj.advisor, 'get_full_name') else str(obj.advisor)
            if not status_display and hasattr(obj, 'get_status_display'):
                status_display = obj.get_status_display()
        
        # Total de la orden
        total_order = get_value('total_order')
        if total_order is None:
            total_order = PaymentOrderListModelSerializer.calculate_total_order(obj)
        
        # Otros campos
        details_count = get_value('details_count', 0)
        payment_types = get_value('payment_types')
        credit_amount = get_value('credit_amount', 0)
        
        data = {
            'id': id,
            'order_number': order_number,
            'student': student,
            'advisor': advisor,
            'student_name': student_name,
            'advisor_name': advisor_name,
            'status': status,
            'status_display': status_display,
            'total_order': total_order,
            'details_count': details_count,
            'payment_types': payment_types.name if payment_types else None,
            'credit_amount': credit_amount if credit_amount else 0,
        }
        
        return data
