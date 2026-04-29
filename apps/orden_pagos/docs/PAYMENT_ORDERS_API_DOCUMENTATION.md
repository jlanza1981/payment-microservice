# API de Órdenes de Pago - Documentación

## Descripción General

Sistema de gestión de órdenes de pago que permite crear, actualizar, consultar y gestionar órdenes asociadas a
estudiantes, asesores, oportunidades y cotizaciones.

---

## Endpoints

### 1. Listar Órdenes de Pago (Con Paginación)

**GET** `/api/v1/payment-orders/`

Lista todas las órdenes de pago con filtros opcionales y paginación.

#### Query Parameters

**Paginación:**

- `page` (int, opcional): Número de página (default: 1)
- `per_page` (int, opcional): Items por página (default: 10)

**Filtros:**

- `status` (string, opcional): Filtrar por estado de la orden
    - Valores: `PENDING`, `PAID`, `CANCELLED`, `PARTIALLY_PAID`
- `student_id` (int, opcional): ID del estudiante
- `advisor_id` (int, opcional): ID del asesor
- `opportunity_id` (int, opcional): ID de la oportunidad
- `quotation_id` (int, opcional): ID de la cotización
- `date_from` (date, opcional): Fecha desde (formato: YYYY-MM-DD)
- `date_to` (date, opcional): Fecha hasta (formato: YYYY-MM-DD)

#### Ejemplos de Uso

**Ejemplo 1: Listar todas las órdenes (primera página, 10 items)**

```http
GET /api/v1/payment-orders/
```

**Ejemplo 2: Página 2 con 20 items por página**

```http
GET /api/v1/payment-orders/?page=2&per_page=20
```

**Ejemplo 3: Filtrar por estado PAID**

```http
GET /api/v1/payment-orders/?status=PAID
```

**Ejemplo 4: Filtrar por estudiante con paginación**

```http
GET /api/v1/payment-orders/?student_id=123&page=1&per_page=15
```

**Ejemplo 5: Filtrar por rango de fechas y asesor**

```http
GET /api/v1/payment-orders/?advisor_id=5&date_from=2024-01-01&date_to=2024-12-31&per_page=25
```

**Ejemplo 6: Múltiples filtros con paginación**

```http
GET /api/v1/payment-orders/?status=PENDING&advisor_id=10&opportunity_id=50&page=1&per_page=10
```

#### Response

```json
{
  "count": 150,
  "next": "http://localhost:8000/api/v1/payment-orders/?status=PENDING&page=2&per_page=10",
  "previous": null,
  "results": [
    {
      "id": 1,
      "order_number": "OP202400001",
      "student": {
        "id": 123,
        "first_name": "Juan",
        "last_name": "Pérez"
      },
      "advisor": {
        "id": 5,
        "first_name": "María",
        "last_name": "García"
      },
      "status": "PENDING",
      "total_order": "1500.00",
      "created_at": "2024-11-26T10:30:00Z",
      "updated_at": "2024-11-26T10:30:00Z"
    },
    {
      "id": 2,
      "order_number": "OP202400002",
      "student": {
        "id": 124,
        "first_name": "Ana",
        "last_name": "López"
      },
      "advisor": {
        "id": 5,
        "first_name": "María",
        "last_name": "García"
      },
      "status": "PAID",
      "total_order": "2000.00",
      "created_at": "2024-11-25T15:20:00Z",
      "updated_at": "2024-11-26T09:00:00Z"
    }
  ]
}
```

#### Estructura de la Respuesta Paginada

- **count** (int): Total de registros que cumplen los filtros
- **next** (string|null): URL de la siguiente página (null si es la última página)
- **previous** (string|null): URL de la página anterior (null si es la primera página)
- **results** (array): Array con los resultados de la página actual

---

### 2. Obtener Orden de Pago Específica

**GET** `/api/v1/payment-orders/{id}/`

Obtiene los detalles completos de una orden de pago específica.

#### Response

