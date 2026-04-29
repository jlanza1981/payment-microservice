# 🧊 Corrido en Frío: Pagos Parciales - Flujo Completo

## Contexto
Estudiante quiere un programa de **$500** y pagará en **abonos mínimos de $50**.

---

## 📝 PASO 1: Frontend crea la orden

**⚠️ IMPORTANTE**: En este paso **NO se envía el monto del abono**, solo la configuración de pagos parciales.

### Request:
```json
POST /api/v1/payment-orders/

{
  "student": 123,
  "advisor": 456,
  "currency": "USD",
  "opportunity": 789,
  "allows_partial_payment": true,
  "minimum_payment_amount": 50.00,  // ⚠️ Monto MÍNIMO por abono (NO es el monto a pagar)
  "payment_details": [
    {
      "payment_concept": 1,  // Matrícula
      "amount": 500.00,      // ⚠️ Total a pagar (NO el abono)
      "quantity": 1
    }
  ],
  "program_data": { ... }
}
```

**Campos importantes**:
- `allows_partial_payment: true` → Habilita pagos en abonos
- `minimum_payment_amount: 50.00` → Cada abono debe ser >= $50
- `amount: 500.00` → Total del concepto (NO el primer abono)

### Response:
```json
{
  "payment_order": {
    "id": 1,
    "order_number": "PO-00001234",
    "status": "PENDING",
    "total_order": 500.00,
    "allows_partial_payment": true,
    "minimum_payment_amount": 50.00,
    "total_paid": 0.00,
    "balance_due": 500.00,
    "is_partially_paid": false
  }
}
```

### Estado:
- ✅ Orden creada
- 📊 `status`: `PENDING`
- 💰 Total: $500
- 📉 Pagado: $0
- ⏳ Saldo: $500

---

## 📧 PASO 2: Backend envía link de pago

```python
# En el endpoint de creación o en un job separado
order.generate_token_and_expiration_date(days_valid=7)
send_payment_link_email(order)
```

**Email enviado**:
```
Hola Juan,

Tu orden de pago PO-00001234 está lista.
Total: $500.00

Puedes pagar en abonos desde $50.00

Link de pago (válido 7 días):
https://app.com/payment/token123abc456def

Saludos,
Equipo LC
```

### Estado:
- 📧 Email enviado
- 📊 `status`: Sigue en `PENDING` (sin cambios)

---

## 🌐 PASO 3: Estudiante abre el link

### Frontend hace:
```javascript
GET /api/v1/payment-orders/by-token/{token}/

Response:
{
  "order_number": "PO-00001234",
  "status": "PENDING",
  "total_order": 500.00,
  "total_paid": 0.00,
  "balance_due": 500.00,
  "allows_partial_payment": true,
  "minimum_payment_amount": 50.00,
  "is_partially_paid": false,
  "student": {
    "name": "Juan Pérez",
    "email": "juan@example.com"
  },
  "payment_order_details": [...]
}
```

### Pantalla del estudiante:
```
╔══════════════════════════════════════════════╗
║          ORDEN DE PAGO PO-00001234          ║
╠══════════════════════════════════════════════╣
║  Estudiante: Juan Pérez                     ║
║  Programa: Inglés - 12 semanas              ║
║                                             ║
║  💵 Total: $500.00                          ║
║  ✅ Pagado: $0.00                           ║
║  ⚠️ Saldo pendiente: $500.00                ║
║                                             ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   ║
║                                             ║
║  Monto a pagar (mínimo $50.00):            ║
║  ┌─────────────────┐                       ║
║  │ $ [    150.00  ]│ 💳                     ║
║  └─────────────────┘                       ║
║                                             ║
║  Método de pago:                           ║
║  ○ Tarjeta  ○ Transferencia  ○ Efectivo   ║
║                                             ║
║  Referencia/Comprobante:                   ║
║  ┌─────────────────────────────┐           ║
║  │ COMP-001                   │           ║
║  └─────────────────────────────┘           ║
║                                             ║
║          [ PROCESAR PAGO ]                 ║
╚══════════════════════════════════════════════╝
```

