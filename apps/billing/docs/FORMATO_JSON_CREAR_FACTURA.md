# Formato JSON para Crear Facturas

## Estructura de Datos para `CreateInvoiceUseCase.execute(data)`

### JSON Completo (Con todos los campos)

```json
{
  "student": 123,
  "advisor": 456,
  "payment_order": 789,
  "invoice_details": [
    {
      "payment_concept": 1,
      "description": "Matrícula curso de inglés - Nivel B1",
      "quantity": 1,
      "unit_price": 500.00,
      "discount": 50.00
    },
    {
      "payment_concept": 2,
      "description": "Materiales de estudio - Libro + CD",
      "quantity": 2,
      "unit_price": 75.00,
      "discount": 0.00
    }
  ],
  "currency": "USD",
  "taxes": 0.00,
  "notes": "Primera factura del estudiante. Descuento aplicado por pronto pago."
}
```

### JSON Mínimo (Solo campos obligatorios)

```json
{
  "student": 123,
  "advisor": 456,
  "payment_order": 789,
  "invoice_details": [
    {
      "payment_concept": 1,
      "description": "Matrícula",
      "quantity": 1,
      "unit_price": 500.00
    }
  ]
}
```

---

## Descripción de Campos

### Campos Principales (Nivel Root)

| Campo             | Tipo           | Obligatorio | Default | Descripción                                           |
|-------------------|----------------|-------------|---------|-------------------------------------------------------|
| `student`         | `int`          | ✅ Sí        | -       | ID del estudiante (debe existir en la tabla Usuarios) |
| `advisor`         | `int`          | ✅ Sí        | -       | ID del asesor (debe existir en la tabla Usuarios)     |
| `payment_order`   | `int`          | ✅ Sí        | -       | ID de la orden de pago asociada                       |
| `invoice_details` | `List[Object]` | ✅ Sí        | -       | Lista de detalles de la factura (mínimo 1)            |
| `currency`        | `string`       | ❌ No        | `"USD"` | Código de moneda (USD, EUR, COP, etc.)                |
| `taxes`           | `decimal`      | ❌ No        | `0.00`  | Monto de impuestos                                    |
| `notes`           | `string`       | ❌ No        | `null`  | Notas u observaciones adicionales                     |

### Campos de `invoice_details` (Array de Objetos)

| Campo             | Tipo      | Obligatorio | Default | Descripción                            |
|-------------------|-----------|-------------|---------|----------------------------------------|
| `payment_concept` | `int`     | ✅ Sí        | -       | ID del concepto de pago (debe existir) |
| `description`     | `string`  | ✅ Sí        | -       | Descripción detallada del concepto     |
| `quantity`        | `int`     | ✅ Sí        | -       | Cantidad (debe ser > 0)                |
| `unit_price`      | `decimal` | ✅ Sí        | -       | Precio unitario (debe ser > 0)         |
| `discount`        | `decimal` | ❌ No        | `0.00`  | Descuento por línea                    |

---

## Ejemplos de Uso

### Ejemplo 1: Factura Simple (Solo Matrícula)

```json
{
  "student": 15,
  "advisor": 8,
  "payment_order": 1025,
  "invoice_details": [
    {
      "payment_concept": 1,
      "description": "Matrícula programa de inglés",
      "quantity": 1,
      "unit_price": 1200.00
    }
  ]
}
```

**Resultado esperado:**

- Subtotal: $1,200.00
- Taxes: $0.00
- Total: $1,200.00
- Balance Due: $1,200.00
- Status: Emitida (I)

---

### Ejemplo 2: Factura con Múltiples Conceptos

```json
{
  "student": 42,
  "advisor": 12,
  "payment_order": 2048,
  "invoice_details": [
    {
      "payment_concept": 1,
      "description": "Matrícula curso intensivo",
      "quantity": 1,
      "unit_price": 800.00,
      "discount": 100.00
    },
    {
      "payment_concept": 3,
      "description": "Material didáctico",
      "quantity": 1,
      "unit_price": 150.00,
      "discount": 0.00
    },
    {
      "payment_concept": 5,
      "description": "Certificación internacional",
      "quantity": 1,
      "unit_price": 250.00,
      "discount": 0.00
    }
  ],
  "currency": "USD",
  "notes": "Descuento de $100 aplicado por referido"
}
```

**Resultado esperado:**

- Subtotal: (800 - 100) + 150 + 250 = $1,200.00
- Taxes: $0.00
- Total: $1,200.00

---

### Ejemplo 3: Factura con Impuestos

```json
{
  "student": 89,
  "advisor": 5,
  "payment_order": 3072,
  "invoice_details": [
    {
      "payment_concept": 2,
      "description": "Alojamiento 4 semanas",
      "quantity": 4,
      "unit_price": 200.00
    }
  ],
  "currency": "USD",
  "taxes": 80.00,
  "notes": "Incluye IVA del 10%"
}
```

**Resultado esperado:**

- Subtotal: 4 × $200 = $800.00
- Taxes: $80.00
- Total: $880.00

---

### Ejemplo 4: Factura en Otra Moneda

```json
{
  "student": 156,
  "advisor": 23,
  "payment_order": 4096,
  "invoice_details": [
    {
      "payment_concept": 1,
      "description": "Matrícula programa de francés",
      "quantity": 1,
      "unit_price": 450.00
    }
  ],
  "currency": "EUR"
}
```

