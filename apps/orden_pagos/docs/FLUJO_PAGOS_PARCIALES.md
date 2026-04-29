# Flujo Completo: Órdenes con Pagos Parciales (Abonos)

## Resumen

Se ha implementado soporte completo para pagos parciales en las órdenes de pago. Los campos agregados son:

- **`allows_partial_payment`** (boolean): Indica si la orden permite pagos parciales
- **`minimum_payment_amount`** (Decimal, opcional): Monto mínimo permitido para cada abono

---

## 1. Crear Orden con Pagos Parciales

### Datos de Entrada (Frontend → Backend)

**Endpoint**: `POST /api/v1/payment-orders/`

```json
{
  "student": 123,
  "advisor": 456,
  "currency": "USD",
  "opportunity": 789,
  "quotation": 101,
  "allows_partial_payment": true,
  "minimum_payment_amount": 50.00,
  "payment_details": [
    {
      "payment_concept": 1,
      "amount": 500.00,
      "quantity": 1,
      "discount_type": "percentage",
      "discount_amount": 10.00
    }
  ],
  "program_data": {
    "program_type": 1,
    "institution": 2,
    "country": "CO",
    "city": 4,
    "program": 5,
    "start_date": "2025-06-01",
    "duration": 12,
    "duration_type": "w",
    "price_week": 100.00
  }
}
```

### Validaciones Automáticas

- ✅ Si `allows_partial_payment = true` y `minimum_payment_amount > 0`, se valida que el monto sea positivo
- ✅ El campo `minimum_payment_amount` es opcional (puede ser `null`)
- ✅ Si no se especifica `allows_partial_payment`, el valor por defecto es `false`

### Flujo Interno

1. **Router** recibe el payload y crea un `CreatePaymentOrderCommand`
2. **CreatePaymentOrderUseCase** procesa el comando:
   - Valida reglas de negocio
   - Prepara datos incluyendo `allows_partial_payment` y `minimum_payment_amount`
   - Detecta si necesita separar órdenes (tipos independientes vs dependientes)
3. **PaymentOrderRepository** crea la orden en la base de datos:
   - Guarda todos los campos incluyendo los de pagos parciales
   - Crea los detalles y programa asociados
   - Calcula el `total_order` automáticamente

### Estado Inicial

- **Status**: `PENDING`
- La orden NO está lista para recibir pagos hasta que se active

---

## 2. Activar Orden para Recibir Pagos

Antes de poder recibir el primer pago, la orden debe activarse.

### Opción A: Activación Manual

```python
from payment_orders.models import PaymentOrder

order = PaymentOrder.objects.get(order_number='PO-00001234')
order.activate_for_payments()  # PENDING → ACTIVE
```

### Opción B: Activación Automática (recomendado)

El método `activate_for_payments()` debe llamarse:
- Después de enviar el enlace de pago al estudiante
- Cuando el estudiante accede al portal de pagos
- Al momento de registrar el primer pago

**Validación**: Solo se puede activar si:
- `status == 'PENDING'`
- `allows_partial_payment == True`

---

## 3. Registrar Primer Pago (Crea Invoice)

### Datos de Entrada

**Endpoint**: `POST /api/v1/invoices/` (o endpoint personalizado para primer pago)

```json
{
  "order_number": "PO-00001234",
  "amount": 150.00,
  "payment_method": "TRANSFER",
  "reference_number": "COMP-123",
  "payment_date": "2025-05-15"
}
```

### Flujo Interno

```python
from payment_orders.models import PaymentOrder, Invoice, InvoiceDetail
from decimal import Decimal

# 1. Obtener la orden
order = PaymentOrder.objects.get(order_number='PO-00001234')

# 2. Validar que puede recibir pagos
if not order.can_receive_payments():
    raise ValidationError("La orden no puede recibir pagos")

# 3. Validar monto
amount = Decimal('150.00')
if order.minimum_payment_amount and amount < order.minimum_payment_amount:
    raise ValidationError(f"Monto mínimo: {order.minimum_payment_amount}")

# 4. CREAR Invoice (primera vez)
invoice = Invoice.objects.create(
    payment_order=order,
    student=order.student,
    total=order.total_order,
    balance_due=order.total_order,
    status='PENDING'
)

# 5. Registrar primer pago
payment = InvoiceDetail.objects.create(
    invoice=invoice,
    payment_method='TRANSFER',
    amount=amount,
    payment_date='2025-05-15',
    reference_number='COMP-123'
)

# 6. Actualizar balance
invoice.balance_due -= amount
invoice.save()

# 7. Si se completó, marcar como pagada
if invoice.balance_due <= 0:
    order.mark_as_paid()  # ACTIVE → PAID
    invoice.status = 'PAID'
    invoice.save()
```

