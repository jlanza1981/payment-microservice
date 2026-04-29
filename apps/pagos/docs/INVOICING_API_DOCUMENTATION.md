# Invoicing API Documentation

## Descripción General

Este sistema de facturación permite emitir facturas para programas de idiomas y educación superior, con o sin una cotización previa. El proceso permite:

- Registrar y facturar ventas derivadas de cotizaciones
- Registrar y facturar ventas directas sin necesidad de una cotización
- Asociar pagos a una factura (no directamente a la inscripción o cotización)
- Gestionar pagos por cuotas y extensiones

## Modelos

### Invoice (Factura)
- Numeración automática: `INV-{año}-{número}`
- Estados: Draft (D), Issued (I), Partially Paid (PP), Paid (P), Cancelled (C)
- Tipos de venta: Con cotización (Q), Venta directa (D)
- Calcula automáticamente totales y saldo pendiente

### InvoiceDetail (Detalle de Factura)
- Conceptos: Administrative Cost, Registration Fee, Tuition, Extension, Booking Fee, Accommodation, Material, Insurance, Transfer, Others
- Calcula subtotales automáticamente

### Payment (Pago)
- 23 tipos de pago (manteniendo compatibilidad con PagosEnLinea)
- Estados: Pending (P), Available (D), Assigned (A), Verified (V), Rejected (R), Cancelled (X)
- Relaciones ManyToMany con extensiones y abonos
- Actualiza automáticamente el saldo de la factura al verificarse

---

## Endpoints - Facturas (Invoices)

### 1. Listar Facturas
**GET** `/api/v1/invoices/`

Lista todas las facturas con opciones de filtrado.

**Query Parameters:**
- `user` (int): Filtrar por ID de estudiante
- `advisor` (int): Filtrar por ID de asesor
- `status` (string): Filtrar por estado (D, I, PP, P, C)
- `sale_type` (string): Filtrar por tipo de venta (Q, D)
- `quotation` (int): Filtrar por ID de cotización
- `enrollment_form` (int): Filtrar por ID de planilla
- `from_date` (date): Fecha desde (formato: YYYY-MM-DD)
- `to_date` (date): Fecha hasta (formato: YYYY-MM-DD)
- `invoice_number` (string): Buscar por número de factura

**Response:**
```json
[
  {
    "id": 1,
    "invoice_number": "INV-2025-000001",
    "issue_date": "2025-10-31T10:30:00Z",
    "due_date": "2025-11-30",
    "student_name": "Juan Pérez",
    "student_email": "juan@email.com",
    "advisor_name": "María González",
    "sale_type": "Q",
    "sale_type_display": "Sale with Quotation",
    "subtotal": "5000.00",
    "total_discounts": "500.00",
    "taxes": "0.00",
    "total": "4500.00",
    "balance_due": "2500.00",
    "currency": "USD",
    "status": "PP",
    "status_display": "Partially Paid",
    "total_paid": "2000.00",
    "payment_percentage": 44.44,
    "details": [...],
    "payments": [...]
  }
]
```

---

### 2. Ver Detalle de Factura
**GET** `/api/v1/invoices/{id}/`

Obtiene el detalle completo de una factura.

**Response:** Igual que el listado, pero un solo objeto.

---

### 3. Crear Factura
**POST** `/api/v1/invoices/create/`

Crea una nueva factura con sus líneas de detalle.

**Request Body:**
```json
{
  "user": 123,
  "advisor": 45,
  "quotation": 67,
  "enrollment_form": null,
  "sale_type": "Q",
  "due_date": "2025-11-30",
  "currency": "USD",
  "notes": "Factura para programa de inglés",
  "details": [
    {
      "concept": "CA",
      "description": "Costo Administrativo LC",
      "quantity": 1,
      "unit_price": "150.00",
      "discount": "0.00"
    },
    {
      "concept": "IN",
      "description": "Inscripción al programa",
      "quantity": 1,
      "unit_price": "200.00",
      "discount": "20.00"
    },
    {
      "concept": "MA",
      "description": "Matrícula 12 semanas",
      "quantity": 12,
      "unit_price": "350.00",
      "discount": "0.00"
    }
  ]
}
```

**Response:**
```json
{
  "s": "s",
  "invoice": { ...factura completa... },
  "msj": "Invoice created successfully"
}
```

**Validation Errors:**
- Si `sale_type` es "Q", `quotation` es requerido
- Todos los montos deben ser >= 0
- Debe incluir al menos un item en `details`

---

### 4. Actualizar Factura
**PUT** `/api/v1/invoices/{invoice_id}/update/`

Actualiza una factura existente (solo si está en estado Draft o Issued).

**Request Body:** Campos parciales de la factura que se desean actualizar.

**Response:**
```json
{
  "s": "s",
  "invoice": { ...factura actualizada... },
  "msj": "Invoice updated successfully"
}
```

**Restricciones:**
- No se puede editar facturas con estado "Paid" (P) o "Cancelled" (C)

---

### 5. Emitir Factura
**POST** `/api/v1/invoices/{invoice_id}/issue/`

Cambia el estado de una factura de "Draft" a "Issued".

