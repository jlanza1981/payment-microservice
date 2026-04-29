# Payment Repository - Documentación

## Descripción

Este documento describe la interfaz de repositorio y su implementación para el modelo `Payment` en la app de pagos.

## Arquitectura

La implementación sigue el patrón Repository con una separación clara entre:

- **Domain/Interface**: Define el contrato abstracto (`PaymentRepositoryInterface`)
- **Infrastructure**: Implementa el contrato usando Django ORM (`PaymentRepository`)

## Archivos

```
apps/pagos/
├── domain/
│   └── interface/
│       └── repository/
│           └── payment_repository_interface.py
└── infrastructure/
    └── repository/
        └── payment_repository.py
```

## PaymentRepositoryInterface

Interfaz abstracta que define todas las operaciones disponibles para el modelo `Payment`.

### Métodos Principales

#### Operaciones CRUD

- `list_all(filters: Dict[str, Any] = None) -> List[Payment]`
    - Lista todos los pagos con filtros opcionales
    - Incluye anotaciones para nombres de usuario y asesor
    - Retorna QuerySet ordenado por fecha de pago descendente

- `create(payment_data: Dict[str, Any], allocations: List[Dict[str, Any]] = None) -> Payment`
    - Crea un nuevo pago con asignaciones opcionales
    - Utiliza transacciones atómicas
    - Normaliza datos de entrada automáticamente

- `update(payment_id: int, payment_data: Dict[str, Any]) -> Payment`
    - Actualiza un pago existente
    - Valida que el pago no esté anulado
    - Puede actualizar asignaciones si se incluyen en `payment_data`

- `cancel(payment_id: int) -> bool`
    - Anula un pago cambiando su estado a 'X'
    - Retorna `True` si se anuló correctamente

#### Operaciones de Estado

- `verify(payment_id: int, verification_date: Any = None) -> Payment`
    - Verifica un pago por tesorería
    - Cambia estado a 'V' (Verificado)
    - Establece fecha de verificación (por defecto hoy)

- `reject(payment_id: int) -> Payment`
    - Rechaza un pago
    - Cambia estado a 'R' (Rechazado)

#### Consultas

- `get_by_id(payment_id: int) -> Optional[Payment]`
    - Obtiene un pago por ID con relaciones básicas

- `get_by_payment_number(payment_number: str) -> Optional[Payment]`
    - Obtiene un pago por número de pago único

- `get_by_id_with_relations(payment_id: int) -> Optional[Payment]`
    - Obtiene un pago con todas sus relaciones cargadas
    - Incluye: invoice, user, advisor, allocations

- `get_payments_by_invoice(invoice_id: int) -> List[Payment]`
    - Obtiene todos los pagos de una factura

- `get_payments_by_user(user_id: int) -> List[Payment]`
    - Obtiene todos los pagos de un usuario

- `get_pending_payments_by_user(user_id: int) -> List[Payment]`
    - Obtiene pagos pendientes de verificación (status='P')

- `get_verified_payments_by_invoice(invoice_id: int) -> List[Payment]`
    - Obtiene pagos verificados de una factura (status='V')

- `get_payments_by_date_range(start_date, end_date, status: str = None) -> List[Payment]`
    - Obtiene pagos en un rango de fechas
    - Puede filtrar por estado específico

- `get_payments_by_advisor(advisor_id: int) -> List[Payment]`
    - Obtiene pagos gestionados por un asesor

#### Operaciones de PaymentAllocation

- `get_payment_allocations_by_payment(payment_id: int) -> List[PaymentAllocation]`
    - Obtiene todas las asignaciones de un pago

#### Cálculos

- `calculate_total_payments_by_invoice(invoice_id: int) -> Decimal`
    - Calcula el total de pagos verificados de una factura

## PaymentRepository

Implementación concreta de `PaymentRepositoryInterface` usando Django ORM.

### Características

1. **Normalización Automática**: Convierte instancias de modelos a IDs automáticamente
2. **Transacciones Atómicas**: Todas las operaciones de escritura usan `transaction.atomic()`
3. **Optimización de Consultas**: Usa `select_related` y `prefetch_related` para reducir queries
4. **Anotaciones**: Incluye nombres completos y estados legibles en listados
5. **Filtrado Dinámico**: Método `_apply_filters` para aplicar filtros flexibles

### Métodos Privados

- `_normalize_payment_data(payment_data: Dict[str, Any]) -> Dict[str, Any]`
    - Convierte instancias de modelos a IDs
    - Remueve campos no editables

- `_create_payment_allocations(payment: Payment, allocations: List[Dict[str, Any]]) -> None`
    - Crea asignaciones de pago en bloque usando `bulk_create`

- `_normalize_allocation_data(allocation_data: Dict[str, Any]) -> Dict[str, Any]`
    - Normaliza datos de asignación para creación

- `_reload_payment(payment_id: int) -> Payment`
    - Recarga un pago con todas sus relaciones

- `_apply_filters(queryset: QuerySet, filters: Dict[str, Any]) -> QuerySet`
    - Aplica filtros dinámicos al queryset
    - Soporta: status, user_id, invoice_id, advisor_id, payment_method, start_date, end_date, search

## Uso

### Ejemplo 1: Crear un Pago

