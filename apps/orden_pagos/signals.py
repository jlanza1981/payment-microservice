from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.orden_pagos.models import PaymentOrderDetails


@receiver(post_save, sender=PaymentOrderDetails)
def update_order_total_on_save(sender, instance, **kwargs):
    """Actualiza el total de la orden cuando se guarda/actualiza un detalle"""
    order = instance.payment_order
    order.total_order = order.calculated_total
    order.save(update_fields=['total_order'])


@receiver(post_delete, sender=PaymentOrderDetails)
def update_order_total_on_delete(sender, instance, **kwargs):
    """Actualiza el total de la orden cuando se elimina un detalle"""
    order = instance.payment_order
    order.total_order = order.calculated_total
    order.save(update_fields=['total_order'])