**Response:**
```json
{
  "s": "s",
  "invoice": { ...factura emitida... },
  "msj": "Invoice issued successfully"
}
```

**Validaciones:**
- Solo se pueden emitir facturas en estado "Draft"
- La factura debe tener al menos una línea de detalle

---

### 6. Anular Factura
**POST** `/api/v1/invoices/{invoice_id}/cancel/`

Anula una factura.

**Response:**
```json
{
  "s": "s",
  "invoice": { ...factura anulada... },
  "msj": "Invoice cancelled successfully"
}
```

**Restricciones:**
- No se puede anular una factura que ya está cancelada
- No se puede anular una factura con pagos verificados

---

### 7. Agregar Línea a Factura
**POST** `/api/v1/invoices/{invoice_id}/add-detail/`

Agrega una nueva línea de detalle a una factura existente.

**Request Body:**
```json
{
  "concept": "EX",
  "description": "Extensión 4 semanas adicionales",
  "quantity": 4,
  "unit_price": "350.00",
  "discount": "50.00",
  "quotation_course": 89
}
```

**Response:**
```json
{
  "s": "s",
  "detail": { ...detalle creado... },
  "invoice": { ...factura actualizada con nuevos totales... },
  "msj": "Line item added successfully"
}
```

**Restricciones:**
- No se pueden agregar líneas a facturas Paid o Cancelled

---

### 8. Estadísticas de Facturas
**GET** `/api/v1/invoices/stats/`

Obtiene estadísticas generales de facturación.

**Query Parameters:**
- `user` (int, opcional): Filtrar por estudiante
- `advisor` (int, opcional): Filtrar por asesor

**Response:**
```json
{
  "s": "s",
  "stats": {
    "total_invoices": 150,
    "draft_invoices": 10,
    "issued_invoices": 50,
    "partially_paid_invoices": 30,
    "paid_invoices": 55,
    "cancelled_invoices": 5,
    "total_amount": "675000.00",
    "total_balance_due": "125000.00",
    "total_paid": "550000.00"
  }
}
```

---

## Endpoints - Pagos (Payments)

### 1. Listar Pagos
**GET** `/api/v1/payments/`

Lista todos los pagos con opciones de filtrado.

**Query Parameters:**
- `invoice` (int): Filtrar por ID de factura
- `user` (int): Filtrar por ID de usuario
- `verified` (boolean): Filtrar por pagos verificados (true/false)
- `status` (string): Filtrar por estado (P, D, A, V, R, X)
- `payment_method` (string): Filtrar por método de pago (PP, TC, TD, TF, EF, CH, OT)

**Response:**
```json
[
  {
    "id": 1,
    "payment_number": "PAY-2025-000001",
    "invoice": 15,
    "payment_type": "C",
    "payment_type_display": "Administrative Cost",
    "payment_date": "2025-10-31T14:25:00Z",
    "verification_date": "2025-11-01",
    "payment_method": "PP",
    "payment_method_display": "PayPal",
    "external_transaction_id": "PAYID-XXXXXXXXXXXXXXXX",
    "user": 123,
    "user_email": "juan@email.com",
    "user_name": "Juan Pérez",
    "amount": "150.00",
    "currency": "USD",
    "status": "V",
    "status_display": "Verified",
    "verified": true,
    "payer_name": "Juan Pérez García",
    "advisor_reference": 45,
    "advisor_email": "maria@lcmundo.com",
    "advisor_name": "María González",
    "notes": null,
    "created_at": "2025-10-31T14:25:00Z",
    "updated_at": "2025-11-01T09:00:00Z"
  }
]
```

---

### 2. Registrar Pago
**POST** `/api/v1/payments/create/`

Registra un nuevo pago asociado a una factura.

**Request Body:**
```json
{
  "invoice": 15,
  "payment_type": "M",
  "payment_method": "PP",
  "external_transaction_id": "PAYID-XXXXXXXXXXXXXXXX",
  "user": 123,
  "amount": "4200.00",
  "currency": "USD",
  "payer_name": "Juan Pérez García",
  "advisor_reference": 45,
  "extensions": [],
  "down_payments": [],
  "terms_accepted": true,
  "notes": "Pago de matrícula completa"
}
```

**Response:**
```json
{
  "s": "s",
  "payment": { ...pago registrado... },
  "invoice": { ...factura con saldo actualizado... },
  "msj": "Payment registered successfully"
}
```

**Validaciones:**
- `amount` debe ser mayor a 0
- `amount` no puede exceder el `balance_due` de la factura
- No se puede agregar pago a factura cancelada
- `external_transaction_id` es requerido

**Nota:** Si el usuario tiene permiso `website.verify_payment`, el pago se verifica automáticamente.

---

### 3. Verificar Pago
**POST** `/api/v1/payments/{payment_id}/verify/`

Verifica un pago pendiente.

**Response:**
```json
{
  "s": "s",
  "payment": { ...pago verificado... },
  "invoice": { ...factura con saldo actualizado... },
  "msj": "Payment verified successfully"
}
```

**Restricciones:**
- No se puede verificar un pago ya verificado
- No se puede verificar un pago rechazado

