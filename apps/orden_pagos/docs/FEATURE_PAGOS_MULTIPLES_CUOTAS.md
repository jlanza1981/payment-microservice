# Feature: Soporte para Múltiples Cuotas en Pagos Parciales

## 📋 Resumen

Se ha implementado el soporte completo para **pagos en múltiples cuotas (4 o más)** en las órdenes de pago, permitiendo que el asesor defina el monto sugerido para cada cuota cuando envía el link de pago.

---

## 🎯 Problema Resuelto

**Antes:**
- El sistema solo soportaba `initial_payment_amount` para el primer pago
- No había forma de especificar el monto del 2do, 3ro, 4to abono, etc.
- El PDF mostraba siempre el mismo monto inicial o el saldo completo
- No se podía reenviar el link de pago para órdenes en estado ACTIVE

**Ahora:**
- El asesor puede especificar el monto de cada cuota al enviar el link
- El PDF muestra claramente el número de cuota (Cuota 1, Cuota 2, Cuota 3, etc.)
- Se puede reenviar el link para órdenes PENDING o ACTIVE
- El PDF muestra el progreso de pagos (cuotas pagadas, total pagado, saldo pendiente)

---

## 🔧 Cambios Implementados

### 1. **Nuevo Campo en el Modelo: `suggested_payment_amount`**

**Ubicación:**
- `db_manager/payment_orders/models.py` (línea ~256)
- `api/apps/orden_pagos/models.py` (línea ~208)

```python
suggested_payment_amount = models.DecimalField(
    max_digits=10, 
    decimal_places=2, 
    null=True, 
    blank=True,
    verbose_name=_('Monto sugerido para el pago'),
    help_text=_('Monto sugerido para el pago actual. Se actualiza cada vez que el asesor envía un link de pago (1ra, 2da, 3ra, 4ta cuota, etc.)')
)
```

**Propósito:**
- Almacena el monto sugerido para **CUALQUIER cuota** (1ra, 2da, 3ra, 4ta...)
- Se actualiza cada vez que el asesor envía un link con un monto específico
- **Reemplaza a `initial_payment_amount` y `next_suggested_payment_amount`** (campo unificado)
- Permite soportar 4+ cuotas de forma flexible

---

### 2. **Nuevos Métodos en PaymentOrder**

**Ubicación:** `api/apps/orden_pagos/models.py` (líneas ~294-327)

#### `get_payment_count() -> int`
Obtiene el número de pagos completados para la orden.

```python
def get_payment_count(self) -> int:
    """
    Obtiene el número de pagos realizados para esta orden.
    Útil para saber en qué cuota se encuentra (1ra, 2da, 3ra, 4ta, etc.)
    """
    invoice = self.invoices_payment_order.first()
    if invoice:
        return invoice.invoice_payment.filter(status='COMPLETED').count()
    return 0
```

#### `get_next_payment_number() -> int`
Obtiene el número del siguiente pago (1, 2, 3, 4...).

```python
def get_next_payment_number(self) -> int:
    """
    Obtiene el número del siguiente pago (para mostrar "Cuota 2", "Cuota 3", etc.)
    """
    return self.get_payment_count() + 1
```

---

### 3. **Actualización de `get_order_structure()`**

**Ubicación:** `api/apps/orden_pagos/models.py` (línea ~402)

Se agregaron los siguientes campos al dict retornado:
```python
"suggested_payment_amount": Decimal(...),  # Campo unificado para todas las cuotas
"payment_count": self.get_payment_count(),
"next_payment_number": self.get_next_payment_number(),
```

---

### 4. **Endpoint Actualizado: `POST /api/v1/payment-orders/by-id/{order_id}/send-payment-link/`**

**Ubicación:** `api/apps/orden_pagos/presentation/api/router.py` (línea ~421)

#### Nuevos Query Parameters:
- `suggested_amount` (opcional): Monto sugerido para el siguiente abono

#### Ejemplo de Uso:

**Primera cuota (sin suggested_amount):**
```bash
POST /api/v1/payment-orders/by-id/123/send-payment-link/
```

