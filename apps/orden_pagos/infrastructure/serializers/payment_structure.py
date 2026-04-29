from rest_framework import serializers

from apps.orden_pagos.infrastructure.serializers.payment_structure_field import PaymentStructureFieldSerializer
from apps.orden_pagos.models import PaymentStructure


class PaymentStructureSerializer(serializers.ModelSerializer):
    payment_type = serializers.SerializerMethodField()
    fields = serializers.SerializerMethodField()

    class Meta:
        model = PaymentStructure
        fields = [
            "id",
            "payment_type",
            "has_discount",
            "notes",
            "is_active",
            "fields",
        ]

    @staticmethod
    def get_payment_type(obj):
        return {
            "id": obj.payment_type.id,
            "name": obj.payment_type.name,
            "code": getattr(obj.payment_type, "code", None)
        }

    @staticmethod
    def get_structure_fields(obj):
        qs = obj.structure_section_payment_structure.all().order_by("order")
        return PaymentStructureFieldSerializer(qs, many=True).data
