# Tests de Payment Providers

Esta carpeta contiene tests para el módulo `apps.payment_providers` que gestiona:
- Integración con proveedores de pago (PayPal, Stripe, etc.)
- Eventos de dominio de pagos
- Procesamiento de webhooks

---

## 📋 Tests Disponibles

### `test_event_flow_simple.py`
- **Descripción:** Test simplificado del flujo de eventos de pagos
- **Verifica:** Lógica del dispatcher de eventos
- **Ejecutar:** `python apps/payment_providers/tests/test_event_flow_simple.py`

### `test_payment_flow.py`
- **Descripción:** Test del flujo completo de eventos de pagos parciales
- **Verifica:** 
  - Primer pago parcial → Recibo
  - Pago completo → Factura
  - Múltiples abonos
- **Ejecutar:** `python apps/payment_providers/tests/test_payment_flow.py`

### `test_payment_token.py`
- **Descripción:** Verificación de tokens de pago cifrados
- **Verifica:** 
  - Creación de tokens
  - Cifrado/Descifrado
  - Validación
- **Ejecutar:** `python apps/payment_providers/tests/test_payment_token.py`

---

## 🚀 Ejecutar Tests

```bash
# Ejecutar todos los tests
cd /home/jlanza/projects/backend/django/api

python apps/payment_providers/tests/test_event_flow_simple.py
python apps/payment_providers/tests/test_payment_flow.py
python apps/payment_providers/tests/test_payment_token.py
```

---

## 📚 Eventos de Dominio

Los eventos de dominio definidos en este módulo:

- `PaymentCapturedEvent` - Pago capturado exitosamente
- `PaymentFailedEvent` - Pago fallido
- `PaymentRefundedEvent` - Pago reembolsado

---

## 🔗 Relacionado

- **Código:** `apps/payment_providers/domain/`, `apps/payment_providers/application/`
- **Documentación general:** `docs/`