### Resultado

- ✅ Se crea el registro `Invoice` vinculado a la orden
- ✅ Se crea el primer `InvoiceDetail` con el pago
- ✅ La orden permanece en `ACTIVE` (aún tiene saldo pendiente)
- ✅ `invoice.balance_due` = Total - Primer pago

---

## 4. Registrar Segundo y Subsecuentes Pagos

### Datos de Entrada

```json
{
  "order_number": "PO-00001234",
  "amount": 200.00,
  "payment_method": "CARD",
  "reference_number": "COMP-456"
}
```

### Flujo Interno

```python
# 1. Obtener la orden
order = PaymentOrder.objects.get(order_number='PO-00001234')

# 2. Validar que puede recibir pagos
if not order.can_receive_payments():
    raise ValidationError("Orden no disponible para pagos")

# 3. Obtener invoice EXISTENTE
invoice = order.invoices_payment_order.first()
if not invoice:
    raise ValidationError("No existe factura para esta orden")

# 4. Validar monto
amount = Decimal('200.00')
balance = invoice.balance_due

if order.minimum_payment_amount and amount < order.minimum_payment_amount:
    raise ValidationError(f"Monto mínimo: {order.minimum_payment_amount}")

if amount > balance:
    amount = balance  # Ajustar al saldo exacto

# 5. SOLO agregar nuevo InvoiceDetail (NO crear nuevo Invoice)
payment = InvoiceDetail.objects.create(
    invoice=invoice,
    payment_method='CARD',
    amount=amount,
    payment_date=timezone.now(),
    reference_number='COMP-456'
)

# 6. Actualizar balance
invoice.balance_due -= amount
invoice.save()

# 7. Si se completó, marcar como pagada
if invoice.balance_due <= 0:
    order.mark_as_paid()  # ACTIVE → PAID
    invoice.status = 'PAID'
    invoice.save()
```

### Diferencia Clave

| Acción | Primer Pago | Pagos Subsecuentes |
|--------|-------------|-------------------|
| Crear `Invoice` | ✅ Sí | ❌ No (ya existe) |
| Crear `InvoiceDetail` | ✅ Sí | ✅ Sí |
| Actualizar `balance_due` | ✅ Sí | ✅ Sí |
| Cambiar estado orden | Solo si se completa | Solo si se completa |

---

## 5. Estados de la Orden

```
PENDING → activate_for_payments() → ACTIVE
ACTIVE → mark_as_paid() → PAID (cuando balance_due = 0)
PAID → verify() → VERIFIED (verificación por tesorería)
PENDING → cancel() → CANCELLED (solo si no hay pagos)
```

### Métodos Disponibles

```python
# Verificar si puede recibir pagos
order.can_receive_payments()  # True si status == 'ACTIVE'

# Obtener saldo pendiente
balance = order.get_balance_due()  # Delega a invoice.balance_due

# Activar para pagos
order.activate_for_payments()  # PENDING → ACTIVE (solo si allows_partial_payment)

# Marcar como pagada
order.mark_as_paid()  # ACTIVE → PAID (cuando balance = 0)

# Verificar orden
order.verify()  # PAID → VERIFIED

# Anular orden
order.cancel()  # PENDING → CANCELLED
```

---

## 6. Respuesta del API

### Orden Creada

```json
{
  "payment_order": {
    "id": 1234,
    "order_number": "PO-00001234",
    "student": 123,
    "advisor": 456,
    "status": "PENDING",
    "total_order": 500.00,
    "allows_partial_payment": true,
    "minimum_payment_amount": 50.00,
    "payment_order_details": [...],
    "payment_order_program": {...}
  },
  "message": "Orden de pago creada correctamente."
}
```

