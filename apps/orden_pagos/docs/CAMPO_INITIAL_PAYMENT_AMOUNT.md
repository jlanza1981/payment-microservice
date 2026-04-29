# ✅ Resumen: Campo `initial_payment_amount` Implementado

## 🎯 **Problema Resuelto**

Basado en las imágenes proporcionadas:

### **Imagen 1** (Formulario de creación):
- Muestra: **"Monto a Pagar: CAD 1,000.00"**
- Este es el **abono inicial sugerido** que el estudiante pagará

### **Imagen 2** (PDF de la orden):
- Muestra: **"TOTAL: CAD 630.00"** (total de la orden)
- **NO mostraba el monto del abono** ($1,000)

### **Solución**:
Se agregó el campo `initial_payment_amount` para guardar ese monto y mostrarlo en el PDF.

---

## 📋 **Cambios Realizados**

### 1️⃣ **Modelo PaymentOrder** (db_manager y api)

**Campo agregado**:
```python
initial_payment_amount = models.DecimalField(
    max_digits=10, 
    decimal_places=2, 
    null=True, 
    blank=True,
    verbose_name=_('Monto del abono inicial'),
    help_text=_('Monto sugerido para el primer pago que se muestra en la orden PDF')
)
```

**Incluido en `get_order_structure()`**:
```python
order_json = {
    # ...existing fields...
    "initial_payment_amount": Decimal(self.initial_payment_amount) if self.initial_payment_amount else None,
    # ...
}
```

---

### 2️⃣ **Schema de Entrada** (`CreatePaymentOrderSchema`)

```python
initial_payment_amount: Optional[Decimal] = Field(
    None, 
    ge=Decimal('0.00'), 
    description="Monto del abono inicial sugerido"
)
```

**Validaciones agregadas**:
- Si hay `initial_payment_amount`, debe ser mayor a 0
- Si hay `minimum_payment_amount`, el inicial debe ser >= al mínimo

---

### 3️⃣ **Command** (`CreatePaymentOrderCommand`)

```python
@dataclass
class CreatePaymentOrderCommand:
    # ...existing fields...
    initial_payment_amount: Optional[Decimal] = None
```

---

### 4️⃣ **Use Case** (`create_payment_order.py`)

```python
order_data_independent = {
    # ...existing fields...
    'initial_payment_amount': getattr(data, 'initial_payment_amount', None),
}
```

---

### 5️⃣ **Schema de Salida** (`PaymentOrderSchema`)

```python
initial_payment_amount: Optional[Decimal] = None
```

**Incluido en `from_orm()`**:
```python
data = {
    # ...existing fields...
    'initial_payment_amount': getattr(obj, 'initial_payment_amount', None),
}
```

---

### 6️⃣ **Template PDF** (`pdf_order_payment.html`)

**Sección agregada después del total**:
```html
<div class="total">
    <span class="text-total">TOTAL:</span>
    <span class="monto">{{ data.currency }} {{ data.total_order }}</span>
</div>

<!-- ✅ NUEVO: Muestra el monto del abono -->
{% if data.allows_partial_payment and data.initial_payment_amount %}
<div class="total" style="margin-top: 1rem; background: #d4edda; color: #155724;">
    <span class="text-total">MONTO A PAGAR:</span>
    <span class="monto">{{ data.currency }} {{ data.initial_payment_amount }}</span>
</div>
{% endif %}
```

**Nota en el footer actualizada**:
```html
{% if data.allows_partial_payment %}
<p><strong>Esta orden permite pagos parciales.</strong>
    {% if data.minimum_payment_amount %}
        Monto mínimo por abono: {{ data.currency }} {{ data.minimum_payment_amount }}.
    {% endif %}
    {% if data.initial_payment_amount %}
        Monto sugerido para el primer pago: {{ data.currency }} {{ data.initial_payment_amount }}.
    {% endif %}
</p>
{% endif %}
```

---

## 📝 **Cómo Usar desde el Frontend**

### **Al crear la orden**:
```json
POST /api/v1/payment-orders/

{
  "student": 123,
  "advisor": 456,
  "currency": "CAD",
  "opportunity": 789,
  "allows_partial_payment": true,
  "minimum_payment_amount": 50.00,      // ⬅️ Monto MÍNIMO por abono
  "initial_payment_amount": 1000.00,    // ⬅️ NUEVO: Monto del abono inicial
  "payment_details": [
    {
      "payment_concept": 1,
      "amount": 2608.00                   // ⬅️ Total de la orden
    }
  ]
}
```