**Resultado esperado:**

- Total: €450.00
- Currency: EUR

---

## Validaciones que se Realizan

### 1. Validaciones de Existencia

- ✅ `student` existe en la base de datos
- ✅ `advisor` existe en la base de datos
- ✅ `payment_order` existe en la base de datos
- ✅ Cada `payment_concept` existe en la base de datos

### 2. Validaciones de Estado

- ✅ Estudiante está activo (`is_active = True`)
- ✅ Orden de pago no está cancelada
- ✅ Orden de pago no está completamente pagada

### 3. Validaciones de Datos

- ✅ `invoice_details` no está vacío (al menos 1 detalle)
- ✅ `quantity` es mayor a 0
- ✅ `unit_price` es mayor a 0

### 4. Validaciones de Negocio

- ✅ Si un concepto de pago requiere programa, la orden debe tener programa asociado

---

## Errores Comunes

### Error: "El ID del estudiante es obligatorio"

```json
{
  "advisor": 456,
  "payment_order": 789,
  "invoice_details": [
    ...
  ]
}
```

❌ Falta el campo `student`

---

### Error: "Debe proporcionar al menos un detalle de factura"

```json
{
  "student": 123,
  "advisor": 456,
  "payment_order": 789,
  "invoice_details": []
}
```

❌ El array `invoice_details` está vacío

---

### Error: "No se encontró el estudiante con ID 999"

```json
{
  "student": 999,
  "advisor": 456,
  "payment_order": 789,
  "invoice_details": [
    ...
  ]
}
```

❌ El estudiante con ID 999 no existe

---

### Error: "La orden de pago 123 está cancelada"

```json
{
  "student": 123,
  "advisor": 456,
  "payment_order": 123,
  "invoice_details": [
    ...
  ]
}
```

❌ La orden de pago tiene estado CANCELLED

---

### Error: "Cada detalle debe tener una cantidad (quantity)"

```json
{
  "student": 123,
  "advisor": 456,
  "payment_order": 789,
  "invoice_details": [
    {
      "payment_concept": 1,
      "description": "Matrícula",
      "unit_price": 500.00
    }
  ]
}
```

❌ Falta el campo `quantity`

---

## Flujo de Procesamiento

1. **Validar IDs** → Se obtienen las instancias de estudiante, asesor y orden de pago
2. **Validar detalles** → Se verifica que haya al menos un detalle
3. **Validar reglas de negocio** → Se aplican validaciones del dominio
4. **Convertir conceptos** → Se convierten los IDs de conceptos a instancias
5. **Crear factura** → Se crea la factura con estado "Emitida" (I)
6. **Actualizar orden** → Si la orden estaba en PENDING, pasa a ACTIVE

---

## Código Python de Ejemplo

```python
from apps.billing.application.use_cases import CreateInvoiceUseCase
from apps.billing.domain.interface.services import InvoiceDomainService
from apps.billing.infrastructure.repository import InvoiceRepository
from rest_framework.exceptions import ValidationError

# Configurar dependencias
domain_service = InvoiceDomainService()
repository = InvoiceRepository()
use_case = CreateInvoiceUseCase(domain_service, repository)

# Datos de entrada
data = {
    "student": 123,
    "advisor": 456,
    "payment_order": 789,
    "invoice_details": [
        {
            "payment_concept": 1,
            "description": "Matrícula",
            "quantity": 1,
            "unit_price": 500.00,
            "discount": 0.00
        }
    ],
    "currency": "USD",
    "taxes": 0.00,
    "notes": "Primera factura"
}

# Ejecutar
try:
    invoice = use_case.execute(data)
    print(f"✅ Factura creada: {invoice.invoice_number}")
    print(f"   Total: {invoice.total}")
    print(f"   Balance: {invoice.balance_due}")
except ValidationError as e:
    print(f"❌ Error: {e}")
```

---

## Respuesta Esperada (Objeto Invoice)

Después de crear la factura exitosamente, se retorna un objeto `Invoice` con:

```python
{
    "id": 1,
    "invoice_number": "INV-2026-00001",
    "user_id": 123,
    "advisor_id": 456,
    "payment_order_id": 789,
    "subtotal": 500.00,
    "taxes": 0.00,
    "total": 500.00,
    "balance_due": 500.00,
    "status": "I",  # Emitida
    "currency": "USD",
    "notes": "Primera factura",
    "created_at": "2026-01-12T10:30:00Z",
    "updated_at": "2026-01-12T10:30:00Z",
    "details": [
        {
            "id": 1,
            "concept_id": 1,
            "description": "Matrícula",
            "quantity": 1,
            "unit_price": 500.00,
            "discount": 0.00,
            "subtotal": 500.00
        }
    ]
}
```

---

## Notas Importantes

1. **Cálculo Automático**: Los totales se calculan automáticamente en el modelo
2. **Número Automático**: El `invoice_number` se genera automáticamente
3. **Balance Due**: Se inicializa igual al total (sin pagos aplicados)
4. **Estado Inicial**: Siempre se crea con estado "Emitida" (I)
5. **Transacción Atómica**: Si algo falla, no se guarda nada
6. **Orden de Pago**: Se actualiza de PENDING a ACTIVE automáticamente

---

**Última actualización**: 2026-01-12  
**Versión**: 1.0.0

