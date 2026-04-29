"""
Señales para el sistema de pagos y facturación.

NOTA: Toda la lógica de pagos se maneja en los casos de uso (webhooks).
- Creación de recibos: CreatePaymentReceiptUseCase
- Actualización de balance: Payment.save() (modelo)
- Creación de InvoiceCreditDetail: paypal_payment_capture_process

Este archivo se mantiene para futuras señales si son necesarias.
"""
import logging

logger = logging.getLogger(__name__)

# No hay señales activas actualmente.
# Toda la lógica está en casos de uso y modelos, siguiendo DDD.

