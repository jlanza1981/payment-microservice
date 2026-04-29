# Diagramas de Flujos de Pago

Visualización completa de los flujos de pago en el sistema LC Mundo.

## 📋 Índice

1. [Flujo 1: Pago Exonerado](#flujo-1-pago-exonerado)
2. [Flujo 2: Pago Anticipado](#flujo-2-pago-anticipado)
3. [Flujo 3: Pago Normal con Factura](#flujo-3-pago-normal-con-factura)
4. [Diagrama de Estados del Pago](#diagrama-de-estados-del-pago)
5. [Diagrama de Componentes](#diagrama-de-componentes)
6. [Diagrama de Secuencia Completo](#diagrama-de-secuencia-completo)

---

## Flujo 1: Pago Exonerado

### Descripción

Estudiante exonerado → Factura generada → Pago automático verificado

### Diagrama de Flujo

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUJO EXONERADO                              │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐
│  Estudiante  │
│  Exonerado   │
└──────┬───────┘
       │
       ├──────────────────────────────────────────────────┐
       │                                                   │
       v                                                   v
┌─────────────────┐                              ┌────────────────┐
│  PaymentOrder   │                              │   Oportunidad  │
│                 │                              │   de Venta     │
│ status:         │                              │                │
│ "EXONERATED"    │◄─────────────────────────────┤ status: Closed │
│                 │                              │                │
│ allows_partial: │                              └────────────────┘
│     false       │
└────────┬────────┘
         │
         │ 1. Crear Orden Exonerada
         │
         v
┌─────────────────┐
│    Invoice      │
│                 │
│ status: 'E'     │◄────────┐
│ (Exonerada)     │         │
│                 │         │ 2. Generar Factura
│ total: $1500    │         │    automáticamente
│ balance_due:    │         │
│   $1500         │         │
└────────┬────────┘         │
         │                  │
         │ 3. Crear Pago    │
         │    Automático    │
         │                  │
         v                  │
┌─────────────────┐         │
│    Payment      │         │
│                 │         │
│ payment_number: │         │
│   PAY-00001     │         │
│                 │         │
│ payment_method: │         │
│   'EX'          │         │
│                 │─────────┘
│ status: 'V'     │ 4. Actualizar balance
│ (Verificado)    │    invoice.balance_due = 0
│                 │    invoice.status = 'P'
│ amount: $1500   │
│                 │
│ invoice: ───────┼────────► Invoice
│                 │
└─────────────────┘

                     ┌─────────────────────┐
                     │   RESULTADO FINAL   │
                     ├─────────────────────┤
                     │ • Orden: EXONERATED │
                     │ • Factura: Pagada   │
                     │ • Pago: Verificado  │
                     │ • Balance: $0       │
                     └─────────────────────┘
```

### Código

```python
# Crear pago exonerado
payment = use_case.create_exonerated_payment(
    invoice=invoice,
    user=student,
    advisor=advisor,
    amount=Decimal('1500.00')
)

# Resultado:
# - payment.payment_method = 'EX'
# - payment.status = 'V'
# - invoice.balance_due = 0
# - invoice.status = 'P'
```

---

## Flujo 2: Pago Anticipado

### Descripción

Estudiante paga primero → Pago registrado sin factura → Factura generada después → Asociación

### Diagrama de Flujo

```
┌─────────────────────────────────────────────────────────────────┐
│                  FLUJO PAGO ANTICIPADO                          │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐
│  Estudiante  │
│  Paga por    │
│   PayPal     │
└──────┬───────┘
       │
       │ 1. Realizar Pago
       │    (PayPal/Stripe/etc)
       │
       v
┌─────────────────┐         ┌──────────────────────┐
│    Payment      │         │  Gateway de Pago     │
│                 │◄────────┤  (PayPal/Stripe)     │
│ payment_number: │         │                      │
│   PAY-00002     │         │  transaction_id:     │
│                 │         │    PAYPAL-123456     │
│ payment_method: │         │                      │
│   'PP'          │         │  amount: $500.00     │
│                 │         │  status: COMPLETED   │
│ status: 'D'     │         └──────────────────────┘
│ (Disponible)    │
│                 │
│ amount: $500    │
│                 │
│ invoice: NULL   │◄───────── SIN FACTURA AÚN
│                 │
└────────┬────────┘
         │
         │ Tiempo transcurre...
         │
         v
┌─────────────────┐
│  PaymentOrder   │
│                 │
│ status: ACTIVE  │
│                 │
│ total: $500     │
└────────┬────────┘
         │
         │ 2. Generar Factura
         │    (después del pago)
         │
         v
┌─────────────────┐
│    Invoice      │
│                 │
│ invoice_number: │
│   FAC-00001     │
│                 │
│ status: 'I'     │
│ (Emitida)       │
│                 │
│ total: $500     │
│ balance_due:    │
│   $500          │
└────────┬────────┘
         │
         │ 3. Asociar Pago
         │    a Factura
         │
         v
┌─────────────────┐         ┌─────────────────────┐
│    Payment      │         │ PaymentAllocation   │
│  (ACTUALIZADO)  │         │                     │
│                 │         │ payment: ────┐      │
│ invoice: ───────┼────────►│ Invoice      │      │
│   FAC-00001     │         │              │      │
│                 │         │ invoice_     │      │
│ status: 'V'     │         │ detail: ─────┼────► InvoiceDetail
│ (Verificado)    │         │              │      │
│                 │◄────────┤ amount_      │      │
│                 │         │ applied:     │      │
│                 │         │   $500       │      │
└─────────────────┘         │              │      │
                            │ status: PAID │      │
         │                  └──────────────┘      │
         │                                        │
         │ 4. Actualizar Factura                  │
         │                                        │
         v                                        v
┌─────────────────┐                    ┌──────────────┐
│    Invoice      │                    │ InvoiceDetail│
│  (ACTUALIZADA)  │                    │              │
│                 │                    │ payment_     │
│ balance_due: $0 │                    │ concept:     │
│                 │                    │  Matrícula   │
│ status: 'P'     │                    │              │
│ (Pagada)        │                    │ unit_price:  │
└─────────────────┘                    │   $500       │
                                       └──────────────┘

                     ┌─────────────────────┐
                     │   RESULTADO FINAL   │
                     ├─────────────────────┤
                     │ • Pago: Verificado  │
                     │ • Factura: Pagada   │
                     │ • Balance: $0       │
                     │ • Allocations: OK   │
                     └─────────────────────┘
```

### Código

```python
# PASO 1: Crear pago sin factura
payment = use_case.create_advance_payment(
    user=student,
    advisor=advisor,
    amount=Decimal('500.00'),
    payment_method='PP',
    payment_reference_number='PAYPAL-123456',
    status='D'
)
# payment.invoice = None

# PASO 2: Generar factura (tiempo después)
invoice = create_invoice_use_case.execute(...)

# PASO 3: Asociar factura al pago
payment = use_case.associate_invoice_to_payment(
    payment_id=payment.id,
    invoice_id=invoice.id,
    allocations=[...]
)
# payment.invoice = invoice
# invoice.balance_due = 0
```

---

## Flujo 3: Pago Normal con Factura

### Descripción

Orden → Factura → Estudiante paga → Pago registrado

### Diagrama de Flujo

```
┌─────────────────────────────────────────────────────────────────┐
│                   FLUJO PAGO NORMAL                             │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐
│  Oportunidad │
│  de Venta    │
└──────┬───────┘
       │
       │ 1. Crear Orden
       │
       v
┌─────────────────┐
│  PaymentOrder   │
│                 │
│ status: PENDING │
│                 │
│ total: $1000    │
└────────┬────────┘
         │
         │ 2. Generar Factura
         │
         v
┌─────────────────┐
│    Invoice      │
│                 │
│ status: 'I'     │
│ (Emitida)       │
│                 │
│ total: $1000    │
│ balance_due:    │
│   $1000         │
└────────┬────────┘
         │
         │ 3. Estudiante realiza pago
         │    (Link de pago)
         │
         v
┌──────────────┐         ┌─────────────────┐
│  Estudiante  │────────►│  Gateway Pago   │
│  Paga        │         │  (PayPal/Stripe)│
└──────────────┘         └────────┬────────┘
                                  │
                                  │ 4. Webhook/Callback
                                  │
                                  v
                         ┌─────────────────┐
                         │    Payment      │
                         │                 │
                         │ payment_method: │
                         │   'PP'          │
                         │                 │
                         │ status: 'D'     │
                         │                 │
                         │ amount: $1000   │
                         │                 │
                         │ invoice: ───────┼───► Invoice
                         │   FAC-00001     │
                         └────────┬────────┘
                                  │
                                  │ 5. Actualizar
                                  │
                                  v
                         ┌─────────────────┐
                         │    Invoice      │
                         │  (ACTUALIZADA)  │
                         │                 │
                         │ balance_due: $0 │
                         │                 │
                         │ status: 'P'     │
                         │ (Pagada)        │
                         └─────────────────┘

                     ┌─────────────────────┐
                     │   RESULTADO FINAL   │
                     ├─────────────────────┤
                     │ • Orden: PAID       │
                     │ • Factura: Pagada   │
                     │ • Pago: Disponible  │
                     │ • Balance: $0       │
                     └─────────────────────┘
```

---

## Diagrama de Estados del Pago

```
┌─────────────────────────────────────────────────────────────────┐
│                  ESTADOS DE UN PAGO                             │
└─────────────────────────────────────────────────────────────────┘

                    ┌───────────────┐
                    │     INICIO    │
                    └───────┬───────┘
                            │
                ┌───────────┴──────────┐
                │                      │
                v                      v
        ┌───────────────┐      ┌──────────────┐
        │  'P'          │      │  'D'         │
        │  Pendiente    │      │  Disponible  │
        │  por verificar│      │              │
        └───────┬───────┘      └──────┬───────┘
                │                     │
                │  verificar()        │  verificar()
                │                     │
                └──────────┬──────────┘
                           │
                           v
                    ┌──────────────┐
                    │  'V'         │
                    │  Verificado  │
                    └──────┬───────┘
                           │
                           │  (Estado final exitoso)
                           │
                           v
                    ┌──────────────┐
                    │  Pagos con   │
                    │  invoice     │
                    │  actualizan  │
                    │  balance     │
                    └──────────────┘

        ┌────────────┐                    ┌────────────┐
        │  'R'       │                    │  'X'       │
        │  Rechazado │◄───────────────────┤  Anulado   │
        └────────────┘    reject()        └────────────┘
             ↑                                   ↑
             │                                   │
             │ reject()                          │ cancel()
             │                                   │
        ┌────┴─────┐                      ┌─────┴──────┐
        │  'P' / 'D'│                     │  Cualquier │
        └──────────┘                      │  Estado    │
                                          └────────────┘

LEYENDA:
• 'P' - Pendiente por verificar (requiere verificación manual)
• 'D' - Disponible (pagos automáticos verificados, ej: PayPal)
• 'V' - Verificado (aprobado por tesorería)
• 'R' - Rechazado (pago no válido)
• 'X' - Anulado (pago cancelado)

ESTADOS ESPECIALES:
• Pagos con payment_method='EX' → status='V' automáticamente
• Pagos sin invoice → cualquier estado excepto 'V'
```

---

## Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│              ARQUITECTURA DE COMPONENTES                        │
└─────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                          │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │         Django Ninja API Endpoints                       │ │
│  │                                                          │ │
│  │  POST /api/v1/payments/                                 │ │
│  │  POST /api/v1/payments/exonerated/                      │ │
│  │  POST /api/v1/payments/advance/                         │ │
│  │  PATCH /api/v1/payments/{id}/associate-invoice/        │ │
│  └──────────────────────────────────────────────────────────┘ │
│                          │                                     │
│                          │  Pydantic Schemas                   │
│                          v                                     │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  PaymentInputSchema                                      │ │
│  │  PaymentAllocationInputSchema                           │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
                          │
                          │  Commands
                          v
┌────────────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                            │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │         CreatePaymentUseCase                             │ │
│  │                                                          │ │
│  │  • execute()                                            │ │
│  │  • create_exonerated_payment()                          │ │
│  │  • create_advance_payment()                             │ │
│  │  • associate_invoice_to_payment()                       │ │
│  │                                                          │ │
│  │  • _validate_payment_data()                             │ │
│  │  • _prepare_payment_data()                              │ │
│  │  • _create_payment_with_invoice()                       │ │
│  │  • _create_payment_without_invoice()                    │ │
│  └──────────────────────────────────────────────────────────┘ │
│                          │                                     │
│                          │  Repository Interface               │
│                          v                                     │
└────────────────────────────────────────────────────────────────┘
                          │
┌────────────────────────────────────────────────────────────────┐
│                     DOMAIN LAYER                               │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │      PaymentRepositoryInterface (Abstract)               │ │
│  │                                                          │ │
│  │  • create()                                             │ │
│  │  • update()                                             │ │
│  │  • get_by_id()                                          │ │
│  │  • cancel()                                             │ │
│  │  • verify()                                             │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
                          │
                          │  Implements
                          v
┌────────────────────────────────────────────────────────────────┐
│                  INFRASTRUCTURE LAYER                          │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │      PaymentRepository (Implementation)                  │ │
│  │                                                          │ │
│  │  • Django ORM Operations                                │ │
│  │  • Transaction Management                               │ │
│  │  • Query Optimization                                   │ │
│  └──────────────────────────────────────────────────────────┘ │
│                          │                                     │
│                          │  ORM                                │
│                          v                                     │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              Django Models                               │ │
│  │                                                          │ │
│  │  • Payment                                              │ │
│  │  • PaymentAllocation                                    │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
                          │
                          v
┌────────────────────────────────────────────────────────────────┐
│                      DATABASE                                  │
│                                                                │
│  Tables:                                                       │
│  • payments                                                    │
│  • payment_allocations                                         │
│  • invoices                                                    │
│  • invoice_details                                             │
│  • payment_orders                                              │
└────────────────────────────────────────────────────────────────┘
```

---

## Diagrama de Secuencia Completo

### Secuencia: Crear Pago Exonerado

```
Actor         API          UseCase        Repository      Models        Database
  │            │              │               │             │               │
  │ POST       │              │               │             │               │
  │ /payments/ │              │               │             │               │
  │────────────►              │               │             │               │
  │            │              │               │             │               │
  │            │ execute()    │               │             │               │
  │            │──────────────►               │             │               │
  │            │              │               │             │               │
  │            │              │ _validate_    │             │               │
  │            │              │ payment_data()│             │               │
  │            │              │───────┐       │             │               │
  │            │              │       │       │             │               │
  │            │              │◄──────┘       │             │               │
  │            │              │               │             │               │
  │            │              │ _prepare_     │             │               │
  │            │              │ payment_data()│             │               │
  │            │              │───────┐       │             │               │
  │            │              │       │       │             │               │
  │            │              │◄──────┘       │             │               │
  │            │              │               │             │               │
  │            │              │ create()      │             │               │
  │            │              │───────────────►             │               │
  │            │              │               │             │               │
  │            │              │               │ Payment.    │               │
  │            │              │               │ create()    │               │
  │            │              │               │─────────────►               │
  │            │              │               │             │               │
  │            │              │               │             │ INSERT        │
  │            │              │               │             │───────────────►
  │            │              │               │             │               │
  │            │              │               │             │◄──────────────┤
  │            │              │               │             │               │
  │            │              │               │ PaymentAlloc│               │
  │            │              │               │ .create()   │               │
  │            │              │               │─────────────►               │
  │            │              │               │             │               │
  │            │              │               │             │ INSERT        │
  │            │              │               │             │───────────────►
  │            │              │               │             │               │
  │            │              │               │◄────────────┤               │
  │            │              │               │             │               │
  │            │              │               │ Invoice.    │               │
  │            │              │               │ update_     │               │
  │            │              │               │ balance()   │               │
  │            │              │               │─────────────►               │
  │            │              │               │             │               │
  │            │              │               │             │ UPDATE        │
  │            │              │               │             │───────────────►
  │            │              │               │             │               │
  │            │              │◄──────────────┤             │               │
  │            │              │               │             │               │
  │            │              │ Payment       │             │               │
  │            │◄─────────────┤               │             │               │
  │            │              │               │             │               │
  │            │ 201 Created  │               │             │               │
  │◄───────────┤              │               │             │               │
  │            │              │               │             │               │
```

### Secuencia: Pago Anticipado (Sin Factura → Con Factura)

```
Actor         API          UseCase        Repository      Models        Database
  │            │              │               │             │               │
  │ POST       │              │               │             │               │
  │ /payments/ │              │               │             │               │
  │ advance/   │              │               │             │               │
  │────────────►              │               │             │               │
  │            │              │               │             │               │
  │            │ create_      │               │             │               │
  │            │ advance_     │               │             │               │
  │            │ payment()    │               │             │               │
  │            │──────────────►               │             │               │
  │            │              │               │             │               │
  │            │              │ execute()     │             │               │
  │            │              │ (invoice=None)│             │               │
  │            │              │───────┐       │             │               │
  │            │              │       │       │             │               │
  │            │              │◄──────┘       │             │               │
  │            │              │               │             │               │
  │            │              │ create()      │             │               │
  │            │              │───────────────►             │               │
  │            │              │               │             │               │
  │            │              │               │ Payment.    │               │
  │            │              │               │ create()    │               │
  │            │              │               │ invoice=None│               │
  │            │              │               │─────────────►               │
  │            │              │               │             │               │
  │            │              │               │             │ INSERT        │
  │            │              │               │             │───────────────►
  │            │              │               │             │               │
  │            │              │◄──────────────┤             │               │
  │            │              │               │             │               │
  │            │ Payment      │               │             │               │
  │            │ (sin factura)│               │             │               │
  │◄───────────┤              │               │             │               │
  │            │              │               │             │               │
  │            │              │               │             │               │
  │ ─ ─ ─ ─ ─ TIEMPO TRANSCURRE (Generar factura) ─ ─ ─ ─ ─ │               │
  │            │              │               │             │               │
  │ PATCH      │              │               │             │               │
  │ /payments/ │              │               │             │               │
  │ {id}/      │              │               │             │               │
  │ associate- │              │               │             │               │
  │ invoice/   │              │               │             │               │
  │────────────►              │               │             │               │
  │            │              │               │             │               │
  │            │ associate_   │               │             │               │
  │            │ invoice_to_  │               │             │               │
  │            │ payment()    │               │             │               │
  │            │──────────────►               │             │               │
  │            │              │               │             │               │
  │            │              │ update()      │             │               │
  │            │              │───────────────►             │               │
  │            │              │               │             │               │
  │            │              │               │ Payment.    │               │
  │            │              │               │ update()    │               │
  │            │              │               │ SET invoice │               │
  │            │              │               │─────────────►               │
  │            │              │               │             │               │
  │            │              │               │             │ UPDATE        │
  │            │              │               │             │───────────────►
  │            │              │               │             │               │
  │            │              │               │ Invoice.    │               │
  │            │              │               │ update_     │               │
  │            │              │               │ balance()   │               │
  │            │              │               │─────────────►               │
  │            │              │               │             │               │
  │            │              │               │             │ UPDATE        │
  │            │              │               │             │───────────────►
  │            │              │               │             │               │
  │            │              │◄──────────────┤             │               │
  │            │              │               │             │               │
  │            │ Payment      │               │             │               │
  │            │ (con factura)│               │             │               │
  │◄───────────┤              │               │             │               │
  │            │              │               │             │               │
```

---

## 📊 Resumen Visual

### Estados y Transiciones

```
┌─────────────────────────────────────────────────────────────────┐
│                  MATRIZ DE TRANSICIONES                         │
├─────────────┬───────────────────────────────────────────────────┤
│ Estado      │ Transiciones Permitidas                           │
├─────────────┼───────────────────────────────────────────────────┤
│ P (Pend)    │ → V (verificar), R (rechazar), X (anular)        │
│ D (Disp)    │ → V (verificar), R (rechazar), X (anular)        │
│ V (Verif)   │ → X (anular)                                     │
│ R (Rech)    │ (Estado final - no transiciones)                 │
│ X (Anulado) │ (Estado final - no transiciones)                 │
└─────────────┴───────────────────────────────────────────────────┘
```

### Métodos de Pago

```
┌─────────────────────────────────────────────────────────────────┐
│                    MÉTODOS DE PAGO                              │
├──────┬──────────────────────┬──────────────┬───────────────────┤
│ Code │ Nombre               │ Estado Def.  │ Requiere Verif.  │
├──────┼──────────────────────┼──────────────┼───────────────────┤
│ PP   │ PayPal               │ D            │ No (auto)        │
│ ST   │ Stripe               │ D            │ No (auto)        │
│ TC   │ Tarjeta Crédito      │ D            │ No (auto)        │
│ TD   │ Tarjeta Débito       │ D            │ No (auto)        │
│ BT   │ Transferencia        │ P            │ Sí (manual)      │
│ EF   │ Efectivo             │ P            │ Sí (manual)      │
│ CH   │ Cheque               │ P            │ Sí (manual)      │
│ EX   │ Exonerado            │ V            │ No (auto)        │
│ OT   │ Otro                 │ P            │ Sí (manual)      │
└──────┴──────────────────────┴──────────────┴───────────────────┘
```

---

**Versión:** 1.0  
**Última actualización:** 2026-01-12  
**Autor:** Sistema LC Mundo
