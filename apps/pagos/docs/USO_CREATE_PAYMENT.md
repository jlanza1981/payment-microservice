# Guía Completa: CreatePaymentUseCase

Esta guía explica en detalle cómo usar el caso de uso `CreatePaymentUseCase` para crear pagos en el sistema LC Mundo.

## 📑 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Inicialización](#inicialización)
3. [Flujo 1: Pago Exonerado](#flujo-1-pago-exonerado)
4. [Flujo 2: Pago Anticipado](#flujo-2-pago-anticipado)
5. [Métodos Disponibles](#métodos-disponibles)
6. [Validaciones](#validaciones)
7. [Manejo de Errores](#manejo-de-errores)
8. [Casos de Uso Completos](#casos-de-uso-completos)

---

## Introducción

El `CreatePaymentUseCase` es el caso de uso principal para crear pagos en el sistema. Soporta dos flujos diferentes:

- **Flujo Exonerado**: El estudiante está exonerado, se crea la factura y luego el pago automático
- **Flujo Pago Anticipado**: El estudiante paga primero, luego se genera la factura

## Inicialización

```python
from apps.pagos.application.use_cases.create_payment_exonerated import CreatePaymentUseCase
from apps.pagos.infrastructure.repository.payment_repository import PaymentRepository
from decimal import Decimal

# Crear instancias
repository = PaymentRepository()
use_case = CreatePaymentUseCase(repository)
```

---

## Flujo 1: Pago Exonerado

### Descripción

El estudiante está exonerado del pago. La orden de pago se crea, seguida de la factura, y finalmente el pago.

### Diagrama

```
[Orden Exonerada] → [Factura] → [Pago Automático (EX)]
                                        ↓
                                  Status: 'V' (Verificado)
```

### Ejemplo Completo

```python
from apps.billing.models import Invoice
from apps.administrador.models import Usuarios
from decimal import Decimal

# 1. Obtener el estudiante y asesor
student = Usuarios.objects.get(id=123)
advisor = Usuarios.objects.get(id=456)

# 2. Crear la factura (asumiendo que ya existe)
invoice = Invoice.objects.get(id=789)

# 3. Crear pago exonerado usando el método de conveniencia
payment = use_case.create_exonerated_payment(
    invoice=invoice,
    user=student,
    advisor=advisor,
    amount=Decimal('1500.00'),
    currency='USD',
    notes='Estudiante exonerado por beca completa'
)

# Resultado:
# - payment.payment_method = 'EX'
# - payment.status = 'V' (Verificado automáticamente)
# - payment.verification_date = fecha actual
# - payment.invoice = factura asociada
```

### Método Alternativo (Usando execute)

```python
# Crear pago exonerado usando execute() directamente
payment = use_case.execute(
    payment_data={
        'invoice': invoice,
        'user': student,
        'advisor': advisor,
        'amount': Decimal('1500.00'),
        'payment_method': 'EX',
        'status': 'V',
        'currency': 'USD',
        'payer_name': student.get_full_name(),
        'payment_terms_conditions': True
    }
)
```

### Con Asignaciones de Pago

```python
# Crear pago exonerado con allocations
allocations = [
    {
        'invoice_detail_id': 1,
        'payment_concept_id': 10,
        'amount_applied': Decimal('1000.00'),
        'status': 'EXONERATED'
    },
    {
        'invoice_detail_id': 2,
        'payment_concept_id': 20,
        'amount_applied': Decimal('500.00'),
        'status': 'EXONERATED'
    }
]

payment = use_case.execute(
    payment_data={
        'invoice': invoice,
        'user': student,
        'advisor': advisor,
        'amount': Decimal('1500.00'),
        'payment_method': 'EX',
        'status': 'V',
        'currency': 'USD'
    },
    allocations=allocations
)
```

---

## Flujo 2: Pago Anticipado

### Descripción

El estudiante realiza el pago ANTES de que se genere la factura. El pago se registra sin factura (`invoice=None`) y
posteriormente se asocia.

### Diagrama

```
[Orden de Pago] → [Pago del Estudiante] → [Factura] → [Asociación]
                          ↓                                ↓
                    invoice = None                  invoice = X
                    Status: 'D' o 'P'               Status: 'V'
```

### Paso 1: Crear Pago Sin Factura

```python
# Estudiante realiza pago por PayPal
payment = use_case.create_advance_payment(
    user=student,
    advisor=advisor,
    amount=Decimal('500.00'),
    payment_method='PP',  # PayPal
    payment_reference_number='PAYPAL-TXN-123456',
    currency='USD',
    status='D'  # Disponible (ya verificado por PayPal)
)

# Resultado:
# - payment.invoice = None  (Sin factura aún)
# - payment.payment_number = 'PAY-00001'
# - payment.status = 'D'
# - payment.payment_reference_number = 'PAYPAL-TXN-123456'
```

### Paso 2: Generar Factura

```python
from apps.billing.application.use_cases.create_invoice import CreateInvoiceUseCase

# Crear factura para la orden de pago
invoice = create_invoice_use_case.execute(
    invoice_data={
        'user': student,
        'advisor': advisor,
        'payment_order': payment_order,
        'status': 'I',  # Emitida
        'currency': 'USD'
    },
    invoice_details=[
        {
            'payment_concept_id': 10,
            'description': 'Matrícula',
            'quantity': 1,
            'unit_price': Decimal('500.00')
        }
    ]
)
```

### Paso 3: Asociar Factura al Pago

```python
# Asociar la factura al pago anticipado
allocations = [
    {
        'invoice_detail_id': invoice.details.first().id,
        'payment_concept_id': 10,
        'amount_applied': Decimal('500.00'),
        'status': 'PAID'
    }
]

updated_payment = use_case.associate_invoice_to_payment(
    payment_id=payment.id,
    invoice_id=invoice.id,
    allocations=allocations
)

# Resultado:
# - updated_payment.invoice = invoice
# - Factura actualiza su balance_due
# - Si balance_due = 0, factura.status = 'P' (Pagada)
```

### Método Alternativo: Todo en Uno

```python
# Si prefieres hacerlo manualmente con execute()
payment = use_case.execute(
    payment_data={
        'invoice': None,  # SIN FACTURA
        'user': student,
        'advisor': advisor,
        'amount': Decimal('500.00'),
        'payment_method': 'ST',  # Stripe
        'payment_reference_number': 'ch_1234567890',
        'currency': 'USD',
        'status': 'P',  # Pendiente verificación
        'payer_name': 'Juan Pérez'
    }
)

# Luego actualizar con factura
payment = repository.update(
    payment_id=payment.id,
    payment_data={
        'invoice_id': invoice.id,
        'status': 'V',  # Verificar el pago
        'verification_date': timezone.now().date(),
        'allocations': allocations
    }
)
```

---

## Métodos Disponibles

### 1. `execute(payment_data, allocations, create_invoice_callback)`

**Método principal** que detecta automáticamente el flujo según si viene o no la factura.

```python
payment = use_case.execute(
    payment_data={
        'invoice': invoice_or_none,  # None = flujo anticipado
        'user': user,
        'advisor': advisor,
        'amount': amount,
        'payment_method': method,
        'currency': 'USD',
        'status': status
    },
    allocations=[...]  # Opcional
)
```

**Parámetros:**

- `payment_data` (Dict): Datos del pago (ver estructura abajo)
- `allocations` (List[Dict], opcional): Asignaciones de pago
- `create_invoice_callback` (callable, opcional): Callback para crear factura

**Retorna:** `Payment` instance

---

### 2. `create_exonerated_payment(...)`

Método de **conveniencia** para crear pagos exonerados.

```python
payment = use_case.create_exonerated_payment(
    invoice=invoice,
    user=student,
    advisor=advisor,
    amount=Decimal('1500.00'),
    currency='USD',
    notes='Beca completa'
)
```

**Parámetros:**

- `invoice`: Instancia de Invoice
- `user`: Usuario/Estudiante
- `advisor`: Asesor
- `amount`: Monto exonerado (Decimal)
- `currency`: Moneda (default: 'USD')
- `notes`: Notas adicionales (default: '')

**Retorna:** `Payment` con status='V' y payment_method='EX'

---

### 3. `create_advance_payment(...)`

Método de **conveniencia** para pagos anticipados (sin factura).

```python
payment = use_case.create_advance_payment(
    user=student,
    advisor=advisor,
    amount=Decimal('500.00'),
    payment_method='PP',
    payment_reference_number='PAYPAL-123',
    currency='USD',
    status='D'
)
```

**Parámetros:**

- `user`: Usuario/Estudiante
- `advisor`: Asesor
- `amount`: Monto del pago (Decimal)
- `payment_method`: Método ('PP', 'ST', 'TC', etc.)
- `payment_reference_number`: Número de transacción (opcional)
- `currency`: Moneda (default: 'USD')
- `status`: Estado inicial (default: 'D')

**Retorna:** `Payment` con invoice=None

---

### 4. `associate_invoice_to_payment(...)`

Asocia una factura a un pago sin factura.

```python
payment = use_case.associate_invoice_to_payment(
    payment_id=payment.id,
    invoice_id=invoice.id,
    allocations=[...]
)
```

**Parámetros:**

- `payment_id`: ID del pago sin factura
- `invoice_id`: ID de la factura a asociar
- `allocations`: Lista de asignaciones (opcional)

**Retorna:** `Payment` actualizado

**Excepciones:**

- `ValueError`: Si el pago ya tiene factura
- `ValueError`: Si el pago está anulado

---

## Validaciones

### Validaciones Automáticas

El caso de uso valida automáticamente:

1. **Campos Requeridos**
    - `user`: Usuario obligatorio
    - `amount`: Monto obligatorio y > 0
    - `payment_method`: Método válido
    - `currency`: Moneda válida

2. **Método de Pago**
    - Debe ser uno de: PP, ST, TC, TD, BT, EF, CH, EX, OT

3. **Monto**
    - Debe ser mayor a 0
    - Debe ser un número válido (Decimal)

4. **Estado**
    - Si payment_method='EX', status se establece a 'V' automáticamente

### Ejemplo de Validación

```python
try:
    payment = use_case.execute({
        'user': None,  # ❌ Error: user requerido
        'amount': Decimal('-100'),  # ❌ Error: monto debe ser > 0
        'payment_method': 'INVALID',  # ❌ Error: método inválido
        'currency': 'USD'
    })
except ValueError as e:
    print(f"Error de validación: {e}")
```

---

## Manejo de Errores

### Errores Comunes

#### 1. Campos Faltantes

```python
# ❌ Error
payment = use_case.execute({'amount': 100})
# ValueError: Campo requerido faltante: user

# ✅ Correcto
payment = use_case.execute({
    'user': student,
    'amount': Decimal('100.00'),
    'payment_method': 'PP',
    'currency': 'USD'
})
```

#### 2. Monto Inválido

```python
# ❌ Error
payment = use_case.execute({
    'user': student,
    'amount': Decimal('0'),  # Monto = 0
    'payment_method': 'PP',
    'currency': 'USD'
})
# ValueError: El monto debe ser mayor a 0
```

#### 3. Método de Pago Inválido

```python
# ❌ Error
payment = use_case.execute({
    'user': student,
    'amount': Decimal('100'),
    'payment_method': 'BITCOIN',  # No válido
    'currency': 'USD'
})
# ValueError: Método de pago inválido
```

#### 4. Asociar Factura a Pago que ya tiene Factura

```python
# ❌ Error
payment = use_case.associate_invoice_to_payment(
    payment_id=payment_with_invoice.id,  # Ya tiene factura
    invoice_id=another_invoice.id
)
# ValueError: El pago PAY-00001 ya tiene factura asociada
```

### Try-Except Recomendado

```python
from django.db import transaction

try:
    with transaction.atomic():
        payment = use_case.execute(payment_data)
        # Otras operaciones...
except ValueError as e:
    logger.error(f"Error de validación: {e}")
    # Manejar error de validación
except Exception as e:
    logger.error(f"Error inesperado: {e}", exc_info=True)
    # Manejar error general
```

---

## Casos de Uso Completos

### Caso 1: Orden Exonerada Completa

```python
from decimal import Decimal
from apps.orden_pagos.models import PaymentOrder
from apps.billing.models import Invoice
from apps.pagos.application.use_cases.create_payment_exonerated import CreatePaymentUseCase

# 1. Crear orden exonerada
order = PaymentOrder.objects.create(
    student=student,
    advisor=advisor,
    status='EXONERATED',
    total_order=Decimal('2000.00')
)

# 2. Agregar conceptos
order_details = PaymentOrderDetails.objects.create(
    payment_order=order,
    payment_concept=concept_matricula,
    quantity=1,
    unit_price=Decimal('2000.00')
)

# 3. Crear factura
invoice = Invoice.objects.create(
    user=student,
    advisor=advisor,
    payment_order=order,
    status='E',  # Exonerada
    subtotal=Decimal('2000.00'),
    total=Decimal('2000.00'),
    currency='USD'
)

# 4. Crear pago exonerado
payment = use_case.create_exonerated_payment(
    invoice=invoice,
    user=student,
    advisor=advisor,
    amount=Decimal('2000.00')
)

print(f"Pago exonerado: {payment.payment_number}")
print(f"Estado: {payment.get_status_display()}")  # Verificado
```

### Caso 2: Pago Anticipado con PayPal

```python
# 1. Estudiante paga por PayPal
paypal_response = {
    'transaction_id': 'PAYPAL-TXN-987654',
    'amount': 500.00,
    'currency': 'USD',
    'status': 'COMPLETED'
}

# 2. Registrar pago anticipado
payment = use_case.create_advance_payment(
    user=student,
    advisor=advisor,
    amount=Decimal(str(paypal_response['amount'])),
    payment_method='PP',
    payment_reference_number=paypal_response['transaction_id'],
    currency=paypal_response['currency'],
    status='D'  # Disponible (PayPal ya verificó)
)

print(f"Pago anticipado registrado: {payment.payment_number}")
print(f"Referencia: {payment.payment_reference_number}")

# 3. Más tarde, crear factura
invoice = create_invoice_for_order(order, student)

# 4. Asociar factura al pago
payment = use_case.associate_invoice_to_payment(
    payment_id=payment.id,
    invoice_id=invoice.id,
    allocations=[
        {
            'invoice_detail_id': invoice.details.first().id,
            'payment_concept_id': concept.id,
            'amount_applied': Decimal('500.00'),
            'status': 'PAID'
        }
    ]
)

print(f"Factura {invoice.invoice_number} asociada a {payment.payment_number}")
```

### Caso 3: Pago Parcial con Múltiples Allocations

```python
# Pago parcial de una factura con múltiples conceptos
allocations = [
    {
        'invoice_detail_id': detail1.id,
        'payment_concept_id': concept_matricula.id,
        'amount_applied': Decimal('300.00'),
        'status': 'PAID'
    },
    {
        'invoice_detail_id': detail2.id,
        'payment_concept_id': concept_mensualidad.id,
        'amount_applied': Decimal('200.00'),
        'status': 'PAID'
    }
]

payment = use_case.execute(
    payment_data={
        'invoice': invoice,
        'user': student,
        'advisor': advisor,
        'amount': Decimal('500.00'),  # Total del pago
        'payment_method': 'BT',  # Transferencia bancaria
        'currency': 'USD',
        'status': 'P'  # Pendiente verificación
    },
    allocations=allocations
)

# Balance de factura se actualiza automáticamente
invoice.refresh_from_db()
print(f"Balance pendiente: ${invoice.balance_due}")
```

---

## 📊 Estructura de Datos

### payment_data (Dict)

```python
{
    'invoice': Invoice | None,  # Factura (None para pago anticipado)
    'user': Usuarios,           # Usuario/Estudiante
    'advisor': Usuarios | None, # Asesor (opcional)
    'amount': Decimal,          # Monto del pago
    'payment_method': str,      # PP, ST, TC, TD, BT, EF, CH, EX, OT
    'payment_reference_number': str | None,  # Referencia de transacción
    'currency': str,            # USD, EUR, etc.
    'status': str,              # P, D, V, R, X
    'payer_name': str,          # Nombre del pagador (auto si no se provee)
    'payment_terms_conditions': bool,  # Default: True
    'payment_date': datetime | None,   # Default: now()
}
```

### allocations (List[Dict])

```python
[
    {
        'invoice_detail_id': int,      # ID del detalle de factura
        'payment_concept_id': int,     # ID del concepto
        'amount_applied': Decimal,     # Monto aplicado
        'status': str                  # PAID, PENDING, EXONERATED
    },
    # ... más allocations
]
```

---

## 🔍 Tips y Mejores Prácticas

### 1. Usar Transacciones Atómicas

```python
from django.db import transaction

with transaction.atomic():
    payment = use_case.execute(payment_data)
    # Otras operaciones relacionadas
```

### 2. Logging

```python
import logging
logger = logging.getLogger(__name__)

try:
    payment = use_case.execute(payment_data)
    logger.info(f"Pago creado: {payment.payment_number}")
except Exception as e:
    logger.error(f"Error creando pago: {e}", exc_info=True)
```

### 3. Validar Balance de Factura

```python
if payment.invoice:
    payment.invoice.refresh_from_db()
    if payment.invoice.balance_due <= 0:
        logger.info(f"Factura {payment.invoice.invoice_number} pagada completamente")
```

### 4. Usar Métodos de Conveniencia

```python
# ✅ Mejor: Usar método específico
payment = use_case.create_exonerated_payment(...)

# ⚠️ Funcional pero más verbose
payment = use_case.execute({
    'payment_method': 'EX',
    'status': 'V',
    # ... más campos
})
```

---

## 📝 Notas Finales

- Todos los métodos usan transacciones atómicas
- Los logs se escriben en nivel INFO para operaciones exitosas
- Los errores se registran en nivel ERROR con traceback completo
- El número de pago se genera automáticamente (PAY-XXXXX)
- Para pagos exonerados, el estado se establece automáticamente a 'V'

---

**Versión:** 1.0  
**Última actualización:** 2026-01-12  
**Autor:** Sistema LC Mundo
