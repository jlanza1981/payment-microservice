"""
Model Serializers personalizados para Pydantic.
Estos serializers transforman instancias de modelos Django en diccionarios
con IDs en lugar de instancias, para que Pydantic pueda validarlos correctamente.
"""
from decimal import Decimal, ROUND_HALF_UP


class InvoiceDetailModelSerializer:
    """
    Serializer personalizado para PaymentOrderDetails.
    Convierte instancias de ForeignKey a IDs y calcula campos derivados.
    """

    @staticmethod
    def serialize(obj) -> dict:
        """Serializa PaymentOrderDetails a un diccionario con IDs"""
        # Obtener payment_concept (puede ser instancia o ID)
        payment_concept = getattr(obj, 'payment_concept', None)
        payment_concept_id = payment_concept.id if hasattr(payment_concept, 'id') else payment_concept

        # Calcular sub_total
        sub_total = InvoiceDetailModelSerializer.calculate_sub_total(obj)

        # Construir el diccionario para serialización
        data = {
            'id': obj.id,
            'payment_concept': payment_concept_id,
            'payment_concept_name': payment_concept.name if payment_concept else None,
            'payment_concept_code': payment_concept.code if payment_concept else None,
            'discount_type': getattr(obj, 'discount_type', None),
            'discount': getattr(obj, 'discount', Decimal('0.00')),
            'total': sub_total,
        }

        return data

    @staticmethod
    def calculate_sub_total(obj) -> Decimal:
        """Calcula el subtotal aplicando el descuento"""
        try:
            amount = Decimal(obj.total or 0)
        except Exception:
            return Decimal('0.00')

        discount_type = getattr(obj, 'discount_type', None)
        discount_amount = getattr(obj, 'discount', None) or Decimal('0.00')

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