### Consulta de Saldo

Para obtener el saldo pendiente, consultar la factura asociada:

```python
GET /api/v1/invoices/?payment_order={order_id}

Response:
{
  "invoice_id": 789,
  "total": 500.00,
  "balance_due": 150.00,  # Saldo pendiente
  "payments": [
    {
      "id": 1,
      "amount": 150.00,
      "payment_method": "TRANSFER",
      "payment_date": "2025-05-15",
      "reference_number": "COMP-123"
    },
    {
      "id": 2,
      "amount": 200.00,
      "payment_method": "CARD",
      "payment_date": "2025-05-20",
      "reference_number": "COMP-456"
    }
  ]
}
```

---

## 7. Validaciones Importantes

### En el Backend

1. **Monto mínimo**: Si `minimum_payment_amount` está configurado, cada abono debe ser >= ese monto
2. **Saldo pendiente**: No se puede abonar más del saldo pendiente
3. **Estado de orden**: Solo se pueden registrar pagos si `status == 'ACTIVE'`
4. **Primera factura**: El `Invoice` solo se crea al registrar el primer pago efectivo

### En el Frontend

- Mostrar saldo pendiente antes de cada pago
- Validar que el monto ingresado cumpla con el mínimo
- Deshabilitar pagos si la orden no está en estado `ACTIVE`
- Mostrar histórico de abonos realizados

---

## 8. Ejemplo Completo Paso a Paso

```python
# PASO 1: Crear orden con pagos parciales
order = PaymentOrder.objects.create(
    student_id=123,
    advisor_id=456,
    opportunity_id=789,
    currency='USD',
    allows_partial_payment=True,
    minimum_payment_amount=Decimal('50.00'),
    status='PENDING'
)
PaymentOrderDetails.objects.create(
    payment_order=order,
    payment_concept_id=1,
    amount=Decimal('500.00')
)
# Total orden: $500

# PASO 2: Activar para recibir pagos
order.activate_for_payments()  # Status → ACTIVE

# PASO 3: Primer pago ($150)
invoice = Invoice.objects.create(
    payment_order=order,
    student=order.student,
    total=order.total_order,
    balance_due=order.total_order
)
InvoiceDetail.objects.create(
    invoice=invoice,
    payment_method='TRANSFER',
    amount=Decimal('150.00')
)
invoice.balance_due = Decimal('350.00')
invoice.save()
# Balance pendiente: $350

# PASO 4: Segundo pago ($200)
InvoiceDetail.objects.create(
    invoice=invoice,
    payment_method='CARD',
    amount=Decimal('200.00')
)
invoice.balance_due = Decimal('150.00')
invoice.save()
# Balance pendiente: $150

# PASO 5: Tercer pago ($150) - Completa el pago
InvoiceDetail.objects.create(
    invoice=invoice,
    payment_method='CASH',
    amount=Decimal('150.00')
)
invoice.balance_due = Decimal('0.00')
invoice.status = 'PAID'
invoice.save()

order.mark_as_paid()  # Status → PAID
# Orden completamente pagada
```

---

## Archivos Modificados

1. ✅ `input_schemas_payment_order.py` - Agregados campos en `CreatePaymentOrderSchema`
2. ✅ `commands.py` - Agregados campos en `CreatePaymentOrderCommand`
3. ✅ `create_payment_order.py` - Uso de caso actualizado para incluir campos
4. ✅ `router.py` - Comentario aclaratorio sobre exclusión de campos
5. ✅ `output_schemas_payment_order.py` - Agregados campos en schemas de salida
6. ✅ `payment_order_repository.py` - Ya maneja automáticamente los campos del modelo

---

## Notas Finales

- El modelo `PaymentOrder` en `db_manager` ya tenía los campos implementados
- El flujo de pagos se completa cuando `invoice.balance_due = 0`
- Los pagos NO modifican la orden, solo agregan registros en `InvoiceDetail`
- El `Invoice` actúa como "contenedor" de todos los abonos realizados
- La orden pasa a `PAID` automáticamente cuando se completa el pago total

