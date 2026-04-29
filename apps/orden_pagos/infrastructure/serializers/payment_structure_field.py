from rest_framework import serializers

from apps.orden_pagos.models import PaymentStructureFields


class PaymentStructureFieldSerializer(serializers.ModelSerializer):
    payment_type = serializers.SerializerMethodField()

    class Meta:
        model = PaymentStructureFields
        fields = [
            "id",
            "name",
            "label",
            "field_type",
            "choice",
            "required",
            "order",
            "default_value",
            "active",
            "payment_type",
        ]

    @staticmethod
    def get_payment_type(obj):
        return {
            "id": obj.payment_type.id,
            "name": obj.payment_type.name,
            "code": getattr(obj.payment_type, "code", None),
        }