Estudiante ingresa: **$150** (primer abono)

---

## 💳 PASO 4: Frontend envía PRIMER pago

**⚠️ AQUÍ es donde se envía el monto del abono** ($150 en este caso).

Este paso puede ocurrir:
- Inmediatamente después de crear la orden
- Días/semanas después (cuando el estudiante abra el link)

### Request:
```json
POST /api/v1/payments/process-payment/

{
  "order_number": "PO-00001234",
  "amount": 150.00,  // ⬅️ MONTO DEL ABONO (lo ingresa el estudiante)
  "payment_method": "TRANSFER",
  "reference_number": "COMP-001",
  "payment_date": "2025-05-15"
}
```

**El estudiante decide** cuánto pagar (respetando el mínimo de $50).

### Backend ejecuta:

```python
from decimal import Decimal
from django.utils import timezone
from payment_orders.models import PaymentOrder
from payments.models import Invoice, InvoiceDetail

def process_payment(order_number, amount, payment_method, reference_number):
    # 1. Obtener orden
    order = PaymentOrder.objects.get(order_number=order_number)
    
    # 2. Validar que puede recibir pagos
    if not order.can_receive_payments():
        raise ValidationError("La orden no puede recibir pagos")
    
    # 3. Si está en PENDING, activarla (primera vez)
    if order.status == 'PENDING':
        order.activate_for_payments()  # PENDING → ACTIVE ✅
    
    # 4. Validar monto mínimo
    if order.minimum_payment_amount and amount < order.minimum_payment_amount:
        raise ValidationError(f"Monto mínimo: {order.minimum_payment_amount}")
    
    # 5. Obtener o CREAR Invoice
    invoice = order.invoices_payment_order.first()
    
    if not invoice:
        # ⚠️ PRIMERA VEZ: Crear Invoice
        invoice = Invoice.objects.create(
            payment_order=order,
            student=order.student,
            total=order.total_order,
            balance_due=order.total_order,
            status='PENDING'
        )
    
    # 6. Validar que no exceda el saldo
    if amount > invoice.balance_due:
        amount = invoice.balance_due
    
    # 7. CREAR InvoiceDetail (registro del pago)
    payment = InvoiceDetail.objects.create(
        invoice=invoice,
        payment_method=payment_method,
        amount=Decimal(amount),
        payment_date=timezone.now(),
        reference_number=reference_number
    )
    
    # 8. Actualizar balance
    invoice.balance_due -= Decimal(amount)
    invoice.save()
    
    # 9. Si se completó el pago, marcar como pagada
    if invoice.balance_due <= 0:
        order.mark_as_paid()  # ACTIVE → PAID
        invoice.status = 'PAID'
        invoice.save()
    
    return {
        'success': True,
        'payment_id': payment.id,
        'new_balance': float(invoice.balance_due),
        'order_status': order.status
    }
```

### Response:
```json
{
  "success": true,
  "payment_id": 789,
  "new_balance": 350.00,
  "order_status": "ACTIVE",
  "message": "Pago registrado exitosamente"
}
```

### Estado en Base de Datos:

**Tabla: payment_order**
```sql
id  | order_number  | status  | total_order | allows_partial_payment | minimum_payment_amount
1   | PO-00001234   | ACTIVE  | 500.00      | true                   | 50.00
```

**Tabla: invoices**
```sql
id  | payment_order_id | total  | balance_due | status
1   | 1                | 500.00 | 350.00      | PENDING
```

**Tabla: invoice_details**
```sql
id  | invoice_id | amount | payment_method | reference_number | payment_date
1   | 1          | 150.00 | TRANSFER       | COMP-001         | 2025-05-15
```

### Estado:
- ✅ Primer pago registrado
- 📊 `status`: `ACTIVE` (recibiendo abonos)
- 💰 Total: $500
- 📈 Pagado: $150
- ⏳ Saldo: $350
- 🔵 `is_partially_paid`: `true`

---

## 🔄 PASO 5: Estudiante vuelve al link (días después)

