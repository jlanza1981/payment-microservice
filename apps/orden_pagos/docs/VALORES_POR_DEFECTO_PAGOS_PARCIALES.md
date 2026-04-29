# ✅ Valores por Defecto para Pagos Parciales

## 🎯 **Configuración Aplicada**

Los campos de pagos parciales ahora tienen valores por defecto en la base de datos:

### **Antes** ❌
```python
allows_partial_payment = models.BooleanField(default=False)  # Deshabilitado por defecto
minimum_payment_amount = models.DecimalField(..., default=None)  # Sin valor
```

### **Ahora** ✅
```python
allows_partial_payment = models.BooleanField(default=True)  # ⬅️ HABILITADO por defecto
minimum_payment_amount = models.DecimalField(..., default=Decimal('50.00'))  # ⬅️ $50 por defecto
```

---

## 📝 **Request Simplificado desde el Frontend**

### **Antes** (debías enviar todos los campos):
```json
POST /api/v1/payment-orders/

{
  "student": 123,
  "advisor": 456,
  "currency": "USD",
  "opportunity": 789,
  "allows_partial_payment": true,    // ⬅️ Obligatorio
  "minimum_payment_amount": 50.00,   // ⬅️ Obligatorio
  "initial_payment_amount": 1000.00,
  "payment_details": [...]
}
```

### **Ahora** (campos opcionales):
```json
POST /api/v1/payment-orders/

{
  "student": 123,
  "advisor": 456,
  "currency": "USD",
  "opportunity": 789,
  "initial_payment_amount": 1000.00,  // ⬅️ Solo envías el abono inicial
  "payment_details": [...]
}
```

**Resultado**: Se usan los valores por defecto:
- `allows_partial_payment`: `true` ✅
- `minimum_payment_amount`: `50.00` ✅

---

## 🔧 **Casos de Uso**

### **Caso 1: Orden con pagos parciales (valores por defecto)**
```json
{
  "student": 123,
  "advisor": 456,
  "initial_payment_amount": 1000.00,
  // allows_partial_payment y minimum_payment_amount se asignan automáticamente
  "payment_details": [...]
}
```

**Base de datos**:
```sql
allows_partial_payment = true      -- Por defecto
minimum_payment_amount = 50.00     -- Por defecto
initial_payment_amount = 1000.00   -- Enviado
```

---

### **Caso 2: Orden con monto mínimo personalizado**
```json
{
  "student": 123,
  "advisor": 456,
  "minimum_payment_amount": 100.00,  // ⬅️ Personalizado
  "initial_payment_amount": 1000.00,
  "payment_details": [...]
}
```

**Base de datos**:
```sql
allows_partial_payment = true      -- Por defecto
minimum_payment_amount = 100.00    -- Personalizado ✅
initial_payment_amount = 1000.00   -- Enviado
```

---

### **Caso 3: Orden SIN pagos parciales**
```json
{
  "student": 123,
  "advisor": 456,
  "allows_partial_payment": false,  // ⬅️ Explícitamente deshabilitado
  "payment_details": [...]
}
```

**Base de datos**:
```sql
allows_partial_payment = false     -- Explícitamente false
minimum_payment_amount = NULL      -- Se ignora si no hay pagos parciales
initial_payment_amount = NULL      -- No aplica
```

---

### **Caso 4: Orden de pago completo (antigua forma)**
```json
{
  "student": 123,
  "advisor": 456,
  "allows_partial_payment": false,  // Deshabilitar pagos parciales
  "payment_details": [...]
}
```

**Resultado**: Orden debe pagarse completa, sin abonos.

---

## 📊 **Tabla Comparativa**

| Campo | Default Anterior | Default Nuevo | Comportamiento |
|-------|------------------|---------------|----------------|
| `allows_partial_payment` | `False` | **`True`** ✅ | Se habilita automáticamente |
| `minimum_payment_amount` | `NULL` | **`50.00`** ✅ | Monto mínimo por abono |
| `initial_payment_amount` | `NULL` | `NULL` | Debe enviarse desde frontend |

