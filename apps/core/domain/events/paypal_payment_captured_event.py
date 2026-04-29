from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class PaypalPaymentCapturedEvent:
    """
    Evento de dominio que representa un pago capturado por PayPal.
    Este evento se dispara desde la capa de Application Service
    después de procesar el payload del InboxEvent.
    """
    capture_id: str      # ID único del capture de PayPal
    order_id: str        # ID de la orden interna (custom_id de PayPal)
    amount: Decimal      # Monto del pago
    currency: str        # Moneda del pago (USD, EUR, etc.)
    payer_email: str     # Email del pagador
    payer_name: str      # Nombre del pagador
    resource: dict        # Payload completo del resource de PayPal (opcional, para referencia)