# Endpoint de Pagos Exonerados

## Descripción

El endpoint de pagos exonerados permite registrar órdenes de pago gratuitas (sin costo) en el sistema, creando el
asiento contable completo sin generar links de pago ni enviar notificaciones por email.

## Ubicación

```
POST /api/v1/payment-orders/exonerated/
```

## Casos de Uso

1. **Becas completas**: Estudiantes con beca del 100%
2. **Exoneraciones institucionales**: Convenios especiales
3. **Cortesías**: Casos especiales aprobados por dirección
4. **Registro de servicios gratuitos**: Eventos, actividades sin costo

## Autenticación

Requiere token de autenticación mediante `AuthBearer`.

## Request

### Para Orden Nueva

```json
{
  "student_id": 123,
  "concepts": [
    {
      "concept_id": 1,
      "quantity": 1
    },
    {
      "concept_id": 5,
      "quantity": 2
    }
  ],
  "payer_name": "Juan Pérez",
  "advisor_id": 5,
  "notes": "Beca completa 2026 - Convenio Universidad XYZ"
}
```

### Para Orden Existente

```json
{
  "order_payment_id": 456,
  "payer_name": "María García",
  "advisor_id": 3,
  "notes": "Exoneración por convenio institucional"
}
```

## Parámetros

### Obligatorios

- **payer_name** (string): Nombre del pagador/beneficiario

### Para Orden Nueva

- **student_id** (integer): ID del estudiante
- **concepts** (array): Lista de conceptos de pago
    - **concept_id** (integer): ID del concepto de pago
    - **quantity** (integer, default=1): Cantidad del concepto

### Para Orden Existente

- **order_payment_id** (integer): ID de la orden existente

### Opcionales

- **advisor_id** (integer): ID del asesor que procesa la exoneración
- **notes** (string): Notas adicionales sobre la exoneración

## Response

### Success (201 Created)

```json
{
  "success": true,
  "message": "Pago exonerado registrado exitosamente",
  "data": {
    "order_payment_id": 789,
    "order_number": "PO-000789",
    "invoice_id": 456,
    "invoice_number": "INV-000456",
    "payment_id": 321,
    "payment_number": "PAY-000321",
    "amount": "0.00"
  }
}
```

### Error Responses

#### 400 Bad Request

```json
{
  "detail": "Esta orden ya está pagada"
}
```

```json
{
  "detail": "Debe proporcionar 'order_payment_id' para orden existente o 'student_id' y 'concepts' para orden nueva"
}
```

#### 404 Not Found

```json
{
  "detail": "Estudiante no encontrado"
}
```

```json
{
  "detail": "Asesor no encontrado"
}
```

```json
{
  "detail": "Concepto {id} no encontrado"
}
```

```json
{
  "detail": "Orden de pago no encontrada"
}
```

#### 500 Internal Server Error

```json
{
  "detail": "Error al procesar pago exonerado: {detalle del error}"
}
```

## Flujo del Proceso

1. **Validación de entrada**: Verifica que se proporcione orden existente O datos para crear nueva
2. **Obtener/Crear orden**:
    - Si hay `order_payment_id`: Valida que no esté pagada y actualiza total a $0
    - Si hay `student_id` y `concepts`: Crea nueva orden con conceptos en $0
3. **Crear/Actualizar factura**: Genera factura con todos los conceptos en $0
4. **Registrar pago**: Crea registro de pago con método 'EX' (Exonerated) y status 'V' (Verificado)
5. **Asignar pagos**: Crea asignaciones por cada concepto con monto $0
6. **Actualizar estado**: Marca la orden como 'PAID'

## Características Importantes

✅ **Transaccional**: Todo el proceso se ejecuta en una transacción atómica

✅ **Sin notificaciones**: No envía emails ni genera links de pago

✅ **Registro completo**: Crea todos los registros contables necesarios

✅ **Validaciones**: Verifica existencia de estudiantes, asesores y conceptos

✅ **Estado inmediato**: El pago se marca como verificado ('V') automáticamente

## Método de Pago

El endpoint utiliza el método de pago **'EX' (Exonerated)** que debe estar configurado en el modelo `Payment`:

```python
PAYMENT_METHODS = (
    ...
    ('EX', _('Exonerated')),
    ...
)
```

## Ejemplos de Uso

### Ejemplo 1: Beca Completa

```bash
curl -X POST "http://localhost:8000/api/v1/payment-orders/exonerated/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": 123,
    "concepts": [
      {"concept_id": 1, "quantity": 1},
      {"concept_id": 2, "quantity": 1}
    ],
    "payer_name": "Juan Pérez González",
    "advisor_id": 5,
    "notes": "Beca completa 2026 - Mérito académico"
  }'
```

### Ejemplo 2: Exonerar Orden Existente

```bash
curl -X POST "http://localhost:8000/api/v1/payment-orders/exonerated/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "order_payment_id": 456,
    "payer_name": "María García",
    "notes": "Exoneración aprobada por Dirección - Convenio institucional"
  }'
```

## Consideraciones

- **No se genera PDF** de la orden de pago
- **No se envían emails** al estudiante
- **El monto siempre es $0.00** en todos los conceptos
- **Estado final**: La orden queda con status 'PAID' y la factura con status 'P'
- **Auditoría**: Se registra el asesor que procesa la exoneración
- **Notas**: Es recomendable incluir notas explicativas sobre el motivo de la exoneración

## Validaciones

El endpoint valida:

1. ✅ Existencia del estudiante
2. ✅ Existencia del asesor (si se proporciona)
3. ✅ Existencia de los conceptos de pago
4. ✅ Que la orden no esté ya pagada (para órdenes existentes)
5. ✅ Que se proporcionen los datos correctos (orden existente XOR datos para nueva)

## Registro en Base de Datos

El endpoint crea/actualiza los siguientes registros:

1. **PaymentOrder**: Orden de pago con `status='PAID'` y `total_order=0.00`
2. **PaymentOrderDetails**: Detalles de la orden con `price=0.00` y `sub_total=0.00`
3. **Invoice**: Factura con `status='P'` y todos los totales en `0.00`
4. **InvoiceDetail**: Detalles de factura con `unit_price=0.00` y `subtotal=0.00`
5. **Payment**: Pago con `payment_method='EX'`, `status='V'` y `amount=0.00`
6. **PaymentAllocation**: Asignaciones por concepto con `amount_applied=0.00` y `status='PAID'`

## Documentación Interactiva

La documentación completa del endpoint está disponible en:

```
http://localhost:8000/api/docs
```

Buscar en la sección **"Exonerated Payments"**.

