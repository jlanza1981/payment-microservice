# 📊 Diagramas de Flujo - Sistema de Pagos PayPal

## 🎯 Diagrama General del Sistema

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SISTEMA DE PAGOS LC MUNDO                        │
└─────────────────────────────────────────────────────────────────────────┘

FASE 1: GENERACIÓN DE ORDEN
─────────────────────────────
┌──────────────┐
│   Asesor     │ Crea orden de pago ($1000)
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│  PaymentOrder    │ order_number: PO-2025-00001
│  total: $1000    │ allows_partial: true
│  status: PENDING │
└──────┬───────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  SendPaymentLinkEmail                │ 📧 Email al estudiante
│  → Link PayPal con custom_id         │
│  → Monto total: $1000                │
│  → Permite abonos parciales          │
└──────────────────────────────────────┘


FASE 2: ESTUDIANTE REALIZA PAGO
────────────────────────────────
┌──────────────┐
│  Estudiante  │ Paga en PayPal
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────┐
│  PayPal                              │
│  → Procesa pago                      │
│  → Genera capture_id                 │
│  → Envía webhook                     │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  PAYMENT.CAPTURE.COMPLETED           │ ⚡ Webhook
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  PaypalPaymentCaptureProcess         │ 🔄 Procesamiento
│  → Extrae datos                      │
│  → Verifica duplicados               │
│  → Determina tipo de pago            │
│  → Crea factura/pago                 │
│  → Envía notificación                │
└──────────────────────────────────────┘
```

---

## 🔀 Diagrama de Decisión: ¿Qué tipo de pago es?

```
┌─────────────────────────────────────────┐
│  Webhook recibido                       │
│  PayPal Order ID: ABC123               │
│  Payment Order ID: 456                  │
│  Amount: $XXX                           │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  1. Crear PaymentTransaction            │ ✅ Evita duplicados
│     - paypal_order_id: ABC123           │
│     - payment_order: 456                │
│     - amount: $XXX                      │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  2. Obtener PaymentOrder (ID: 456)      │
│     - total_order: $1000                │
│     - allows_partial: true              │
└──────────────┬──────────────────────────┘
               │
               ▼
        ┌──────┴──────┐
        │  ¿Existe     │
        │  Factura?    │
        └──────┬───────┘
               │
       ┌───────┴───────┐
       │               │
      SÍ              NO
       │               │
       ▼               ▼
┌──────────────┐  ┌──────────────────┐
│  ABONO       │  │  PRIMER PAGO     │
│  ADICIONAL   │  │                  │
└──────┬───────┘  └─────┬────────────┘
       │                │
       │                ▼
       │         ┌──────────────┐
       │         │  Comparar:   │
       │         │  Monto pagado│
       │         │  vs Total    │
       │         └──────┬───────┘
       │                │
       │        ┌───────┴────────┐
       │        │                │
       │     $XXX >= $1000    $XXX < $1000
       │        │                │
       │        ▼                ▼
       │   ┌─────────┐      ┌─────────┐
       │   │ TOTAL   │      │ PARCIAL │
       │   │ P       │      │ PP      │
       │   └────┬────┘      └────┬────┘
       │        │                │
       └────────┴────────────────┘
                │
                ▼
        ┌───────────────┐
        │  Procesar     │
        │  según tipo   │
        └───────────────┘