```json
{
  "id": 1,
  "order_number": "OP202400001",
  "student": {
    "id": 123,
    "first_name": "Juan",
    "last_name": "Pérez",
    "email": "juan.perez@example.com"
  },
  "advisor": {
    "id": 5,
    "first_name": "María",
    "last_name": "García"
  },
  "opportunity": {
    "id": 50,
    "name": "Oportunidad 2024"
  },
  "quotation": {
    "id": 100,
    "quotation_number": "COT202400050"
  },
  "status": "PENDING",
  "total_order": "1500.00",
  "payment_order_file": "https://example.com/files/orden_pago_1.pdf",
  "payment_link_date": "2024-11-30",
  "created_at": "2024-11-26T10:30:00Z",
  "updated_at": "2024-11-26T10:30:00Z",
  "payment_details": [
    {
      "id": 1,
      "payment_type": {
        "id": 1,
        "name": "Transferencia Bancaria"
      },
      "amount": "1000.00",
      "discount_type": "percentage",
      "discount_amount": "10.00"
    }
  ],
  "program_data": {
    "id": 1,
    "program_type": {
      "id": 1,
      "name": "Curso de Inglés"
    },
    "institution": {
      "id": 1,
      "name": "Language Institute"
    },
    "country": {
      "id": 1,
      "name": "Canadá"
    },
    "city": {
      "id": 1,
      "name": "Toronto"
    },
    "start_date": "2024-01-15",
    "duration": 12,
    "duration_type": "w",
    "price_week": "100.00"
  }
}
```

---

### 3. Crear Orden de Pago

**POST** `/api/v1/payment-orders/`

Crea una nueva orden de pago.

#### Request Body

```json
{
  "student_id": 123,
  "advisor_id": 5,
  "opportunity_id": 50,
  "quotation_id": 100,
  "total_order": "1500.00",
  "payment_details": [
    {
      "payment_type_id": 1,
      "amount": "1000.00",
      "discount_type": "percentage",
      "discount_amount": "10.00"
    }
  ],
  "program_data": {
    "program_type_id": 1,
    "institution_id": 1,
    "country_id": 1,
    "city_id": 1,
    "start_date": "2024-01-15",
    "duration": 12,
    "duration_type": "w",
    "price_week": "100.00"
  }
}
```

#### Response

```json
{
  "id": 1,
  "order_number": "OP202400001",
  "status": "PENDING",
  ...
}
```

Status: `201 Created`

---

### 4. Actualizar Orden de Pago

**PUT** `/api/v1/payment-orders/{id}/`

Actualiza una orden de pago completa (reemplaza todos los campos).

**PATCH** `/api/v1/payment-orders/{id}/`

Actualiza parcialmente una orden de pago (solo campos enviados).

---

### 5. Eliminar Orden de Pago

**DELETE** `/api/v1/payment-orders/{id}/`

Elimina una orden de pago. Solo permite eliminar órdenes en estado `PENDING`.

#### Response

```json
{
  "message": "Orden de pago eliminada correctamente"
}
```

Status: `204 No Content`

---

### 6. Buscar por Número de Orden

**GET** `/api/v1/payment-orders/by-number/{order_number}/`

Busca una orden de pago por su número de orden.

#### Ejemplo

```http
GET /api/v1/payment-orders/by-number/OP202400001/
```

---

### 7. Cambiar Estado de Orden

**POST** `/api/v1/payment-orders/{id}/change-status/`

Cambia el estado de una orden de pago.

#### Request Body

```json
{
  "new_status": "PAID"
}
```

#### Valores permitidos para new_status

- `PENDING`
- `PAID`
- `CANCELLED`
- `PARTIALLY_PAID`

---

### 8. Crear/Actualizar Orden y Enviar Enlace (Todo en Uno)

**POST** `/api/v1/payment-orders/create-and-send/`

**⭐ ENDPOINT RECOMENDADO PARA EL FRONTEND**

