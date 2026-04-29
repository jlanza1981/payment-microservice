# Endpoints de Payment Structures (Estructuras de Pago)

## Descripción

Este módulo proporciona endpoints para consultar las estructuras de pago dinámicas definidas en el sistema. Las
estructuras de pago determinan qué campos se deben mostrar en los formularios según el tipo de pago (concepto)
seleccionado.

## Arquitectura

La implementación sigue el patrón de arquitectura limpia utilizado en el módulo de `payment_concepts`:

```
presentation/api/
  └── payment_structure_router.py      # Endpoints REST
application/use_cases/
  └── get_payment_structures.py        # Casos de uso
infrastructure/repository/
  └── payment_structure_repository.py  # Acceso a datos
```

## Endpoints Disponibles

### 1. Obtener todas las estructuras

```http
GET /api/v1/payment-orders/payment-structures/
Authorization: Bearer <token>
```

**Descripción:** Obtiene todas las estructuras de pago activas con sus campos.

**Respuesta 200:**

```json
[
  {
    "id": 1,
    "payment_type": {
      "id": 1,
      "code": "I",
      "name": "Inscripción"
    },
    "has_discount": true,
    "notes": "Estructura para inscripción de estudiantes",
    "is_active": true,
    "fields": [
      {
        "id": 1,
        "name": "precio",
        "label": "Precio de Inscripción",
        "field_type": "number",
        "choices": null,
        "required": true,
        "readonly": false,
        "order": 1,
        "default_value": "50",
        "active": true
      },
      {
        "id": 2,
        "name": "descuento_pct",
        "label": "Descuento (%)",
        "field_type": "number",
        "choices": null,
        "required": false,
        "readonly": false,
        "order": 2,
        "default_value": "0",
        "active": true
      }
    ]
  }
]
```

---

### 2. Obtener estructura por ID

```http
GET /api/v1/payment-orders/payment-structures/by-id/{structure_id}/
Authorization: Bearer <token>
```

**Parámetros:**

- `structure_id` (int): ID de la estructura de pago

**Respuesta 200:**

```json
{
  "id": 1,
  "payment_type": {
    "id": 1,
    "code": "I",
    "name": "Inscripción"
  },
  "has_discount": true,
  "notes": "Estructura para inscripción",
  "is_active": true,
  "fields": [
    ...
  ]
}
```

**Respuesta 404:**

```json
{
  "error": "Estructura de pago con ID 999 no encontrada"
}
```

---

### 3. Obtener estructura por tipo de pago (Concepto)

```http
GET /api/v1/payment-orders/payment-structures/by-payment-type/{payment_type_id}/
Authorization: Bearer <token>
```

**Parámetros:**

- `payment_type_id` (int): ID del concepto de pago (PaymentConcept)

**Caso de uso:** Este endpoint es el más importante para el frontend. Cuando el usuario selecciona un tipo de pago en el
formulario, este endpoint retorna qué campos dinámicos se deben mostrar.

**Ejemplo:**

```http
GET /api/v1/payment-orders/payment-structures/by-payment-type/1/
```

**Respuesta 200:**

```json
{
  "id": 1,
  "payment_type": {
    "id": 1,
    "code": "I",
    "name": "Inscripción"
  },
  "has_discount": true,
  "notes": "Estructura para inscripción de estudiantes",
  "is_active": true,
  "fields": [
    {
      "id": 1,
      "name": "precio",
      "label": "Precio de Inscripción",
      "field_type": "number",
      "choices": null,
      "required": true,
      "readonly": false,
      "order": 1,
      "default_value": "50",
      "active": true
    },
    {
      "id": 2,
      "name": "descuento_pct",
      "label": "Descuento (%)",
      "field_type": "number",
      "choices": null,
      "required": false,
      "readonly": false,
      "order": 2,
      "default_value": "0",
      "active": true
    }
  ]
}
```

**Respuesta 404:**

```json
{
  "error": "No existe estructura de pago para el tipo de pago con ID 999"
}
```

---

### 4. Obtener estructuras por múltiples tipos de pago

```http
POST /api/v1/payment-orders/payment-structures/by-payment-types/
Authorization: Bearer <token>
Content-Type: application/json
```

**Body:**

```json
[
  1,
  2,
  3
]
```

**Caso de uso:** Cuando necesitas cargar estructuras para varios conceptos de pago a la vez (ej: un formulario con
múltiples tipos de pago seleccionados).

**Respuesta 200:**

```json
[
  {
    "id": 1,
    "payment_type": {
      "id": 1,
      "code": "I",
      "name": "Inscripción"
    },
    "has_discount": true,
    "is_active": true,
    "fields": [
      ...
    ]
  },
  {
    "id": 2,
    "payment_type": {
      "id": 2,
      "code": "M",
      "name": "Matrícula"
    },
    "has_discount": false,
    "is_active": true,
    "fields": [
      ...
    ]
  }
]
```

