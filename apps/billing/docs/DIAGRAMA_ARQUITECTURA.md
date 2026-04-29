# Diagrama de Arquitectura - Billing App

## Estructura de Capas

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                        │
│                     (views.py, serializers)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       APPLICATION LAYER                          │
│                     (Use Cases / Commands)                       │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         CreateInvoiceUseCase                            │   │
│  │  - execute(data)                                        │   │
│  │  - _get_student()                                       │   │
│  │  - _get_advisor()                                       │   │
│  │  - _get_payment_order()                                 │   │
│  │  - _validate_and_convert_details()                      │   │
│  │  - _prepare_invoice_data()                              │   │
│  │  - _update_payment_order_status()                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└────────────┬──────────────────────────────┬────────────────────┘
             │                              │
             ▼                              ▼
┌────────────────────────────┐  ┌──────────────────────────────┐
│     DOMAIN LAYER           │  │   INFRASTRUCTURE LAYER        │
│   (Business Logic)         │  │   (Data Access)               │
│                            │  │                               │
│ ┌────────────────────────┐ │  │ ┌───────────────────────────┐│
│ │ InvoiceDomainService   │ │  │ │  InvoiceRepository        ││
│ │  - validate_creation() │ │  │ │   (Django ORM)            ││
│ │  - validate_cancel()   │ │  │ │  - create()               ││
│ │  - calculate_total()   │ │  │ │  - update()               ││
│ │  - convert_details()   │ │  │ │  - get_by_id()            ││
│ │  - normalize_data()    │ │  │ │  - list_all()             ││
│ └────────────────────────┘ │  │ │  - cancel()               ││
│                            │  │ │  - get_by_number()        ││
│ ┌────────────────────────┐ │  │ └───────────────────────────┘│
│ │RepositoryInterface     │◄─┼──┤                              │
│ │  (Abstract Contract)   │ │  │                              │
│ └────────────────────────┘ │  │                              │
└────────────────────────────┘  └──────────┬───────────────────┘
                                           │
                                           ▼
                                ┌────────────────────────┐
                                │   DATABASE (Django)    │
                                │  - Invoice             │
                                │  - InvoiceDetail       │
                                │  - PaymentReceipt      │
                                │  - StudentCreditBalance│
                                └────────────────────────┘
```

## Flujo de Creación de Factura

```
┌─────────┐      ┌──────────────────┐      ┌─────────────────┐
│  Vista  │─────▶│ CreateInvoiceUC  │─────▶│ DomainService   │
│  (API)  │      │   execute()      │      │  validate()     │
└─────────┘      └────────┬─────────┘      └─────────────────┘
                          │
                          ▼
              ┌──────────────────────┐
              │  InvoiceRepository   │
              │    create()          │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Database           │
              │  - Invoice           │
              │  - InvoiceDetail     │
              └──────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Update Order Status │
              │  (PENDING → ACTIVE)  │
              └──────────────────────┘
```

## Dependencias entre Componentes

```
CreateInvoiceUseCase
    │
    ├─► InvoiceDomainService (validaciones)
    │
    ├─► InvoiceRepository (persistencia)
    │
    ├─► PaymentOrderRepository (actualizar orden)
    │
    ├─► UsersRepository (obtener estudiante/asesor)
    │
    └─► PaymentConceptRepository (validar conceptos)
```

## Flujo de Validaciones

```
1. Validar IDs
   ├─► Estudiante existe y activo
   ├─► Asesor existe
   └─► Orden de pago existe

2. Validar Datos de Entrada
   ├─► Al menos un detalle
   ├─► Cantidades > 0
   └─► Precios > 0

3. Validar Reglas de Negocio
   ├─► Orden no cancelada
   ├─► Orden no pagada completamente
   └─► Conceptos válidos

4. Validar Conceptos de Pago
   ├─► Concepto existe
   └─► Si requiere programa, orden lo tiene

5. Crear Factura
   ├─► Transacción atómica
   ├─► Generar número automático
   └─► Calcular totales

6. Actualizar Orden
   └─► PENDING → ACTIVE
```

## Interacción con Otros Módulos

```
┌──────────────────┐
│  Orden Pagos     │◄────┐
│  (Payment Order) │     │
└──────────────────┘     │
                         │
┌──────────────────┐     │    ┌─────────────┐
│  Administrador   │◄────┼────│   BILLING   │
│  (Usuarios)      │     │    │  (Invoice)  │
└──────────────────┘     │    └─────────────┘
                         │
┌──────────────────┐     │
│  Pagos           │◄────┘
│  (Payment)       │
└──────────────────┘
```

## Patrones Utilizados

### 1. Repository Pattern

```
Interface (Domain) ──implements──> Concrete Repository (Infrastructure)
```

### 2. Use Case Pattern

```
Request → Use Case → Domain Service → Repository → Database
```

### 3. Dependency Injection

```
__init__(domain_service, repository)
```

### 4. Transaction Script

```
@transaction.atomic
def execute():
    # Todas las operaciones en una transacción
```

## Ventajas de la Arquitectura

```
┌────────────────────────────────────────────────────────┐
│  VENTAJAS                                              │
├────────────────────────────────────────────────────────┤
│  ✓ Separación de responsabilidades                     │
│  ✓ Fácil de testear (mocks)                            │
│  ✓ Independiente del framework                         │
│  ✓ Lógica de negocio centralizada                      │
│  ✓ Fácil de mantener y extender                        │
│  ✓ Reutilización de código                             │
│  ✓ Consistente con orden_pagos                         │
└────────────────────────────────────────────────────────┘
```

## Ejemplo de Test

```python
# Mock del repositorio
mock_repository = Mock(spec=InvoiceRepositoryInterface)
mock_repository.create.return_value = invoice_mock

# Mock del domain service
mock_domain = Mock(spec=InvoiceDomainService)
mock_domain.validate_invoice_creation.return_value = True

# Crear use case con mocks
use_case = CreateInvoiceUseCase(
    domain_service=mock_domain,
    repository=mock_repository
)

# Ejecutar test
result = use_case.execute(test_data)
assert result == invoice_mock
```

## Próximas Implementaciones

```
CreateInvoice ✅
    │
    ├─► UpdateInvoice (próximo)
    ├─► CancelInvoice (próximo)
    ├─► ListInvoices (próximo)
    ├─► GenerateInvoicePDF (próximo)
    └─► ApplyCreditToInvoice (próximo)
```