### Frontend hace:
```javascript
GET /api/v1/payment-orders/by-token/{token}/

Response:
{
  "order_number": "PO-00001234",
  "status": "ACTIVE",  // ⚠️ Cambió de PENDING a ACTIVE
  "total_order": 500.00,
  "total_paid": 150.00,  // ✅ Ya hay pagos
  "balance_due": 350.00,
  "is_partially_paid": true,  // ⚠️ Indica pago parcial
  "minimum_payment_amount": 50.00
}
```

### También puede consultar el historial:
```javascript
GET /api/v1/invoices/?payment_order=1

Response:
{
  "invoice_id": 1,
  "total": 500.00,
  "balance_due": 350.00,
  "status": "PENDING",
  "payments": [
    {
      "id": 1,
      "amount": 150.00,
      "payment_method": "TRANSFER",
      "payment_date": "2025-05-15",
      "reference_number": "COMP-001"
    }
  ]
}
```

### Pantalla del estudiante:
```
╔══════════════════════════════════════════════╗
║          ORDEN DE PAGO PO-00001234          ║
╠══════════════════════════════════════════════╣
║  Estudiante: Juan Pérez                     ║
║  Programa: Inglés - 12 semanas              ║
║                                             ║
║  💵 Total: $500.00                          ║
║  ✅ Pagado: $150.00                         ║
║  ⚠️ Saldo pendiente: $350.00                ║
║                                             ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   ║
║                                             ║
║  📋 Historial de pagos:                     ║
║  • $150.00 - Transferencia - 15/05/2025    ║
║                                             ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   ║
║                                             ║
║  Monto a pagar (mínimo $50.00):            ║
║  ┌─────────────────┐                       ║
║  │ $ [    200.00  ]│ 💳                     ║
║  └─────────────────┘                       ║
║                                             ║
║  Método de pago:                           ║
║  ○ Tarjeta  ● Transferencia  ○ Efectivo   ║
║                                             ║
║  Referencia/Comprobante:                   ║
║  ┌─────────────────────────────┐           ║
║  │ COMP-002                   │           ║
║  └─────────────────────────────┘           ║
║                                             ║
║          [ PROCESAR PAGO ]                 ║
╚══════════════════════════════════════════════╝
```

Estudiante ingresa: **$200** (segundo abono)

---

## 💳 PASO 6: Frontend envía SEGUNDO pago

### Request:
```json
POST /api/v1/payments/process-payment/

{
  "order_number": "PO-00001234",
  "amount": 200.00,
  "payment_method": "CARD",
  "reference_number": "COMP-002"
}
```

### Backend ejecuta (mismo código):
```python
# 1-4. Validaciones...

# 5. Obtener Invoice EXISTENTE (NO crear nuevo)
invoice = order.invoices_payment_order.first()
# ⚠️ Ya existe, NO se crea uno nuevo

# 6-7. Crear nuevo InvoiceDetail
payment = InvoiceDetail.objects.create(
    invoice=invoice,  # ⚠️ Mismo invoice
    payment_method='CARD',
    amount=Decimal('200.00'),
    reference_number='COMP-002'
)

# 8. Actualizar balance
invoice.balance_due = Decimal('150.00')  # $350 - $200
invoice.save()

# 9. Aún no se completa (balance > 0)
```

### Response:
```json
{
  "success": true,
  "payment_id": 790,
  "new_balance": 150.00,
  "order_status": "ACTIVE",
  "message": "Pago registrado exitosamente"
}
```

### Estado en Base de Datos:

**Tabla: payment_order** (sin cambios)
```sql
id  | order_number  | status  | total_order
1   | PO-00001234   | ACTIVE  | 500.00
```

**Tabla: invoices** (balance actualizado)
```sql
id  | payment_order_id | total  | balance_due | status
1   | 1                | 500.00 | 150.00      | PENDING
```

**Tabla: invoice_details** (nuevo registro)
```sql
id  | invoice_id | amount | payment_method | reference_number | payment_date
1   | 1          | 150.00 | TRANSFER       | COMP-001         | 2025-05-15
2   | 1          | 200.00 | CARD           | COMP-002         | 2025-05-20  ⬅️ NUEVO
```