Endpoint optimizado que crea o actualiza una orden de pago y envía el enlace automáticamente en una sola llamada.
Ideal para evitar múltiples llamadas HTTP desde el frontend.

#### Request Body

```json
{
  "order_id": null,
  "send_password": false,
  "new_password": "contraseña_temporal",
  "order_data": {
    "student_id": 123,
    "advisor_id": 5,
    "opportunity_id": 50,
    "quotation_id": 25,
    "payment_details": [
      {
        "payment_type_id": 1,
        "amount": 1000.00,
        "discount_type": "percentage",
        "discount_amount": 10.00
      }
    ],
    "payment_program": {
      "program_type_id": 1,
      "institution_id": 10,
      "country_id": 5,
      "city_id": 15,
      "program_id": 20,
      "start_date": "2025-01-15",
      "duration": 12,
      "duration_type": "w",
      "price_week": 250.00
    }
  }
}
```

#### Parámetros

- `order_id` (integer, nullable): ID de la orden a actualizar. Si es `null`, se crea una nueva orden
- `send_password` (boolean, opcional): Indica si se debe incluir la contraseña en el correo. Default: `false`
- `new_password` (string, opcional): Nueva contraseña a enviar al estudiante
- `order_data` (object, requerido): Datos de la orden de pago (misma estructura que CREATE o UPDATE)

#### Response Success - Orden Creada (201)

```json
{
  "id": 1,
  "order_number": "OP202400001",
  "student": {
    "id": 123,
    "nombre": "Juan",
    "apellido": "Pérez",
    "email": "juan.perez@example.com"
  },
  "advisor": {
    "id": 5,
    "nombre": "María",
    "apellido": "García",
    "email": "maria.garcia@lcmundo.com"
  },
  "status": "PENDING",
  "total_order": "3500.00",
  "payment_link_date": "2025-11-28",
  "message": "Orden creada y enlace de pago enviado",
  "payment_link_sent": true,
  "payment_link_task_id": "abc123-def456",
  "student_email": "juan.perez@example.com",
  "advisor_email": "maria.garcia@lcmundo.com"
}
```

#### Response Success - Orden Actualizada (200)

```json
{
  "id": 1,
  "order_number": "OP202400001",
  "message": "Orden actualizada y enlace de pago enviado",
  "payment_link_sent": true,
  "payment_link_task_id": "def456-ghi789",
  "student_email": "juan.perez@example.com",
  "advisor_email": "maria.garcia@lcmundo.com"
}
```

#### Ejemplo con cURL

```bash
# Crear nueva orden y enviar enlace
curl -X POST "http://localhost:8000/api/v1/payment-orders/create-and-send/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": null,
    "send_password": true,
    "new_password": "Temporal2025!",
    "order_data": {
      "student_id": 123,
      "advisor_id": 5,
      "payment_details": [{
        "payment_type_id": 1,
        "amount": 1000.00
      }]
    }
  }'
```

#### Ventajas

- ✅ **Una sola llamada HTTP** en lugar de dos
- ✅ **Más rápido** - Menos latencia de red
- ✅ **Más confiable** - Transacción atómica
- ✅ **Menos código** en el frontend
- ✅ **Mejor experiencia de usuario**

---

### 9. Enviar Enlace de Pago (Solo Envío)

**POST** `/api/v1/payment-orders/{id}/send-payment-link/`

Envía el enlace de pago al estudiante y al asesor por correo electrónico con un PDF adjunto de la orden de pago.
Solo se puede enviar para órdenes en estado PENDING.

#### Request Body (Opcional)

```json
{
  "send_password": false,
  "new_password": "contraseña_temporal"
}
```

#### Parámetros

- `send_password` (boolean, opcional): Indica si se debe incluir la contraseña en el correo. Default: `false`
- `new_password` (string, opcional): Nueva contraseña a enviar al estudiante (requerido si `send_password` es `true`)

#### Ejemplo 1: Enviar enlace sin contraseña