---

## Modelos Relacionados

### PaymentStructure

Define la estructura general de un tipo de pago:

- `payment_type`: Relación con PaymentConcept
- `has_discount`: Indica si permite descuentos
- `notes`: Notas adicionales
- `is_active`: Si está activa

### PaymentStructureFields

Define los campos dinámicos de cada estructura:

- `name`: Nombre técnico del campo (ej: "precio", "descuento_pct")
- `label`: Etiqueta visible (ej: "Precio", "Descuento (%)")
- `field_type`: Tipo de campo (text, number, select, checkbox, etc.)
- `choices`: Opciones disponibles (para select, radio, etc.)
- `required`: Si es obligatorio
- `readonly`: Si es solo lectura
- `order`: Orden de visualización
- `default_value`: Valor por defecto
- `active`: Si está activo

## Tipos de Campo Soportados

```python
FIELD_TYPES = [
    ('text', 'Texto'),
    ('hidden', 'Oculto'),
    ('div', 'Div'),
    ('number', 'Número'),
    ('select', 'Select'),
    ('readonly', 'Solo Lectura'),
    ('radio', 'Radio'),
    ('checkbox', 'Checkbox'),
]
```

## Casos de Uso

### Ejemplo 1: Formulario Dinámico

Cuando el usuario selecciona "Inscripción" como tipo de pago:

1. Frontend hace request:
   ```http
   GET /api/v1/payment-orders/payment-structures/by-payment-type/1/
   ```

2. Backend retorna los campos que debe mostrar el formulario

3. Frontend renderiza dinámicamente:
    - Input de tipo "number" para "Precio de Inscripción"
    - Input de tipo "number" para "Descuento (%)"
    - Etc.

### Ejemplo 2: Validación de Formulario

El frontend puede usar la información de `required`, `field_type`, y `choices` para:

- Validar campos obligatorios
- Validar tipos de datos
- Mostrar opciones de select/radio

### Ejemplo 3: Valores por Defecto

Al cargar el formulario, el frontend puede usar `default_value` para pre-llenar campos.

## Optimización

El repositorio utiliza `select_related` y `prefetch_related` para optimizar las consultas:

```python
PaymentStructure.objects.filter(is_active=True)
.select_related('payment_type', 'payment_type__category')
.prefetch_related(
    Prefetch(
        'structure_section_payment_structure',
        queryset=PaymentStructureFields.objects.filter(active=True).order_by('order')
    )
)
```

Esto evita el problema N+1 y carga todos los datos relacionados en una sola consulta eficiente.

## Testing

Para probar los endpoints:

```bash
# Obtener todas las estructuras
curl -X GET "http://localhost:8000/api/v1/payment-orders/payment-structures/" \
  -H "Authorization: Bearer <token>"

# Obtener estructura por ID
curl -X GET "http://localhost:8000/api/v1/payment-orders/payment-structures/by-id/1/" \
  -H "Authorization: Bearer <token>"

# Obtener estructura por tipo de pago
curl -X GET "http://localhost:8000/api/v1/payment-orders/payment-structures/by-payment-type/1/" \
  -H "Authorization: Bearer <token>"

# Obtener múltiples estructuras
curl -X POST "http://localhost:8000/api/v1/payment-orders/payment-structures/by-payment-types/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d "[1, 2, 3]"
```

## Integración con Frontend

### React/Vue Ejemplo

```javascript
// Cargar estructura cuando cambia el tipo de pago
async function loadPaymentStructure(paymentTypeId) {
    const response = await fetch(
        `/api/v1/payment-orders/payment-structures/by-payment-type/${paymentTypeId}/`,
        {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        }
    );

    const structure = await response.json();

    // Renderizar campos dinámicamente
    structure.fields.forEach(field => {
        renderField(field);
    });
}

function renderField(field) {
    switch (field.field_type) {
        case 'number':
            return `<input type="number" name="${field.name}" 
              required="${field.required}" 
              value="${field.default_value}" 
              placeholder="${field.label}" />`;
        case 'select':
            // Usar field.choices para opciones
            return `<select name="${field.name}">...</select>`;
        // etc.
    }
}
```

## Notas Importantes

1. **Autenticación requerida:** Todos los endpoints requieren token de autenticación válido

2. **Solo estructuras activas:** Los endpoints solo retornan estructuras con `is_active=True`

3. **Campos ordenados:** Los campos se retornan ordenados por el campo `order`

4. **Campos activos:** Solo se incluyen campos con `active=True`

5. **Relaciones optimizadas:** Las consultas están optimizadas para evitar múltiples queries a la BD

