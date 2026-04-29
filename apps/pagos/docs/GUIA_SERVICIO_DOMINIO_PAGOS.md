# Guía de Uso del Servicio de Dominio de Pagos

## Descripción General

El **PaymentDomainService** es un servicio de dominio que se encarga de:

- Convertir IDs a instancias de modelos de forma segura
- Validar la existencia de entidades relacionadas antes de crear un pago
- Usar repositorios en lugar de acceso directo a modelos (siguiendo Clean Architecture)

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                     Caso de Uso (Application Layer)              │
│  - CreatePayment                                                 │
│  - Recibe datos con IDs                                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  PaymentRepository (Infrastructure)              │
│  - create(payment_data, allocations)                             │
│  - Usa PaymentDomainService para conversión                      │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              PaymentDomainService (Domain Layer)                 │
│  - convert_ids_to_instances()                                    │
│  - convert_allocation_ids_to_instances()                         │
│  - Usa repositorios:                                             │
│    • UsersRepository                                             │
│    • InvoiceRepository                                           │
│    • PaymentConceptRepository                                    │
└─────────────────────────────────────────────────────────────────┘
```

## Uso desde Caso de Uso

### Ejemplo 1: Crear Pago SIN Factura (Pago Adelantado)

```python
from apps.pagos.application.use_cases.create_payment_exonerated import CreatePayment
from apps.pagos.infrastructure.repository.payment_repository import PaymentRepository

# Datos del pago (todos los IDs se convierten automáticamente)
payment_data = {
    'user_id': 123,  # Se convierte a instancia de Usuarios
    'advisor_id': 45,  # Se convierte a instancia de Usuarios
    'invoice_id': None,  # Sin factura aún
    'amount': Decimal('500.00'),
    'currency': 'USD',
    'payment_method': 'BT',
    'status': 'P',
    'payer_name': 'Juan Pérez'
}

# Asignaciones a conceptos (sin invoice_detail porque no hay factura)
allocations = [
    {
        'concept_id': 1,  # ID del concepto de pago (se convierte a instancia)
        'invoice_detail_id': None,
        'amount': Decimal('500.00'),
        'description': 'Pago adelantado matrícula'
    }
]

# Crear el pago
repository = PaymentRepository()
use_case = CreatePayment(repository)
payment = use_case.execute(payment_data, allocations)

print(f"Pago creado: {payment.payment_number}")
```

### Ejemplo 2: Crear Pago CON Factura (Flujo Normal)

```python
# Datos del pago con factura
payment_data = {
    'user_id': 123,  # Se convierte a instancia de Usuarios
    'advisor_id': 45,  # Se convierte a instancia de Usuarios
    'invoice_id': 789,  # Se convierte a instancia de Invoice
    'amount': Decimal('1500.00'),
    'currency': 'USD',
    'payment_method': 'TC',
    'status': 'D',
    'payer_name': 'María García'
}

# Asignaciones a detalles de factura
allocations = [
    {
        'concept_id': 1,  # Concepto: Matrícula
        'invoice_detail_id': 101,  # Detalle específico de la factura
        'amount': Decimal('1000.00'),
        'description': 'Pago matrícula'
    },
    {
        'concept_id': 2,  # Concepto: Materiales
        'invoice_detail_id': 102,
        'amount': Decimal('500.00'),
        'description': 'Pago materiales'
    }
]

# Crear el pago
payment = use_case.execute(payment_data, allocations)
```

### Ejemplo 3: Crear Pago Exonerado (Con Factura)

```python
payment_data = {
    'user_id': 123,
    'advisor_id': 45,
    'invoice_id': 789,  # Factura ya creada
    'amount': Decimal('0.00'),  # Monto 0 porque está exonerado
    'currency': 'USD',
    'payment_method': 'EX',  # Método: Exonerado
    'status': 'V',  # Estado: Verificado
    'payer_name': 'Sistema'
}

allocations = [
    {
        'concept_id': 1,
        'invoice_detail_id': 101,
        'amount': Decimal('0.00'),
        'description': 'Exoneración total'
    }
]

payment = use_case.execute(payment_data, allocations)
```

## Validaciones Automáticas

El `PaymentDomainService` valida automáticamente:

1. ✅ **Existencia de Usuario**: Verifica que `user_id` exista
2. ✅ **Existencia de Asesor**: Verifica que `advisor_id` exista (si se proporciona)
3. ✅ **Existencia de Factura**: Verifica que `invoice_id` exista (si se proporciona)
4. ✅ **Existencia de Conceptos**: Verifica que cada `concept_id` en allocations exista
5. ✅ **Existencia de Detalles**: Verifica que cada `invoice_detail_id` exista (si se proporciona)

Si alguna entidad no existe, lanza `ValidationError` con mensaje descriptivo.

## Repositorios Utilizados

### 1. UsersRepository

```python
# Ubicación: apps/orden_pagos/infrastructure/repository/users_repository.py
get_user_by_id(user_id) -> Usuarios
```

### 2. InvoiceRepository

```python
# Ubicación: apps/billing/infrastructure/repository/invoice_repository.py
get_by_id(invoice_id) -> Invoice
```

### 3. PaymentConceptRepository

```python
# Ubicación: apps/orden_pagos/infrastructure/repository/payment_concept_repository.py
get_concept_by_id(concept_id) -> PaymentConcept
```

## Beneficios de Esta Arquitectura

1. **Separación de Responsabilidades**:
    - Caso de uso: Lógica de negocio de alto nivel
    - Repositorio: Persistencia de datos
    - Servicio de dominio: Conversión y validación

2. **Testeable**:
    - Los repositorios se pueden mockear fácilmente
    - Las validaciones están centralizadas

3. **Consistente**:
    - Siempre se valida la existencia de entidades
    - Mensajes de error claros

4. **Mantenible**:
    - Si cambia la forma de obtener un usuario, solo se modifica el repositorio
    - No hay acceso directo a modelos desde el caso de uso

## Dos Flujos Principales

### Flujo 1: Exonerado (Orden → Factura → Pago)

```
1. Crear Orden de Pago (PaymentOrder)
   ↓
2. Crear Factura (Invoice) con detalles
   ↓
3. Crear Pago Exonerado
   - invoice_id: ID de la factura
   - payment_method: 'EX'
   - amount: 0.00
   - allocations: vinculadas a invoice_details
```

### Flujo 2: Pago Normal (Pago → Factura)

```
1. Crear Pago sin factura
   - invoice_id: None
   - allocations: solo con concept_id
   ↓
2. Estudiante realiza el pago
   ↓
3. Crear Factura después
   - Vincular al pago existente
```

## Errores Comunes

### ❌ Error: "El usuario con ID X no existe"

**Solución**: Verificar que el `user_id` sea válido y el usuario exista en la BD.

### ❌ Error: "La factura con ID X no existe"

**Solución**: Si es pago adelantado, pasar `invoice_id: None`. Si es con factura, verificar que exista.

### ❌ Error: "El concepto de pago con ID X no existe"

**Solución**: Verificar que el `concept_id` en allocations sea válido.

### ❌ Error: "El detalle de factura con ID X no existe"

**Solución**: Verificar que el `invoice_detail_id` corresponda a un detalle de la factura indicada.

## Próximos Pasos

- [ ] Crear documentación del caso de uso `CreatePayment`
- [ ] Añadir ejemplos de tests unitarios
- [ ] Documentar el proceso de actualización de pagos
- [ ] Crear diagramas de secuencia para ambos flujos