---

## 📄 **PDF Generado**

El PDF ahora mostrará:

```
┌────────────────────────────────────┐
│  ORDEN N° PO-2026-000025          │
│  Cliente: Johanna Lanza            │
│  Email: lanza.johanna@gmail.com    │
├────────────────────────────────────┤
│                                    │
│  DESCRIPCIÓN          SUB TOTAL    │
│  Inscripción          150.00       │
│  Matrícula            480.00       │
│                                    │
│              TOTAL: CAD 630.00     │ ⬅️ Total real
│       MONTO A PAGAR: CAD 1,000.00  │ ⬅️ NUEVO: Abono inicial
│                                    │
├────────────────────────────────────┤
│  NOTA:                             │
│  Esta orden permite pagos parciales│
│  Monto mínimo por abono: CAD 50.00 │
│  Monto sugerido: CAD 1,000.00      │
└────────────────────────────────────┘
```

---

## 🔑 **Diferencia entre los 3 campos**

| Campo | Propósito | Ejemplo |
|-------|-----------|---------|
| `total_order` | Monto total a pagar (suma de conceptos) | $2,608.00 |
| `minimum_payment_amount` | Monto MÍNIMO permitido por abono | $50.00 |
| `initial_payment_amount` | Monto SUGERIDO para el primer abono | $1,000.00 |

### **Ejemplo práctico**:
- **Total de la orden**: $2,608.00
- **Monto mínimo por abono**: $50.00 (no puede pagar menos)
- **Monto inicial sugerido**: $1,000.00 (se muestra en el PDF como "MONTO A PAGAR")

El estudiante puede pagar:
- ✅ $1,000 (el sugerido)
- ✅ $500 (mayor al mínimo)
- ✅ $2,608 (el total completo)
- ❌ $30 (menor al mínimo)

---

## 🎯 **Flujo Completo**

```
1. Asesor crea orden:
   - Total: $2,608
   - Abono inicial: $1,000
   - Mínimo: $50

2. Sistema guarda:
   - PaymentOrder.total_order = 2608
   - PaymentOrder.initial_payment_amount = 1000
   - PaymentOrder.minimum_payment_amount = 50

3. Sistema genera PDF:
   - Muestra TOTAL: $2,608
   - Muestra MONTO A PAGAR: $1,000 ✅

4. PDF se envía al estudiante

5. Estudiante ve en el PDF:
   - Total a pagar: $2,608
   - Primer pago sugerido: $1,000

6. Estudiante hace pago:
   - Puede pagar $1,000 (sugerido)
   - O cualquier monto >= $50
```

---

## ⚠️ **Importante**

### **`initial_payment_amount` es diferente del primer pago real**:

- **`initial_payment_amount`**: Monto SUGERIDO que se muestra en el PDF
- **Primer pago real**: Monto que el estudiante decide pagar (puede ser diferente)

### **Ejemplo**:
```
Orden creada:
- total_order: $2,608
- initial_payment_amount: $1,000 (sugerido)

PDF muestra: "MONTO A PAGAR: $1,000"

Estudiante puede decidir pagar:
- $1,000 (igual al sugerido) ✅
- $1,500 (más del sugerido) ✅
- $500 (menos del sugerido pero >= mínimo) ✅
- $2,608 (pagar todo de una vez) ✅
```

---

## 📋 **Migración Pendiente**

Debes crear y aplicar la migración en `db_manager`:

```bash
cd /home/jlanza/projects/backend/django/db_manager
python manage.py makemigrations payment_orders -n add_initial_payment_amount
python manage.py migrate
```

Esto agregará la columna `initial_payment_amount` a la tabla `payment_orders`.

---

## ✅ **Resultado Final**

Ahora el PDF de la orden mostrará:
- ✅ Total de la orden
- ✅ **Monto del abono inicial** (el campo que faltaba)
- ✅ Nota sobre pagos parciales
- ✅ Monto mínimo por abono

**El PDF coincidirá con lo que el estudiante ve en el formulario de creación.**