**Segunda cuota (con suggested_amount = 1000):**
```bash
POST /api/v1/payment-orders/by-id/123/send-payment-link/?suggested_amount=1000
```

**Tercera cuota (con suggested_amount = 800):**
```bash
POST /api/v1/payment-orders/by-id/123/send-payment-link/?suggested_amount=800
```

#### Validaciones Automáticas:
- ✅ El monto debe ser mayor a 0
- ✅ No puede exceder el saldo pendiente
- ✅ Debe cumplir el monto mínimo si está definido
- ✅ Acepta órdenes en estado PENDING o ACTIVE

#### Respuesta:
```json
{
  "message": "El enlace de pago para la orden PO202400123 está siendo enviado.",
  "order_number": "PO202400123",
  "task_id": "abc-123-def",
  "student_email": "estudiante@example.com",
  "advisor_email": "asesor@example.com",
  "suggested_amount": 1000.00,
  "payment_info": {
    "total_order": 5000.00,
    "total_paid": 2000.00,
    "balance_due": 3000.00,
    "payment_progress_pct": 40.0,
    "payment_count": 2,
    "next_payment_number": 3,
    "is_first_payment": false,
    "allows_partial_payment": true
  }
}
```

---

### 5. **PDF Actualizado**

**Ubicación:** `api/apps/orden_pagos/templates/pdf_order_payment.html`

#### Cambios en la Sección "MONTO A PAGAR":
Ahora muestra dinámicamente:
- **"MONTO CUOTA 2:"** para la segunda cuota
- **"MONTO CUOTA 3:"** para la tercera cuota
- **"MONTO A PAGAR:"** para la primera cuota

```django
<span class="text-total">
    {% if data.next_payment_number and data.next_payment_number > 1 %}
        MONTO CUOTA {{ data.next_payment_number }}:
    {% else %}
        MONTO A PAGAR:
    {% endif %}
</span>
```

#### Cambios en la Sección "NOTA":
Muestra información clara del progreso:

```
NOTA:
La orden N° PO202400123 debe realizarse antes del 20/02/2026.

Esta orden permite pagos parciales (hasta 4 cuotas o más según excepciones).
Monto mínimo por abono: USD 50.00.

PROGRESO DE PAGOS:
• Cuotas pagadas: 2
• Total pagado: USD 2000.00 de USD 5000.00
• Saldo pendiente: USD 3000.00
• Monto sugerido para la Cuota 3: USD 1000.00
```

---

### 6. **Use Case Actualizado: `SendPaymentLinkUseCase`**

**Ubicación:** `api/apps/orden_pagos/application/use_cases/send_payment_link.py` (línea ~42)

Ahora acepta órdenes en estado **PENDING o ACTIVE**:

```python
if payment_order.status not in ['PENDING', 'ACTIVE']:
    raise ValidationError({
        'status': _(f'La orden debe estar en estado PENDING o ACTIVE. Estado actual: {payment_order.status}')
    })
```

---

## 📊 Flujo Completo de Uso

### Escenario: Pago en 4 cuotas de una orden de $5000

#### **Paso 1: Crear la orden y enviar primera cuota**
```bash
POST /api/v1/payment-orders/
{
  "student_id": 123,
  "advisor_id": 5,
  "total_order": 5000.00,
  "allows_partial_payment": true,
  "minimum_payment_amount": 50.00,
  "suggested_payment_amount": 1500.00,  # Monto sugerido para la 1ra cuota
  "payment_details": [...]
}

# Con query param: ?send_payment_link=true
```

**Resultado:**
- ✅ Orden creada en estado PENDING
- ✅ Email enviado al estudiante con PDF mostrando: "MONTO A PAGAR: $1500"
- ✅ Estudiante paga $1500

---

#### **Paso 2: Estudiante paga la primera cuota**
- El estudiante realiza el pago de $1500
- El sistema actualiza la orden a estado **ACTIVE**
- Total pagado: $1500, Saldo pendiente: $3500

---