---

## Tipos de Pago (Payment Types)

Los siguientes tipos de pago están disponibles (compatibilidad con el sistema actual):

| Código | Descripción |
|--------|-------------|
| C | Costo Administrativo |
| I | Inscripción |
| A | Costo Administrativo e Inscripción |
| E | Extensión de Matrícula |
| M | Matrícula |
| B | Inscripción y Matrícula |
| T | Costo Administrativo, Inscripción y Matrícula |
| P | Abono de Matrícula |
| F | Inscripción con Abono de Matrícula |
| G | Costo e Inscripción con Abono de Matrícula |
| N | Abono de Adicionales |
| O | Todo Excepto Costo |
| K | Registro de HomeStay |
| J | Inscripción y Registro de HomeStay |
| L | Costo, Inscripción, Matrícula y Registro de HomeStay |
| R | Inscripción, Matrícula y Registro de HomeStay |
| S | Matrícula y Registro de HomeStay |
| U | Adicionales completos |
| D | Pago Total |
| W | Inscripción, Matrícula, Booking Fee y adicionales |
| V | Abono de Matrícula y adicionales |
| Z | Costo con Abono de Matrícula |

---

## Conceptos de Factura (Invoice Concepts)

| Código | Descripción |
|--------|-------------|
| CA | Administrative Cost |
| IN | Registration Fee |
| MA | Tuition |
| EX | Tuition Extension |
| BF | Booking Fee |
| HS | Home Stay / Accommodation |
| MT | Educational Material |
| SE | Insurance |
| TR | Transfer |
| OT | Other Services |

---

## Estados de Factura (Invoice Statuses)

| Código | Descripción | Descripción en inglés |
|--------|-------------|----------------------|
| D | Borrador | Draft |
| I | Emitida | Issued |
| PP | Pagada Parcialmente | Partially Paid |
| P | Pagada | Paid |
| C | Anulada | Cancelled |

---

## Estados de Pago (Payment Statuses)

| Código | Descripción | Descripción en inglés |
|--------|-------------|----------------------|
| P | Pendiente | Pending |
| D | Disponible | Available |
| A | Asignado a Cotización | Assigned to Quotation |
| V | Verificado | Verified |
| R | Rechazado | Rejected |
| X | Cancelado | Cancelled |

---

## Flujo de Trabajo Recomendado

### Escenario 1: Venta con Cotización

1. **Crear Factura** desde cotización:
   ```
   POST /api/v1/invoices/create/
   ```
   - Incluir `quotation` ID
   - `sale_type = "Q"`
   - Agregar líneas de detalle basadas en la cotización

2. **Emitir Factura**:
   ```
   POST /api/v1/invoices/{id}/issue/
   ```

3. **Estudiante realiza pago**:
   ```
   POST /api/v1/payments/create/
   ```

4. **Verificar pago** (si no se auto-verificó):
   ```
   POST /api/v1/payments/{payment_id}/verify/
   ```

5. El sistema actualiza automáticamente el saldo de la factura

---

### Escenario 2: Venta Directa (sin cotización)

1. **Crear Factura** directa:
   ```
   POST /api/v1/invoices/create/
   ```
   - `quotation = null`
   - `sale_type = "D"`
   - Puede incluir `enrollment_form` si existe planilla

2. Seguir pasos 2-5 del escenario anterior

---

### Escenario 3: Pago por Cuotas

1. Crear factura con el total del programa
2. Estudiante realiza primer pago (abono):
   ```
   POST /api/v1/payments/create/
   {
     "payment_type": "P",
     "amount": "1000.00",
     ...
   }
   ```
3. Estado de factura cambia a "Partially Paid" (PP)
4. Estudiante realiza pagos subsiguientes
5. Cuando `balance_due` llega a 0, estado cambia a "Paid" (P)

---

## Autenticación

Todos los endpoints requieren autenticación mediante token:

```
Authorization: Token {your-token-here}
```

---

## Formato de Respuestas

### Éxito
```json
{
  "s": "s",
  "data": {...},
  "msj": "Success message"
}
```

### Error
```json
{
  "s": "n",
  "errors": {...},
  "msj": "Error message"
}
```

---

## Notas Importantes

1. **Numeración Automática**: Los números de factura y pago se generan automáticamente al crear el registro
2. **Cálculos Automáticos**: Los subtotales, totales y saldos se calculan automáticamente
3. **Integridad de Datos**: No se puede eliminar una factura con pagos verificados
4. **Transacciones**: Todas las operaciones críticas usan transacciones atómicas
5. **Migraciones**: Este sistema coexiste con el sistema anterior, no requiere migración inmediata de datos
6. **Compatibilidad**: Los 23 tipos de pago del sistema anterior se mantienen para compatibilidad

---

## Próximas Funcionalidades (Pendientes)

- [ ] Envío automático de correos al emitir factura
- [ ] Envío automático de correos al verificar pago
- [ ] Generación de PDF de facturas
- [ ] Integración con generadores de PDF existentes
- [ ] Webhooks para notificaciones de pago
- [ ] Panel de estadísticas avanzadas