### Estado:
- ✅ Segundo pago registrado
- 📊 `status`: `ACTIVE` (sigue activa)
- 💰 Total: $500
- 📈 Pagado: $350 ($150 + $200)
- ⏳ Saldo: $150
- 🔵 `is_partially_paid`: `true`

---

## 💳 PASO 7: Tercer y último pago

### Request:
```json
POST /api/v1/payments/process-payment/

{
  "order_number": "PO-00001234",
  "amount": 150.00,
  "payment_method": "CASH",
  "reference_number": "COMP-003"
}
```

### Backend ejecuta:
```python
# 1-7. Igual que antes...

# 8. Actualizar balance
invoice.balance_due = Decimal('0.00')  # $150 - $150 = 0

# 9. ⚠️ SE COMPLETA EL PAGO
if invoice.balance_due <= 0:
    order.mark_as_paid()  # ACTIVE → PAID ✅
    invoice.status = 'PAID'
    invoice.save()
```

### Response:
```json
{
  "success": true,
  "payment_id": 791,
  "new_balance": 0.00,
  "order_status": "PAID",  // ⚠️ Cambió a PAID
  "message": "¡Orden pagada completamente!"
}
```

### Estado en Base de Datos:

**Tabla: payment_order**
```sql
id  | order_number  | status | total_order
1   | PO-00001234   | PAID   | 500.00  ⬅️ Cambió a PAID
```

**Tabla: invoices**
```sql
id  | payment_order_id | total  | balance_due | status
1   | 1                | 500.00 | 0.00        | PAID  ⬅️ Cambió a PAID
```

**Tabla: invoice_details** (3 registros)
```sql
id  | invoice_id | amount | payment_method | reference_number | payment_date
1   | 1          | 150.00 | TRANSFER       | COMP-001         | 2025-05-15
2   | 1          | 200.00 | CARD           | COMP-002         | 2025-05-20
3   | 1          | 150.00 | CASH           | COMP-003         | 2025-05-25  ⬅️ NUEVO
```

### Estado Final:
- ✅ Orden completamente pagada
- 📊 `status`: `PAID`
- 💰 Total: $500
- 📈 Pagado: $500
- ⏳ Saldo: $0
- 🔵 `is_partially_paid`: `false` (ya no es parcial)

---

## 📊 Consulta final de la orden

```javascript
GET /api/v1/payment-orders/PO-00001234/

Response:
{
  "order_number": "PO-00001234",
  "status": "PAID",
  "total_order": 500.00,
  "total_paid": 500.00,
  "balance_due": 0.00,
  "allows_partial_payment": true,
  "minimum_payment_amount": 50.00,
  "is_partially_paid": false,  // Ya no es parcial
  "student": { ... },
  "invoice": {
    "id": 1,
    "total": 500.00,
    "balance_due": 0.00,
    "status": "PAID",
    "payments": [
      {
        "id": 1,
        "amount": 150.00,
        "payment_method": "TRANSFER",
        "reference_number": "COMP-001",
        "payment_date": "2025-05-15"
      },
      {
        "id": 2,
        "amount": 200.00,
        "payment_method": "CARD",
        "reference_number": "COMP-002",
        "payment_date": "2025-05-20"
      },
      {
        "id": 3,
        "amount": 150.00,
        "payment_method": "CASH",
        "reference_number": "COMP-003",
        "payment_date": "2025-05-25"
      }
    ]
  }
}
```

---

## 🎯 Resumen de Estados

| Momento | Status Orden | Total Paid | Balance Due | is_partially_paid |
|---------|-------------|------------|-------------|-------------------|
| Orden creada | `PENDING` | $0 | $500 | `false` |
| Primer pago ($150) | `ACTIVE` | $150 | $350 | `true` ✅ |
| Segundo pago ($200) | `ACTIVE` | $350 | $150 | `true` ✅ |
| Tercer pago ($150) | `PAID` | $500 | $0 | `false` |