#### **Paso 3: Asesor envía segunda cuota ($1200)**
```bash
POST /api/v1/payment-orders/by-id/123/send-payment-link/?suggested_amount=1200
```

**Resultado:**
- ✅ Campo `next_suggested_payment_amount` = 1200
- ✅ Email enviado con PDF mostrando: "**MONTO CUOTA 2: $1200**"
- ✅ Nota muestra: "Cuotas pagadas: 1, Total pagado: $1500, Saldo: $3500"

---

#### **Paso 4: Estudiante paga la segunda cuota**
- El estudiante realiza el pago de $1200
- Total pagado: $2700, Saldo pendiente: $2300

---

#### **Paso 5: Asesor envía tercera cuota ($1000)**
```bash
POST /api/v1/payment-orders/by-id/123/send-payment-link/?suggested_amount=1000
```

**Resultado:**
- ✅ Email con PDF: "**MONTO CUOTA 3: $1000**"
- ✅ Nota: "Cuotas pagadas: 2, Total pagado: $2700, Saldo: $2300"

---

#### **Paso 6: Asesor envía cuarta y última cuota ($1300)**
```bash
POST /api/v1/payment-orders/by-id/123/send-payment-link/?suggested_amount=1300
```

**Resultado:**
- ✅ Email con PDF: "**MONTO CUOTA 4: $1300**"
- ✅ Al completar este pago, la orden pasa a estado **PAID**

---

## 🔐 Validaciones Implementadas

1. **Validación de Estado:**
   - Solo PENDING o ACTIVE pueden recibir links de pago
   
2. **Validación de Monto:**
   - `suggested_amount > 0`
   - `suggested_amount <= balance_due`
   - `suggested_amount >= minimum_payment_amount`

3. **Validación de Token:**
   - El link expira según `link_expires_at`
   - Token único por orden

---

## 🗄️ Migración de Base de Datos

**Pendiente de ejecutar:**

```bash
cd /home/jlanza/projects/backend/django/db_manager
python manage.py makemigrations payment_orders --name add_suggested_payment_amount
python manage.py migrate
```

Esto agregará el campo `suggested_payment_amount` a la tabla `payment_order`.

---

## 📝 Notas Importantes

1. **El viewset de DRF (`payment_order_viewset.py`) está DEPRECATED**
   - No se debe usar ni modificar
   - Todo se maneja desde Django Ninja (`router.py`)

2. **El campo `suggested_payment_amount` es único y se sobrescribe**
   - Se usa para TODAS las cuotas (1ra, 2da, 3ra, 4ta...)
   - Cada vez que envías un nuevo link con `suggested_amount`, actualiza este campo
   - No es un historial, solo guarda el último monto sugerido
   - **Simplifica la implementación: UN campo en lugar de dos**

3. **Soporta 4+ cuotas sin límite**
   - El sistema no tiene un límite hardcoded de cuotas
   - Mientras haya saldo pendiente, se puede seguir enviando links

4. **Compatibilidad con sistema actual**
   - Si no se envía `suggested_amount`, funciona como antes
   - El campo es opcional y nullable

---

## 🧪 Testing Recomendado

1. **Crear orden con pago parcial**
2. **Enviar link sin suggested_amount (primera cuota)**
3. **Simular pago de primera cuota**
4. **Enviar link con suggested_amount=1000 (segunda cuota)**
5. **Verificar PDF generado muestra "CUOTA 2"**
6. **Verificar nota muestra progreso correcto**
7. **Repetir para cuota 3 y 4**

---

## 📚 Referencias

- **Router Django Ninja:** `api/apps/orden_pagos/presentation/api/router.py`
- **Modelo PaymentOrder:** `api/apps/orden_pagos/models.py`
- **Template PDF:** `api/apps/orden_pagos/templates/pdf_order_payment.html`
- **Use Case:** `api/apps/orden_pagos/application/use_cases/send_payment_link.py`

---

**Fecha de implementación:** 11 de Febrero de 2026  
**Desarrollador:** GitHub Copilot  
**Estado:** ✅ Completado - Pendiente migración DB