```python
from apps.pagos.infrastructure.repository.payment_repository import PaymentRepository

repository = PaymentRepository()

# Datos del pago
payment_data = {
    'invoice_id': 123,
    'user_id': 456,
    'advisor_id': 789,
    'amount': Decimal('500.00'),
    'currency': 'USD',
    'payment_method': 'BT',
    'payment_reference_number': 'REF-123456',
    'payer_name': 'Juan Pérez',
    'status': 'P'
}

# Asignaciones opcionales
allocations = [
    {
        'invoice_detail_id': 1,
        'concept_id': 10,
        'amount_applied': Decimal('300.00'),
        'status': 'PAID'
    },
    {
        'invoice_detail_id': 2,
        'concept_id': 11,
        'amount_applied': Decimal('200.00'),
        'status': 'PAID'
    }
]

payment = repository.create(payment_data, allocations)
print(f"Pago creado: {payment.payment_number}")
```

### Ejemplo 2: Verificar un Pago

```python
from datetime import date
from apps.pagos.infrastructure.repository.payment_repository import PaymentRepository

repository = PaymentRepository()

# Verificar pago con fecha específica
payment = repository.verify(payment_id=123, verification_date=date.today())
print(f"Pago verificado: {payment.payment_number}")

# O verificar con fecha automática (hoy)
payment = repository.verify(payment_id=123)
```

### Ejemplo 3: Listar Pagos con Filtros

```python
from apps.pagos.infrastructure.repository.payment_repository import PaymentRepository

repository = PaymentRepository()

# Filtros
filters = {
    'status': 'V',  # Verificados
    'start_date': date(2026, 1, 1),
    'end_date': date(2026, 1, 31),
    'advisor_id': 789,
    'search': 'Juan'
}

payments = repository.list_all(filters)
for payment in payments:
    print(f"{payment.payment_number} - ${payment.amount}")
```

### Ejemplo 4: Calcular Total de Pagos

```python
from apps.pagos.infrastructure.repository.payment_repository import PaymentRepository

repository = PaymentRepository()

# Total de pagos verificados de una factura
total = repository.calculate_total_payments_by_invoice(invoice_id=123)
print(f"Total pagado: ${total}")
```

### Ejemplo 5: Anular un Pago

```python
from apps.pagos.infrastructure.repository.payment_repository import PaymentRepository

repository = PaymentRepository()

success = repository.cancel(payment_id=123)
if success:
    print("Pago anulado correctamente")
```

## Estados de Pago

| Código | Descripción             |
|--------|-------------------------|
| P      | Pendiente por verificar |
| D      | Disponible              |
| V      | Verificado              |
| R      | Rechazado               |
| X      | Anulado                 |

## Métodos de Pago

| Código | Descripción   |
|--------|---------------|
| PP     | PayPal        |
| ST     | Stripe        |
| TC     | Credit Card   |
| TD     | Debit Card    |
| BT     | Bank Transfer |
| EF     | Cash          |
| CH     | Check         |
| EX     | Exonerated    |
| OT     | Other         |

## Validaciones

1. **No se pueden actualizar pagos anulados**: El método `update` valida que el estado no sea 'X'
2. **Solo se pueden verificar pagos pendientes o disponibles**: Estados 'P' o 'D'
3. **Solo se pueden rechazar pagos pendientes o disponibles**: Estados 'P' o 'D'
4. **No se puede anular un pago ya anulado**: El método `cancel` valida el estado actual

## Relaciones

- **Payment -> Invoice**: ForeignKey a Invoice (PROTECT)
- **Payment -> User**: ForeignKey a Usuarios (PROTECT)
- **Payment -> Advisor**: ForeignKey a Usuarios (PROTECT, nullable)
- **PaymentAllocation -> Payment**: ForeignKey (PROTECT)
- **PaymentAllocation -> InvoiceDetail**: ForeignKey (PROTECT)
- **PaymentAllocation -> PaymentConcept**: ForeignKey (PROTECT)

## Optimizaciones

1. **Select Related**: Carga relaciones ForeignKey en una sola query
2. **Prefetch Related**: Carga relaciones ManyToMany y reverse FK eficientemente
3. **Bulk Create**: Crea asignaciones en bloque para mejor performance
4. **Índices**: Campos indexados: `payment_number`, `invoice`, `status`
5. **Anotaciones**: Calcula campos derivados en la base de datos

## Integración con Use Cases

El repositorio está diseñado para ser usado desde la capa de aplicación (use cases):

```python
# apps/pagos/application/use_cases/create_payment_exonerated.py

from apps.pagos.infrastructure.repository.payment_repository import PaymentRepository


class CreatePaymentUseCase:
    def __init__(self):
        self.repository = PaymentRepository()

    def execute(self, payment_data, allocations=None):
        # Validaciones de negocio
        self._validate_business_rules(payment_data)

        # Crear pago usando repositorio
        payment = self.repository.create(payment_data, allocations)

        return payment
```

## Notas

- Los métodos aceptan diccionarios para facilitar la serialización desde APIs
- Todas las operaciones de escritura usan transacciones atómicas
- Las validaciones de negocio complejas deben implementarse en los use cases
- El repositorio solo maneja persistencia y consultas básicas