---

## 🔑 Campos Clave

### `minimum_payment_amount`
- **Propósito**: Define el monto MÍNIMO que se puede abonar
- **NO es el primer pago**, es el límite inferior
- **Ejemplo**: Si es $50, puedes pagar $50, $100, $150, etc., pero NO $30

### `allows_partial_payment`
- **Propósito**: Indica si la orden acepta abonos
- **Si es `false`**: Solo se puede pagar el monto completo
- **Si es `true`**: Se puede pagar en múltiples abonos

### `is_partially_paid`
- **Propósito**: Indica si la orden tiene pagos incompletos
- **`true`**: Hay al menos un pago pero aún falta saldo
- **`false`**: Sin pagos o completamente pagada

---

## 🚨 Diferencias Clave

| Concepto | Primer Pago | Pagos Subsecuentes |
|----------|-------------|-------------------|
| Crear `Invoice` | ✅ Sí | ❌ No (ya existe) |
| Crear `InvoiceDetail` | ✅ Sí | ✅ Sí |
| Cambiar status orden | `PENDING` → `ACTIVE` | Solo si balance = 0 (`ACTIVE` → `PAID`) |
| Actualizar `balance_due` | ✅ Sí | ✅ Sí |

---

## ✅ Validaciones en Cada Pago

1. **Orden existe y no está cancelada**
2. **Orden está en estado `ACTIVE` o `PENDING`**
3. **Link no ha expirado** (`link_expires_at > now`)
4. **Monto >= minimum_payment_amount**
5. **Monto <= balance_due** (no puede pagar más del saldo)
6. **Método de pago válido**

---

## 📝 Notas Finales

- El **Invoice se crea una sola vez** al primer pago
- Cada pago adicional **solo crea un InvoiceDetail**
- El **balance_due se actualiza** en cada pago
- La orden **pasa a PAID automáticamente** cuando balance = 0
- El campo **`is_partially_paid`** es útil para filtros en el frontend
- El **`minimum_payment_amount`** NO es obligatorio (puede ser `null`)

---

## 🕐 Escenario: Estudiante NO Paga Inmediatamente

### Timeline Completa:

#### **Día 1 - Lunes 10:00 AM**: Asesor crea la orden
```json
POST /api/v1/payment-orders/
{
  "student": 123,
  "allows_partial_payment": true,
  "minimum_payment_amount": 50.00,
  "payment_details": [{"payment_concept": 1, "amount": 500.00}]
}
```

**Estado BD**:
```sql
payment_order: status='PENDING', total_order=500.00
invoices: (vacía, no existe aún)
invoice_details: (vacía)
```

---

#### **Día 1 - Lunes 10:01 AM**: Backend envía email
```python
order.generate_token_and_expiration_date(days_valid=7)
send_payment_link_email(order)
```

**Email enviado** con link: `https://app.com/payment/token123abc`

**Estado BD**: Sin cambios (sigue en PENDING)

---

#### **Día 1-3**: Estudiante ignora el email
- Orden sigue en `PENDING`
- No hay Invoice
- No hay pagos

---

#### **Día 4 - Jueves 3:00 PM**: Estudiante finalmente abre el link

**Frontend consulta**:
```javascript
GET /api/v1/payment-orders/by-token/token123abc/

Response:
{
  "order_number": "PO-00001234",
  "status": "PENDING",
  "total_order": 500.00,
  "total_paid": 0.00,
  "balance_due": 500.00,
  "minimum_payment_amount": 50.00
}
```

**Frontend muestra**:
```
╔══════════════════════════════════╗
║  Total: $500.00                 ║
║  Pagado: $0.00                  ║
║  Saldo: $500.00                 ║
║                                 ║
║  Monto a pagar (min $50):      ║
║  $ [________] 💳               ║  ⬅️ INPUT VACÍO
║                                 ║
║  [ PAGAR ]                      ║
╚══════════════════════════════════╝
```

**Estudiante ingresa**: $150 ⬅️ **AQUÍ decide el monto**

---

