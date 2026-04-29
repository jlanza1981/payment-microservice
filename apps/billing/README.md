# Billing App

Módulo de facturación para el sistema LC Mundo. Gestiona la creación, actualización y administración de facturas,
recibos de pago y créditos de estudiantes.

## Estructura del Proyecto

La app `billing` sigue la arquitectura hexagonal (Clean Architecture) con la siguiente estructura:

```
billing/
├── domain/                          # Capa de dominio
│   ├── interface/
│   │   ├── repository/              # Interfaces de repositorios
│   │   │   └── invoice_repository_interface.py
│   │   └── services/                # Servicios de dominio
│   │       └── invoice_service.py
│   └── __init__.py
├── infrastructure/                  # Capa de infraestructura
│   ├── repository/                  # Implementaciones de repositorios
│   │   └── invoice_repository.py
│   └── __init__.py
├── application/                     # Capa de aplicación
│   ├── use_cases/                   # Casos de uso
│   │   └── create_invoice.py
│   └── __init__.py
├── docs/                            # Documentación
│   └── REPOSITORIO_Y_CASOS_DE_USO.md
├── tests/                           # Tests
│   └── test_invoice_use_case.py
├── models.py                        # Modelos de Django
├── admin.py                         # Configuración del admin
├── views.py                         # Vistas
└── urls_V1.py                       # URLs
```

## Modelos Principales

### Invoice (Factura)

- **Campos principales:**
    - `invoice_number`: Número de factura único (auto-generado)
    - `user`: Estudiante (relación con Usuarios)
    - `advisor`: Asesor (relación con Usuarios)
    - `payment_order`: Orden de pago asociada
    - `subtotal`, `taxes`, `total`: Montos calculados
    - `balance_due`: Saldo pendiente
    - `status`: Estado (Borrador, Emitida, Parcialmente pagada, Pagada, Anulada, etc.)

### InvoiceDetail (Detalle de Factura)

- Líneas de la factura con conceptos de pago
- Campos: `concept`, `description`, `quantity`, `unit_price`, `discount`, `subtotal`

### PaymentReceipt (Recibo de Pago)

- Recibos generados automáticamente al registrar pagos
- Incluye PDF generado y envío por email

### StudentCreditBalance (Saldo a Favor)

- Gestión de abonos y créditos de estudiantes
- Permite aplicar saldos a futuras facturas

## Arquitectura

### 1. Domain Layer (Capa de Dominio)

Define las reglas de negocio y contratos sin depender de frameworks.

#### InvoiceRepositoryInterface

Contrato abstracto que define operaciones del repositorio:

- CRUD de facturas
- Consultas especializadas (por estudiante, orden de pago, etc.)
- Cálculo de deudas

#### InvoiceDomainService

Lógica de negocio y validaciones:

- Validación de creación de facturas
- Validación de anulaciones
- Cálculo de totales
- Conversión de datos

### 2. Infrastructure Layer (Capa de Infraestructura)

Implementa el acceso a datos usando Django ORM.

#### InvoiceRepository

- Implementación concreta del repositorio
- Optimización de consultas con `select_related` y `prefetch_related`
- Filtros avanzados
- Transacciones atómicas

### 3. Application Layer (Capa de Aplicación)

Casos de uso que orquestan la lógica de negocio.

#### CreateInvoiceUseCase

Caso de uso para crear facturas:

1. Valida entidades relacionadas
2. Aplica reglas de negocio
3. Valida conceptos de pago
4. Crea la factura
5. Actualiza orden de pago

## Uso

### Crear una Factura

```python
from apps.billing.application.use_cases import CreateInvoiceUseCase
from apps.billing.domain.interface.services import InvoiceDomainService
from apps.billing.infrastructure.repository import InvoiceRepository

# Instanciar dependencias
domain_service = InvoiceDomainService()
repository = InvoiceRepository()
use_case = CreateInvoiceUseCase(domain_service, repository)

# Datos de la factura
invoice_data = {
    "student": 123,  # ID del estudiante
    "advisor": 456,  # ID del asesor
    "payment_order": 789,  # ID de la orden de pago
    "invoice_details": [
        {
            "payment_concept": 1,  # ID del concepto
            "description": "Matrícula",
            "quantity": 1,
            "unit_price": 500.00,
            "discount": 50.00
        }
    ],
    "currency": "USD",
    "taxes": 0.00,
    "notes": "Primera factura"
}

# Ejecutar
invoice = use_case.execute(invoice_data)
print(f"Factura creada: {invoice.invoice_number}")
```

### Usar el Repositorio Directamente

```python
from apps.billing.infrastructure.repository import InvoiceRepository

repository = InvoiceRepository()

# Listar facturas con filtros
invoices = repository.list_all({
    'student_id': 123,
    'status': 'I',
    'date_from': '2026-01-01'
})

# Obtener factura por ID
invoice = repository.get_by_id(1)

# Calcular deuda de un estudiante
total_debt = repository.calculate_student_total_debt(123)
```

## Estados de Factura

- **B** - Borrador
- **I** - Emitida
- **PP** - Parcialmente pagada
- **P** - Pagada
- **A** - Anulada
- **PV** - Pendiente por Verificar por Tesorería
- **V** - Verificada por Tesorería
- **R** - Reembolsada

## Flujo de Facturación

1. **Crear Orden de Pago** (en `orden_pagos`)
2. **Crear Factura** (en `billing`)
    - Se genera número automático
    - Se calculan totales
    - Estado inicial: Emitida
    - La orden de pago pasa a ACTIVE
3. **Registrar Pagos** (en `pagos`)
    - Se actualiza `balance_due`
    - Se genera recibo automático
    - Se envía por email
4. **Factura Pagada Completamente**
    - Estado: Pagada
    - Orden de pago se marca como PAID

## Validaciones Principales

1. **Estudiante activo** - No se puede facturar a estudiantes inactivos
2. **Orden de pago válida** - No puede estar cancelada o ya pagada
3. **Al menos un detalle** - Debe tener conceptos de facturación
4. **Montos positivos** - Cantidades y precios deben ser > 0
5. **Conceptos requieren programa** - Algunos conceptos necesitan que la orden tenga programa

## Testing

Ejecutar tests:

```bash
python manage.py test apps.billing.tests
```

## Documentación Adicional

- [Repositorio y Casos de Uso](docs/REPOSITORIO_Y_CASOS_DE_USO.md) - Documentación detallada de la arquitectura
- [Sistema de Abonos](../../docs/GUIA_RAPIDA_SISTEMA_ABONOS.md) - Guía del sistema de créditos

## Próximos Desarrollos

- [ ] Caso de uso para actualizar facturas
- [ ] Caso de uso para anular facturas
- [ ] Caso de uso para generar PDF de facturas
- [ ] Caso de uso para aplicar créditos
- [ ] Caso de uso para listar facturas con paginación
- [ ] Integración con sistema de reportes
- [ ] Notificaciones automáticas de facturas pendientes

## Notas Técnicas

- Las facturas generan número correlativo automáticamente
- Los totales se calculan automáticamente en el modelo
- Los recibos se generan de forma asíncrona con Celery
- Los PDFs se generan con WeasyPrint
- Todas las operaciones críticas usan transacciones atómicas

