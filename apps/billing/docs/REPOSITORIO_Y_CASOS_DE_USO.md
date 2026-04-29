# Documentación del Repositorio y Caso de Uso de Billing

## Estructura Creada

Se ha implementado la arquitectura hexagonal (Clean Architecture) para el módulo de facturación, siguiendo el mismo
patrón utilizado en `orden_pagos`.

### Estructura de Carpetas

```
apps/billing/
├── domain/
│   ├── __init__.py
│   └── interface/
│       ├── __init__.py
│       ├── repository/
│       │   ├── __init__.py
│       │   └── invoice_repository_interface.py
│       └── services/
│           ├── __init__.py
│           └── invoice_service.py
├── infrastructure/
│   ├── __init__.py
│   └── repository/
│       ├── __init__.py
│       └── invoice_repository.py
└── application/
    ├── __init__.py
    └── use_cases/
        ├── __init__.py
        └── create_invoice.py
```

## Componentes

### 1. Domain Layer (Capa de Dominio)

#### InvoiceRepositoryInterface

**Ubicación:** `domain/interface/repository/invoice_repository_interface.py`

Contrato abstracto que define las operaciones del repositorio de facturas:

- `list_all()` - Listar facturas con filtros opcionales
- `create()` - Crear factura con detalles
- `update()` - Actualizar factura existente
- `cancel()` - Anular factura
- `get_by_id()` - Obtener por ID
- `get_by_invoice_number()` - Obtener por número de factura
- `get_by_id_with_relations()` - Obtener con todas las relaciones
- `save_invoice()` - Guardar instancia con campos específicos
- `get_invoices_by_student()` - Facturas de un estudiante
- `get_invoices_by_payment_order()` - Facturas de una orden de pago
- `get_pending_invoices_by_student()` - Facturas pendientes de un estudiante
- `calculate_student_total_debt()` - Calcular deuda total

#### InvoiceDomainService

**Ubicación:** `domain/interface/services/invoice_service.py`

Servicio de dominio con lógica de negocio y validaciones:

**Métodos principales:**

- `validate_invoice_creation()` - Valida si se puede crear una factura
    - Verifica que el estudiante esté activo
    - Valida que la orden de pago no esté cancelada o pagada
    - Valida que haya al menos un detalle
    - Valida montos positivos

- `validate_invoice_cancellation()` - Valida si se puede anular una factura
    - No permite anular facturas ya anuladas
    - No permite anular facturas pagadas sin reembolso

- `calculate_invoice_total()` - Calcula el total de la factura
    - Formula: `subtotal - descuentos + impuestos`

- `convert_invoice_details_to_instances()` - Convierte IDs a instancias de modelo
    - Transforma `payment_concept` (ID) a instancia de `PaymentConcept`

- `normalize_invoice_data()` - Normaliza datos convirtiendo instancias a IDs
    - Convierte instancias de `Usuarios`, `PaymentOrder` a IDs

- `validate_payment_concept_requires_program()` - Valida conceptos que requieren programa
    - Verifica que si un concepto requiere programa, la orden lo tenga

### 2. Infrastructure Layer (Capa de Infraestructura)

#### InvoiceRepository

**Ubicación:** `infrastructure/repository/invoice_repository.py`

Implementación concreta del repositorio usando Django ORM:

**Características:**

- Usa `select_related()` y `prefetch_related()` para optimizar consultas
- Implementa anotaciones para mostrar nombres completos y estados descriptivos
- Maneja transacciones atómicas en operaciones críticas
- Incluye método `_apply_filters()` para filtrado avanzado:
    - Por estudiante
    - Por asesor
    - Por estado
    - Por orden de pago
    - Por rango de fechas
    - Por número de factura
    - Por nombre de estudiante

**Métodos auxiliares privados:**

- `_normalize_invoice_data()` - Normaliza datos usando el servicio de dominio
- `_create_invoice_details()` - Crea los detalles de la factura
- `_reload_invoice()` - Recarga factura con todas las relaciones
- `_apply_filters()` - Aplica filtros al queryset

### 3. Application Layer (Capa de Aplicación)

#### CreateInvoiceUseCase

**Ubicación:** `application/use_cases/create_invoice.py`

Caso de uso para crear facturas siguiendo las reglas de negocio:

**Flujo de ejecución:**

1. **Obtener entidades relacionadas:**
    - Obtiene estudiante, asesor y orden de pago
    - Valida que existan

2. **Validar datos de entrada:**
    - Verifica que haya al menos un detalle
    - Valida campos obligatorios

