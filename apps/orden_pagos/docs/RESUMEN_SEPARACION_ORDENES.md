# Resumen: Separación Automática de Órdenes de Pago

## Fecha: 2025-11-30

## Problema Original

Se necesitaba enviar dos correos separados cuando una orden de pago contenía "Costo Administrativo" (C) o "Booking
Fee" (F) combinados con otros tipos de pago que requieren programa de estudio.

## Solución Implementada

En lugar de separar los correos, se decidió **crear dos órdenes separadas desde el inicio** cuando se detecta esta
combinación. Esta es una solución más limpia y mantenible.

## Tipos de Pago Clasificados

### Tipos INDEPENDIENTES (no requieren programa):

- `C` - Costo Administrativo
- `F` - Booking Fee
- `I` - Inscripción
- `D` - Airport Drop-off
- `H` - HomeStay (Alojamiento)
- `AH` - Abono de Alojamiento
- `CL` - Custodian Letter
- `ST` - Student Services Fee
- `CF` - Courier Fees
- `HS` - Homestay Special Diet

### Tipos DEPENDIENTES (requieren programa):

- `M` - Matricula
- `B` - Inscripción y Matricula
- `T` - Pago Total
- `E` - Extension de Matricula
- `A` - Abono de Matricula
- `IA` - Inscripción y Abono de Matricula
- `BF` - Inscripción, Matricula y Booking Fee
- `IF` - Inscripción y Booking Fee
- `MF` - Matricula y Booking Fee
- `HF` - HomeStay y Booking Fee
- `AF` - Abono de Matricula y Booking Fee
- `R` - Airport Pick-up
- `S` - Seguro Médico
- `U` - Adicionales completos
- `L`, `W` - (si existen)

## Archivos Modificados

### 1. `apps/orden_pagos/models.py`

**Cambios:**

- ✅ Agregadas constantes globales:
    - `INDEPENDENT_PAYMENT_TYPES` - Tipos que NO requieren programa
    - `PROGRAM_DEPENDENT_TYPES` - Tipos que SÍ requieren programa

- ✅ Corregida función `payment_order_upload_to()` para retornar el path

- ✅ Agregado método `PaymentOrder.should_split_orders()`:
    - Detecta si una orden tiene tipos independientes + dependientes
    - Retorna: `(debe_separar, detalles_independientes, detalles_dependientes)`

### 2. `apps/orden_pagos/application/use_cases/create_payment_order.py`

**Cambios:**

- ✅ Agregado import de constantes y `PaymentType`

- ✅ Modificado método `execute()`:
    - Detecta si se requiere separar órdenes
    - Decide si crear una o dos órdenes

- ✅ Agregado método `_check_split_required()`:
    - Analiza los detalles de pago
    - Clasifica por tipo (independiente vs dependiente)
    - Retorna si se requiere separación

- ✅ Creado método `_create_single_order()`:
    - Crea una sola orden (flujo normal)

- ✅ Creado método `_create_split_orders()`:
    - Crea dos órdenes separadas:
        - **Orden 1**: Solo tipos independientes (con programa mínimo)
        - **Orden 2**: Solo tipos dependientes (con programa completo)
    - Retorna lista con ambas órdenes

- ✅ Creado método `_get_minimal_program_data()`:
    - Genera datos de programa mínimos para orden de tipos independientes
    - Copia contexto básico pero sin cálculos de precio

### 3. `apps/orden_pagos/application/use_cases/send_payment_link.py`

**Cambios:**

- ✅ Simplificado método `execute()`:
    - Ya no necesita detectar separación (se hace en creación)
    - Envía un solo correo por orden

- ✅ Eliminados métodos innecesarios:
    - `_check_payment_types()`
    - `_send_split_emails()`
    - `_generate_partial_pdf()`
    - `_send_partial_email()`
    - `_get_payment_types_from_details()`

- ✅ Simplificado método `_prepare_and_send_emails()`

- ✅ Simplificado método `_generate_and_save_pdf()`

### 4. `apps/orden_pagos/presentation/views/payment_order_viewset.py`

**Cambios:**

- ✅ Actualizado método `create()`:
    - Maneja retorno de una orden o lista de dos órdenes
    - Si se crearon dos órdenes:
        - Serializa ambas con `many=True`
        - Retorna respuesta con `split: true` y mensaje explicativo
        - Envía link de pago para ambas órdenes si se solicita
    - Si se creó una sola orden:
        - Mantiene el flujo normal

## Flujo de Ejecución

### Caso 1: Solo tipos independientes (C, F)

```
Request → CreatePaymentOrderUseCase
       → _check_split_required() → False
       → _create_single_order() 
       → 1 orden con programa mínimo
```

### Caso 2: Solo tipos dependientes (M, B, T, etc.)

```
Request → CreatePaymentOrderUseCase
       → _check_split_required() → False
       → _create_single_order()
       → 1 orden con programa completo
```

### Caso 3: Tipos independientes + dependientes

```
Request → CreatePaymentOrderUseCase
       → _check_split_required() → True
       → _create_split_orders()
       → Orden 1: Tipos independientes (programa mínimo)
       → Orden 2: Tipos dependientes (programa completo)
       → Retorna [orden1, orden2]
```

## Respuesta de la API

### Una sola orden:

```json
{
  "id": 123,
  "order_number": "PO-0001234",
  "student": {
    ...
  },
  "total_order": "250.00",
  ...
}
```

### Dos órdenes separadas:

```json
{
  "orders": [
    {
      "id": 123,
      "order_number": "PO-0001234",
      "total_order": "100.00",
      ...
    },
    {
      "id": 124,
      "order_number": "PO-0001235",
      "total_order": "500.00",
      ...
    }
  ],
  "split": true,
  "message": "Se crearon dos órdenes separadas: una para pagos independientes y otra para pagos dependientes del programa"
}
```

## Ventajas de esta Solución

1. ✅ **Separación limpia**: Cada orden tiene su propio estado, token, PDF y correo
2. ✅ **Gestión independiente**: Se pueden pagar por separado
3. ✅ **Tracking simple**: No hay complejidad de estados parciales
4. ✅ **Contabilidad clara**: Cada invoice corresponde a UNA orden
5. ✅ **Moneda correcta**: Cada orden usa la moneda de su institución
6. ✅ **Sin refactorización masiva**: Los casos de uso de envío quedan simples

## Consideraciones para el Frontend

El frontend debe detectar cuando `split === true` en la respuesta y:

- Mostrar ambas órdenes al usuario
- Indicar que se crearon dos órdenes separadas
- Permitir pagar cada una independientemente

## Próximos Pasos (Opcionales)

1. Agregar tests unitarios para `_check_split_required()`
2. Agregar tests de integración para creación de órdenes separadas
3. Actualizar documentación de API
4. Considerar agregar campo `related_order_id` para vincular órdenes relacionadas

## Notas Técnicas

- Las órdenes separadas son completamente independientes en la BD
- Cada orden genera su propio número correlativo (PO-XXXXXXX)
- El programa mínimo en tipos independientes mantiene contexto pero sin cálculos
- Los correos se envían de forma individual por cada orden

---

**Autor**: GitHub Copilot  
**Revisión requerida**: Sí  
**Tests requeridos**: Sí

