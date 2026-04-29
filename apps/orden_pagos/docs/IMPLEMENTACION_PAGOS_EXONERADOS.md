# Implementación de Endpoint de Pagos Exonerados

## Resumen

Se ha implementado un nuevo endpoint en Django Ninja para procesar pagos exonerados (gratuitos), permitiendo registrar
el asiento contable completo sin generar links de pago ni enviar notificaciones.

## Archivos Creados

### 1. Schemas

**Ubicación**: `apps/orden_pagos/presentation/api/schemas/exonerated_payment_schemas.py`

- `ExoneratedPaymentInput`: Schema de entrada con validaciones
- `ExoneratedPaymentOutput`: Schema de respuesta
- `ConceptInput`: Schema para conceptos de pago
- `PaymentDataOutput`: Schema con datos del pago creado

### 2. Router

**Ubicación**: `apps/orden_pagos/presentation/api/exonerated_payment_router.py`

Funciones implementadas:

- `create_exonerated_payment()`: Endpoint principal (POST)
- `_get_or_create_order()`: Obtiene orden existente o crea nueva
- `_create_order_payment()`: Crea orden de pago en $0
- `_get_or_create_invoice()`: Crea/actualiza factura
- `_create_payment_allocations()`: Crea asignaciones de pago

### 3. Tests

**Ubicación**: `apps/orden_pagos/tests/test_exonerated_payment.py`

Incluye:

- Tests unitarios de validación
- Tests de flujo completo
- Tests de errores y excepciones

### 4. Documentación

**Ubicación**: `apps/orden_pagos/docs/ENDPOINT_PAGOS_EXONERADOS.md`

Documentación completa con:

- Descripción del endpoint
- Ejemplos de uso
- Validaciones
- Errores comunes
- Flujo del proceso

## Archivos Modificados

### 1. Modelo Payment

**Archivo**: `apps/pagos/models.py`

✅ Agregado método de pago `('EX', _('Exonerated'))`

### 2. Router Principal

**Archivo**: `apps/orden_pagos/presentation/api/router.py`

✅ Importado `exonerated_router`
✅ Registrado sub-router: `router.add_router("/exonerated", exonerated_router)`

### 3. Schemas __init__

**Archivo**: `apps/orden_pagos/presentation/api/schemas/__init__.py`

✅ Agregados imports de schemas de pagos exonerados
✅ Exportados en `__all__`

## URL del Endpoint

```
POST /api/v1/payment-orders/exonerated/
```

## Autenticación

Requiere `AuthBearer` (token de autenticación)

## Funcionalidades

### ✅ Implementadas

1. **Crear orden nueva con conceptos en $0**
2. **Exonerar orden existente**
3. **Generar factura automáticamente**
4. **Registrar pago con método 'EX'**
5. **Crear asignaciones por concepto**
6. **Actualizar estado de orden a PAID**
7. **Validaciones completas**
8. **Transacciones atómicas**
9. **Manejo de errores**

### ❌ NO Implementado (por diseño)

- Generación de PDFs
- Envío de emails
- Links de pago
- Notificaciones

## Flujo de Proceso

```
1. Recibir request
   ↓
2. Validar datos de entrada
   ↓
3. ┌─ Orden nueva?
   │  ├─ SÍ → Crear orden con conceptos en $0
   │  └─ NO → Obtener orden existente y validar
   ↓
4. Crear/Actualizar factura en $0
   ↓
5. Crear pago con método 'EX' y status 'V'
   ↓
6. Crear asignaciones de pago por concepto
   ↓
7. Actualizar orden a status 'PAID'
   ↓
8. Retornar respuesta con IDs generados
```

## Validaciones

- ✅ Debe proporcionar orden existente O datos para nueva (no ambos)
- ✅ Estudiante debe existir
- ✅ Asesor debe existir (si se proporciona)
- ✅ Conceptos deben existir
- ✅ Orden existente no debe estar pagada
- ✅ Transacción atómica (rollback en caso de error)

## Ejemplos de Uso

### Orden Nueva

```bash
curl -X POST "http://localhost:8000/api/v1/payment-orders/exonerated/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": 123,
    "concepts": [{"concept_id": 1, "quantity": 1}],
    "payer_name": "Juan Pérez",
    "advisor_id": 5,
    "notes": "Beca completa 2026"
  }'
```

### Orden Existente

```bash
curl -X POST "http://localhost:8000/api/v1/payment-orders/exonerated/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "order_payment_id": 456,
    "payer_name": "María García",
    "notes": "Exoneración aprobada"
  }'
```

## Respuesta Exitosa

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

## Códigos HTTP

- `201 Created`: Pago exonerado creado exitosamente
- `400 Bad Request`: Error de validación
- `404 Not Found`: Recurso no encontrado
- `500 Internal Server Error`: Error del servidor

## Migración Pendiente

⚠️ **IMPORTANTE**: Ejecutar migración para agregar método de pago 'EX':

```bash
python manage.py makemigrations pagos --name add_exonerated_payment_method
python manage.py migrate
```

## Testing

Ejecutar tests:

```bash
python manage.py test apps.orden_pagos.tests.test_exonerated_payment
```

## Documentación Interactiva

Disponible en Django Ninja docs:

```
http://localhost:8000/api/docs
```

Buscar sección: **"Exonerated Payments"**

## Casos de Uso Principales

1. **Becas Académicas**: Estudiantes con beca del 100%
2. **Convenios Institucionales**: Acuerdos especiales con organizaciones
3. **Cortesías**: Casos excepcionales aprobados por dirección
4. **Eventos Gratuitos**: Registros de actividades sin costo
5. **Exoneraciones Administrativas**: Ajustes contables aprobados

## Consideraciones de Seguridad

- ✅ Requiere autenticación
- ✅ Validación de permisos mediante AuthBearer
- ✅ Transacciones atómicas
- ✅ Validación de datos de entrada
- ✅ Manejo seguro de errores

## Auditoría

El sistema registra:

- Usuario que realizó el pago (student)
- Asesor que procesó la exoneración
- Fecha de creación automática
- Notas explicativas
- Método de pago 'EX' identificable

## Próximos Pasos

1. ✅ Ejecutar migraciones
2. ✅ Probar endpoint en desarrollo
3. ✅ Ejecutar suite de tests
4. ✅ Actualizar documentación de usuario
5. ✅ Capacitar equipo en uso del endpoint
6. ✅ Monitorear logs en producción

## Soporte

Para preguntas o problemas:

- Ver documentación completa en `docs/ENDPOINT_PAGOS_EXONERADOS.md`
- Revisar tests en `tests/test_exonerated_payment.py`
- Consultar código en `presentation/api/exonerated_payment_router.py`

---

**Fecha de Implementación**: 2026-01-12
**Versión**: 1.0.0
**Estado**: ✅ Implementado y listo para pruebas