3. **Validar reglas de negocio:**
    - Usa `InvoiceDomainService.validate_invoice_creation()`

4. **Validar conceptos de pago:**
    - Verifica que los conceptos existan
    - Valida que no requieran programa si la orden no lo tiene
    - Convierte IDs a instancias

5. **Crear factura:**
    - Prepara datos normalizados
    - Crea factura usando el repositorio
    - Todo en una transacción atómica

6. **Actualizar orden de pago:**
    - Si estaba en PENDING, la cambia a ACTIVE

**Estructura de datos esperada:**

```python
{
    "student": 123,  # ID del estudiante
    "advisor": 456,  # ID del asesor
    "payment_order": 789,  # ID de la orden de pago
    "invoice_details": [
        {
            "payment_concept": 1,  # ID del concepto
            "description": "Matrícula curso de inglés",
            "quantity": 1,
            "unit_price": 500.00,
            "discount": 50.00  # Opcional
        },
        # Más detalles...
    ],
    "currency": "USD",  # Opcional, default: USD
    "taxes": 0.00,  # Opcional, default: 0.00
    "notes": "Observaciones adicionales"  # Opcional
}
```

## Uso del Caso de Uso

### Ejemplo básico:

```python
from apps.billing.application.use_cases import CreateInvoiceUseCase
from apps.billing.domain.interface.services import InvoiceDomainService
from apps.billing.infrastructure.repository import InvoiceRepository

# Instanciar dependencias
domain_service = InvoiceDomainService()
repository = InvoiceRepository()

# Crear caso de uso
use_case = CreateInvoiceUseCase(
    domain_service=domain_service,
    repository=repository
)

# Datos de la factura
invoice_data = {
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
    invoice = use_case.execute(invoice_data)
    print(f"Factura creada: {invoice.invoice_number}")
except ValidationError as e:
    print(f"Error: {e}")
```

### Ejemplo desde una vista de Django REST Framework:

```python
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from apps.billing.application.use_cases import CreateInvoiceUseCase
from apps.billing.domain.interface.services import InvoiceDomainService
from apps.billing.infrastructure.repository import InvoiceRepository


@api_view(['POST'])
def create_invoice_view(request):
    """Endpoint para crear facturas"""

    # Instanciar caso de uso
    domain_service = InvoiceDomainService()
    repository = InvoiceRepository()
    use_case = CreateInvoiceUseCase(domain_service, repository)

    try:
        # Ejecutar caso de uso
        invoice = use_case.execute(request.data)

        return Response({
            'success': True,
            'message': 'Factura creada exitosamente',
            'data': {
                'invoice_id': invoice.id,
                'invoice_number': invoice.invoice_number,
                'total': str(invoice.total),
                'status': invoice.get_status_display()
            }
        }, status=status.HTTP_201_CREATED)

    except ValidationError as e:
        return Response({
            'success': False,
            'message': 'Error de validación',
            'errors': e.detail
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            'success': False,
            'message': 'Error al crear la factura',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

## Ventajas de esta Arquitectura

1. **Separación de responsabilidades:**
    - Domain: Define contratos y reglas de negocio
    - Infrastructure: Implementa acceso a datos
    - Application: Orquesta casos de uso

2. **Testeable:**
    - Cada componente se puede testear independientemente
    - Se pueden mockear los repositorios en los tests

3. **Mantenible:**
    - Cambios en la base de datos no afectan la lógica de negocio
    - Reglas de negocio centralizadas en el servicio de dominio

4. **Escalable:**
    - Fácil agregar nuevos casos de uso
    - Fácil agregar nuevos métodos al repositorio

5. **Consistente:**
    - Sigue el mismo patrón que `orden_pagos`
    - Facilita la comprensión del código

## Próximos Pasos

Se pueden agregar más casos de uso según las necesidades:

- `UpdateInvoiceUseCase` - Actualizar facturas
- `CancelInvoiceUseCase` - Anular facturas
- `ListInvoicesUseCase` - Listar facturas con filtros
- `GetInvoiceByNumberUseCase` - Obtener factura por número
- `GenerateInvoicePDFUseCase` - Generar PDF de factura
- `ApplyCreditToInvoiceUseCase` - Aplicar abonos a facturas

## Notas Importantes

- Todas las operaciones de creación/actualización usan transacciones atómicas
- Las validaciones de negocio están en el `InvoiceDomainService`
- El repositorio solo maneja acceso a datos, no lógica de negocio
- Los casos de uso orquestan el flujo completo de la operación
- Se valida que los conceptos de pago sean compatibles con la orden de pago