```

---

## 💰 Flujo Detallado: PAGO TOTAL

```
┌─────────────────────────────────────────────────────────────┐
│  Webhook: $1000 (orden total: $1000)                        │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  ¿Existe factura? → NO                                      │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  _process_first_payment()                                   │
│  1. Compara: $1000 >= $1000 ✓                              │
│  2. invoice_status = 'P' (Pagada)                           │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  _create_invoice(status='P')                                │
│  📄 Invoice                                                 │
│  ├─ invoice_number: FAC-2025-00001                         │
│  ├─ status: P (Pagada)                                      │
│  ├─ total: $1000                                            │
│  └─ balance_due: $1000 (se actualizará)                    │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  _create_payment()                                          │
│  💵 Payment                                                 │
│  ├─ payment_number: PAY-2025-00001                         │
│  ├─ amount: $1000                                           │
│  ├─ status: D (Disponible)                                 │
│  ├─ payment_method: PP (PayPal)                            │
│  └─ payment_reference_number: ABC123                        │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Invoice.update_balance() (automático en save)              │
│  📊 Actualización                                           │
│  ├─ balance_due: $1000 - $1000 = $0                        │
│  └─ status: P (confirmado)                                  │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  _send_full_payment_notification()                          │
│  📧 send_invoice_email_task.delay(invoice.id)              │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Celery Task: send_invoice_email_task                       │
│  📨 Email al estudiante                                     │
│  ├─ Subject: "Factura #FAC-2025-00001 - Pago Completo"    │
│  ├─ Template: invoice_complete_email.html                   │
│  ├─ Adjunto: factura_FAC-2025-00001.pdf                    │
│  └─ Content: "¡Felicitaciones! Pago completado"           │
└─────────────────────────────────────────────────────────────┘
```

---

## 💳 Flujo Detallado: PRIMER ABONO

```
┌─────────────────────────────────────────────────────────────┐
│  Webhook: $300 (orden total: $1000)                         │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  ¿Existe factura? → NO                                      │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  _process_first_payment()                                   │
│  1. Compara: $300 < $1000 ✓                                │
│  2. invoice_status = 'PP' (Parcialmente Pagada)             │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  _create_invoice(status='PP')                               │
│  📄 Invoice                                                 │
│  ├─ invoice_number: FAC-2025-00001                         │
│  ├─ status: PP (Parcialmente Pagada)                        │
│  ├─ total: $1000                                            │
│  └─ balance_due: $1000 (inicial)                            │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  _create_payment()                                          │
│  💵 Payment                                                 │
│  ├─ payment_number: PAY-2025-00001                         │
│  ├─ amount: $300                                            │
│  ├─ status: D (Disponible)                                 │
│  └─ invoice: FAC-2025-00001                                │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Invoice.update_balance() (automático)                      │
│  📊 Actualización                                           │
│  ├─ balance_due: $1000 - $300 = $700                       │
│  └─ status: PP (confirmado)                                 │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Signal: create_payment_receipt (automático)                │
│  ⚡ Se activa porque balance_due > 0                        │
│                                                             │
│  📝 PaymentReceipt creado                                  │
│  ├─ receipt_number: REC-2025-00001                         │
│  ├─ payment: PAY-2025-00001                                │
│  ├─ amount_paid: $300                                       │
│  ├─ previous_balance: $1000                                 │
│  └─ new_balance: $700                                       │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Celery Tasks (en paralelo)                                 │
│  1️⃣ generate_receipt_pdf_task.delay()                      │
│     └─ Genera: recibo_REC-2025-00001.pdf                   │
│  2️⃣ send_receipt_email_task.delay()                        │
│     └─ Envía email con recibo adjunto                      │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  📨 Email al estudiante                                     │
│  ├─ Subject: "Recibo de Abono #REC-2025-00001"            │
│  ├─ Template: payment_receipt_email.html                    │
│  ├─ Adjunto: recibo_REC-2025-00001.pdf                     │
│  └─ Content:                                                │
│     "Abonado: $300"                                         │
│     "Saldo pendiente: $700"                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Flujo Detallado: ABONO ADICIONAL