#### **Día 4 - Jueves 3:05 PM**: Estudiante hace el pago

**Frontend envía**:
```json
POST /api/v1/payments/process-payment/
{
  "order_number": "PO-00001234",
  "amount": 150.00,  // ⬅️ Monto que ingresó el estudiante
  "payment_method": "TRANSFER",
  "reference_number": "COMP-001"
}
```

**Backend ejecuta**:
```python
# Activa la orden (PENDING → ACTIVE)
order.activate_for_payments()

# CREA Invoice (primera vez)
invoice = Invoice.objects.create(
    payment_order=order,
    total=500.00,
    balance_due=500.00
)

# CREA InvoiceDetail con el $150
InvoiceDetail.objects.create(
    invoice=invoice,
    amount=150.00
)

# Actualiza balance
invoice.balance_due = 350.00
```

**Estado BD**:
```sql
payment_order: status='ACTIVE', total_order=500.00
invoices: id=1, total=500.00, balance_due=350.00
invoice_details: id=1, amount=150.00
```

---

#### **Día 4-10**: Estudiante no paga más
- Orden queda en `ACTIVE`
- Balance pendiente: $350
- Invoice existe pero no está completa

---

#### **Día 11 - Miércoles 5:00 PM**: Estudiante vuelve al link

**Frontend consulta**:
```javascript
GET /api/v1/payment-orders/by-token/token123abc/

Response:
{
  "order_number": "PO-00001234",
  "status": "ACTIVE",
  "total_order": 500.00,
  "total_paid": 150.00,  // ⬅️ Muestra el pago anterior
  "balance_due": 350.00,
  "is_partially_paid": true,
  "payments": [
    {
      "amount": 150.00,
      "payment_date": "2025-05-15",
      "reference_number": "COMP-001"
    }
  ]
}
```

**Frontend muestra**:
```
╔══════════════════════════════════╗
║  Total: $500.00                 ║
║  Pagado: $150.00 ✅             ║
║  Saldo: $350.00 ⚠️              ║
║                                 ║
║  Historial:                     ║
║  • $150 - 15/05 - COMP-001     ║
║                                 ║
║  Monto a pagar (min $50):      ║
║  $ [________] 💳               ║  ⬅️ INPUT VACÍO OTRA VEZ
║                                 ║
║  [ PAGAR ]                      ║
╚══════════════════════════════════╝
```

**Estudiante ingresa**: $200 ⬅️ **DECIDE EL SEGUNDO MONTO**

---

#### **Día 11 - Miércoles 5:10 PM**: Segundo pago

**Frontend envía**:
```json
POST /api/v1/payments/process-payment/
{
  "order_number": "PO-00001234",
  "amount": 200.00,  // ⬅️ Nuevo monto
  "payment_method": "CARD",
  "reference_number": "COMP-002"
}
```

**Backend ejecuta**:
```python
# Obtiene Invoice EXISTENTE (NO crea nuevo)
invoice = order.invoices_payment_order.first()

# CREA nuevo InvoiceDetail
InvoiceDetail.objects.create(
    invoice=invoice,  # ⬅️ Mismo invoice
    amount=200.00
)

# Actualiza balance
invoice.balance_due = 150.00  # 350 - 200
```

**Estado BD**:
```sql
payment_order: status='ACTIVE', total_order=500.00
invoices: id=1, total=500.00, balance_due=150.00
invoice_details: 
  - id=1, amount=150.00
  - id=2, amount=200.00  ⬅️ NUEVO
```

---

### 🔑 Puntos Clave de este Escenario:

1. ✅ **La orden se crea SIN monto de abono**
2. ✅ **El estudiante decide el monto cada vez** que abre el link
3. ✅ **El Invoice se crea SOLO al primer pago** (puede ser días después)
4. ✅ **Cada pago subsecuente usa el mismo Invoice**
5. ✅ **El input siempre está vacío** (el estudiante lo llena cada vez)
6. ✅ **El frontend muestra el historial** de pagos anteriores
7. ✅ **La orden permanece ACTIVE** hasta que balance = 0

