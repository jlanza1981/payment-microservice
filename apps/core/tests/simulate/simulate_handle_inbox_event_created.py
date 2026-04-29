# archivo: simulate_inbox_event.py
# Ejecuta: python manage.py shell < simulate_inbox_event.py

import logging

from apps.core.domain.events.inbox_event_created import InboxEventCreated
from apps.core.infrastructure.inbox.event_handlers import handle_inbox_event_created
from apps.pagos.models import InboxEvent

# Configurar logger para ver salida en consola
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def simulate_declined_event():
    """
    Simula un evento 'DECLINED' de PayPal y lo procesa usando
    handle_inbox_event_created como si viniera del webhook.
    """

    # 1️⃣ Simular payload como lo haría PayPal
    payload = {
      "id": "WH-1DY742749C901052A-6FG96269AC0447055F",
      "links": [
        {
          "rel": "self",
          "href": "https://api.sandbox.paypal.com/v1/notifications/webhooks-events/WH-1DY742749C901052A-6FG96269AC0447055F",
          "method": "GET"
        },
        {
          "rel": "resend",
          "href": "https://api.sandbox.paypal.com/v1/notifications/webhooks-events/WH-1DY742749C901052A-6FG96269AC0447055F/resend",
          "method": "POST"
        }
      ],
      "summary": "Payment DECLINED for CA$ 628.59 CAD",
      "resource": {
        "id": "8SA408191P92854JJ",
        "links": [
          {
            "rel": "self",
            "href": "https://api.sandbox.paypal.com/v2/payments/captures/8SA408191P928543J",
            "method": "GET"
          },
          {
            "rel": "refund",
            "href": "https://api.sandbox.paypal.com/v2/payments/captures/8SA408191P928543J/refund",
            "method": "POST"
          },
          {
            "rel": "up",
            "href": "https://api.sandbox.paypal.com/v2/checkout/orders/57S68330GE147383E",
            "method": "GET"
          }
        ],
        "payee": {
          "merchant_id": "D7B352GFB58C8",
          "email_address": "sb-4y4hu48908383@business.example.com"
        },
        "amount": {
          "value": "628.59",
          "currency_code": "CAD"
        },
        "status": "DECLINED",
        "custom_id": "94",
        "create_time": "2026-03-25T22:36:48Z",
        "update_time": "2026-03-25T22:36:48Z",
        "final_capture": True,
        "seller_protection": {
          "status": "ELIGIBLE",
          "dispute_categories": [
            "ITEM_NOT_RECEIVED",
            "UNAUTHORIZED_TRANSACTION"
          ]
        }
      },
      "event_type": "PAYMENT.CAPTURE.DECLINED",
      "create_time": "2026-03-25T22:36:53.097Z",
      "event_version": "1.0",
      "resource_type": "capture",
      "resource_version": "2.0"
    }

    # 2️⃣ Crear o conseguir registro en InboxEvent (simula webhook)
    inbox_event, created = InboxEvent.objects.get_or_create(
        event_id="TEST_DECLINED_001",
        defaults={
            "provider": "paypal",
            "event_type": "PAYMENT.CAPTURE.DECLINED",
            "payload": payload,
            "processed": False,
            "payer_name": "Usuario Test",
            "payment_order_id": 1  # Ajusta según tu PaymentOrder real
        }
    )

    logger.info(f"✅ InboxEvent creado: {inbox_event.id}, creado={created}")

    # 3️⃣ Crear evento de dominio usando tu clase actual
    event = InboxEventCreated(
        inbox_event_id=inbox_event.id,
        provider="PAYPAL",
        event_type="PAYMENT.CAPTURE.DENIED",  # Esto se asigna a provider_event_type
        event_id="TEST_DECLINED_001",
        payment_order_id=1,
        payer_name="Usuario Test"
    )

    # 4️⃣ Ejecutar handler real
    try:
        handle_inbox_event_created(event)
        logger.info(f"🎉 Evento procesado correctamente: {inbox_event.id}")
    except Exception as e:
        logger.error(f"❌ Error procesando evento: {str(e)}", exc_info=True)


if __name__ == "__main__":
    simulate_declined_event()