```
┌─────────────────────────────────────────────────────────────┐
│  Webhook: $400 (balance actual: $700)                       │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  ¿Existe factura? → SÍ (FAC-2025-00001)                    │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  _process_additional_payment()                              │
│  ℹ️ NO crea nueva factura                                  │
│  ✓ Usa factura existente: FAC-2025-00001                   │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  _create_payment()                                          │
│  💵 Payment (nuevo)                                         │
│  ├─ payment_number: PAY-2025-00002                         │
│  ├─ amount: $400                                            │
│  ├─ status: D                                               │
│  └─ invoice: FAC-2025-00001 (LA MISMA)                     │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Invoice.update_balance()                                   │
│  📊 Actualización                                           │
│  ├─ balance_due: $700 - $400 = $300                        │
│  └─ status: PP (sigue parcial)                              │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Signal: create_payment_receipt                             │
│  📝 PaymentReceipt #2                                       │
│  ├─ receipt_number: REC-2025-00002                         │
│  ├─ payment: PAY-2025-00002                                │
│  ├─ amount_paid: $400                                       │
│  ├─ previous_balance: $700                                  │
│  └─ new_balance: $300                                       │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  📨 Email: Recibo #REC-2025-00002                          │
│  "Abonado: $400, Saldo pendiente: $300"                    │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ Flujo Detallado: ABONO FINAL (Completa Factura)

```
┌─────────────────────────────────────────────────────────────┐
│  Webhook: $300 (balance actual: $300)                       │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  ¿Existe factura? → SÍ (FAC-2025-00001)                    │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  _process_additional_payment()                              │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  _create_payment()                                          │
│  💵 Payment (final)                                         │
│  ├─ payment_number: PAY-2025-00003                         │
│  ├─ amount: $300                                            │
│  └─ invoice: FAC-2025-00001                                │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Invoice.update_balance()                                   │
│  📊 Actualización FINAL                                     │
│  ├─ balance_due: $300 - $300 = $0 ✓                        │
│  └─ status: PP → P (PAGADA)                                │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  invoice.refresh_from_db()                                  │
│  ├─ Recarga datos actualizados                             │
│  └─ Verifica: balance_due <= 0 ✓                           │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  _send_full_payment_notification()                          │
│  🎉 FACTURA COMPLETADA                                      │
│  └─ send_invoice_email_task.delay()                         │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  📨 Email: FACTURA COMPLETA                                 │
│  ├─ Subject: "¡Factura Pagada! #FAC-2025-00001"           │
│  ├─ Adjunto: factura_FAC-2025-00001.pdf                    │
│  └─ Content: "¡Felicitaciones! Pago completado"           │
└─────────────────────────────────────────────────────────────┘

NOTA: En este caso NO se genera PaymentReceipt
      porque el signal detecta que balance_due = 0
```

---

## 🛡️ Protección contra Duplicados

```
┌─────────────────────────────────────────────────────────────┐
│  Webhook recibido 2 veces (red issue)                       │
│  PayPal Order ID: ABC123                                    │
│  Payment Order ID: 456                                      │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Primera vez:                                               │
│  ├─ get_payment_transaction(ABC123, 456) → None           │
│  ├─ Crea PaymentTransaction ✓                              │
│  └─ Procesa pago normalmente                               │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Segunda vez (duplicado):                                   │
│  ├─ get_payment_transaction(ABC123, 456) → ✓ EXISTE       │
│  └─ NO crea nueva transacción (evita duplicado)            │
└─────────────────────────────────────────────────────────────┘

RESULTADO: ✅ Protección garantizada
```

---

## 📊 Tabla Comparativa de Flujos

| Escenario | Factura Existe | Monto vs Total | Status Factura | Email Enviado |
|-----------|---------------|----------------|----------------|---------------|
| **Pago total** | NO | $1000 >= $1000 | P (Pagada) | Factura completa |
| **Primer abono** | NO | $300 < $1000 | PP (Parcial) | Recibo de abono |
| **Abono adicional** | SÍ | $400 < $700 | PP (Parcial) | Recibo de abono |
| **Abono final** | SÍ | $300 = $300 | P (Pagada) | Factura completa |

---

**Fecha:** 2 de marzo de 2026  
**Versión:** 1.0  
**Estado:** ✅ Documentado y Validado