---

## 🎯 **Ventajas**

### ✅ **Frontend más simple**
No necesitas enviar `allows_partial_payment` y `minimum_payment_amount` en cada request.

### ✅ **Consistencia**
Todas las órdenes tendrán los mismos valores por defecto (True y $50).

### ✅ **Retrocompatibilidad**
Si envías los campos explícitamente, se usan tus valores.

---

## 📝 **Migración Requerida**

Después de los cambios, debes crear y aplicar la migración:

```bash
cd /home/jlanza/projects/backend/django/db_manager
python manage.py makemigrations payment_orders -n update_partial_payment_defaults
python manage.py migrate
```

**Migración esperada**:
```python
operations = [
    migrations.AlterField(
        model_name='paymentorder',
        name='allows_partial_payment',
        field=models.BooleanField(default=True, verbose_name='Permite pagos parciales'),
    ),
    migrations.AlterField(
        model_name='paymentorder',
        name='minimum_payment_amount',
        field=models.DecimalField(
            blank=True, 
            decimal_places=2, 
            default=Decimal('50.00'),  # ⬅️ NUEVO DEFAULT
            max_digits=10, 
            null=True, 
            verbose_name='Monto mínimo de abono'
        ),
    ),
    migrations.AddField(
        model_name='paymentorder',
        name='initial_payment_amount',
        field=models.DecimalField(...),
    ),
]
```

---

## ⚠️ **Consideraciones**

### **¿Qué pasa con las órdenes existentes?**

Las órdenes ya creadas mantendrán sus valores actuales:
- Si tenían `allows_partial_payment = False`, seguirán con `False`
- La migración **NO cambia registros existentes**, solo afecta nuevos registros

### **¿Puedo cambiar los defaults después?**

Sí, puedes modificar los valores en cualquier momento:

1. Cambia el `default` en el modelo
2. Crea una nueva migración
3. Aplica la migración

---

## 🔄 **Archivos Modificados**

1. ✅ `db_manager/payment_orders/models.py`
   - `allows_partial_payment`: `default=True`
   - `minimum_payment_amount`: `default=Decimal('50.00')`

2. ✅ `api/apps/orden_pagos/models.py`
   - Mismos cambios

3. ✅ `api/apps/orden_pagos/presentation/api/schemas/input_schemas_payment_order.py`
   - `allows_partial_payment`: `Field(True, ...)`
   - `minimum_payment_amount`: `Field(Decimal('50.00'), ...)`

4. ✅ `api/apps/orden_pagos/application/commands.py`
   - `allows_partial_payment: bool = True`
   - `minimum_payment_amount: Optional[Decimal] = Decimal('50.00')`

5. ✅ `api/apps/orden_pagos/application/use_cases/create_payment_order.py`
   - `getattr(data, 'allows_partial_payment', True)`
   - `getattr(data, 'minimum_payment_amount', Decimal('50.00'))`

---

## 📋 **Resumen Ejecutivo**

| Pregunta | Respuesta |
|----------|-----------|
| **¿Los campos tienen valores por defecto en BD?** | ✅ Sí, ahora tienen |
| **¿Qué valor por defecto tiene `allows_partial_payment`?** | `True` (permite pagos parciales) |
| **¿Qué valor por defecto tiene `minimum_payment_amount`?** | `50.00` (monto mínimo) |
| **¿Debo enviarlos desde el frontend?** | ❌ No, son opcionales |
| **¿Puedo sobreescribirlos?** | ✅ Sí, si los envías explícitamente |
| **¿Necesito migración?** | ✅ Sí, ejecuta `makemigrations` y `migrate` |

---

## ✅ **Conclusión**

Con esta configuración:
- **Por defecto**: Todas las órdenes permiten pagos parciales con mínimo de $50
- **Frontend simplificado**: Solo envías `initial_payment_amount` (el abono inicial)
- **Flexibilidad**: Puedes cambiar los valores si lo necesitas

**La mayoría de los requests serán más cortos y simples.** 🚀