```bash
curl -X POST "http://localhost:8000/api/v1/payment-orders/1/send-payment-link/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

#### Ejemplo 2: Enviar enlace con contraseña

```bash
curl -X POST "http://localhost:8000/api/v1/payment-orders/1/send-payment-link/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "send_password": true,
    "new_password": "temporal123"
  }'
```

#### Response Success (200)

```json
{
  "message": "El enlace de pago para la orden OP202400001 está siendo enviado.",
  "order_number": "OP202400001",
  "task_id": "abc123-def456-ghi789",
  "student_email": "estudiante@example.com",
  "advisor_email": "asesor@example.com"
}
```

#### Response Error - Estado Inválido (400)

```json
{
  "error": "Solo se puede enviar el enlace de pago para órdenes en estado PENDING. Estado actual: PAID"
}
```

#### Response Error - Validación (400)

```json
{
  "new_password": [
    "Debe proporcionar una contraseña si \"send_password\" es True"
  ]
}
```

#### Funcionalidades

- Genera un PDF con el detalle completo de la orden de pago
- Envía correo al estudiante con:
    - Enlace de pago
    - PDF adjunto de la orden
    - Credenciales de acceso (si se solicita)
- Envía correo al asesor con:
    - Copia del enlace de pago
    - PDF adjunto de la orden
- Actualiza la fecha de envío del enlace (`payment_link_date`)
- Proceso asíncrono mediante Celery

#### Notas

- El enlace de pago se genera automáticamente según la configuración del sistema
- El envío se realiza de forma asíncrona para no bloquear la respuesta
- Se puede rastrear el estado del envío usando el `task_id` retornado
- El PDF incluye todos los conceptos de pago, descuentos e información del programa

---

## Notas sobre Paginación

1. **URLs de navegación**: Las URLs `next` y `previous` incluyen automáticamente todos los filtros aplicados
2. **Límites**: Puedes ajustar `per_page` según tus necesidades (recomendado: entre 10 y 100)
3. **Performance**: La paginación mejora el rendimiento al no cargar todos los registros de una vez
4. **Filtros persistentes**: Los filtros se mantienen al navegar entre páginas

## Ejemplos con cURL

```bash
# Listar primera página con 10 items
curl -X GET "http://localhost:8000/api/v1/payment-orders/?page=1&per_page=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Filtrar por estado y paginar
curl -X GET "http://localhost:8000/api/v1/payment-orders/?status=PAID&page=1&per_page=20" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Múltiples filtros
curl -X GET "http://localhost:8000/api/v1/payment-orders/?student_id=123&date_from=2024-01-01&date_to=2024-12-31&page=1&per_page=15" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Ejemplos con JavaScript (Fetch)

```javascript
// Función para obtener órdenes de pago con paginación
async function getPaymentOrders(page = 1, perPage = 10, filters = {}) {
    const params = new URLSearchParams({
        page,
        per_page: perPage,
        ...filters
    });

    const response = await fetch(`/api/v1/payment-orders/?${params}`, {
        headers: {
            'Authorization': 'Bearer YOUR_TOKEN',
            'Content-Type': 'application/json'
        }
    });

    return await response.json();
}

// Uso
const result = await getPaymentOrders(1, 20, {
    status: 'PAID',
    advisor_id: 5
});

console.log(`Total: ${result.count}`);
console.log(`Resultados:`, result.results);
console.log(`Siguiente página: ${result.next}`);
```

## Ejemplos con Python (requests)

```python
import requests


def get_payment_orders(page=1, per_page=10, **filters):
    params = {
        'page': page,
        'per_page': per_page,
        **filters
    }

    response = requests.get(
        'http://localhost:8000/api/v1/payment-orders/',
        params=params,
        headers={'Authorization': 'Bearer YOUR_TOKEN'}
    )

    return response.json()


# Uso
result = get_payment_orders(
    page=1,
    per_page=20,
    status='PAID',
    advisor_id=5
)

print(f"Total: {result['count']}")
print(f"Resultados: {len(result['results'])}")
print(f"Siguiente página: {result['next']}")
```

