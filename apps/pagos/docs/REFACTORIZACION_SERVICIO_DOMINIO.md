# Resumen: Refactorización del Servicio de Dominio de Pagos

## 📅 Fecha

2026-01-12

## 🎯 Objetivo

Refactorizar el `PaymentDomainService` para utilizar repositorios en lugar de acceso directo a modelos, siguiendo los
principios de Clean Architecture.

## ✅ Cambios Realizados

### 1. Creación del PaymentDomainService

**Archivo**: `apps/pagos/domain/interface/services/payment_service.py`

**Antes**: No existía
**Después**: Servicio de dominio que:

- Convierte IDs a instancias de modelos
- Valida la existencia de entidades relacionadas
- Usa repositorios en lugar de acceso directo a modelos

### 2. Repositorios Utilizados

#### UsersRepository

```python
# Ubicación: apps/orden_pagos/infrastructure/repository/users_repository.py
- get_user_by_id(user_id) -> Usuarios
```

#### InvoiceRepository

```python
# Ubicación: apps/billing/infrastructure/repository/invoice_repository.py
- get_by_id(invoice_id) -> Invoice
```

#### PaymentConceptRepository

```python
# Ubicación: apps/orden_pagos/infrastructure/repository/payment_concept_repository.py
- get_concept_by_id(concept_id) -> PaymentConcept
```

### 3. Actualización del PaymentRepository

**Archivo**: `apps/pagos/infrastructure/repository/payment_repository.py`

**Cambios**:

- ✅ Agregado `PaymentDomainService` como dependencia
- ✅ Método `create()` ahora usa `convert_ids_to_instances()`
- ✅ Método `update()` ahora usa `convert_ids_to_instances()`
- ✅ Eliminados métodos `_normalize_payment_data()` y `_normalize_allocation_data()`
- ✅ El método `_create_payment_allocations()` simplificado

**Antes**:

```python
def create(self, payment_data: Dict[str, Any], allocations: List[Dict[str, Any]] = None):
    # Convertía instancias a IDs manualmente
    payment_kwargs = self._normalize_payment_data(payment_data)
    payment = Payment.objects.create(**payment_kwargs)
```

**Después**:

```python
def create(self, payment_data: Dict[str, Any], allocations: List[Dict[str, Any]] = None):
    # Convierte IDs a instancias usando el servicio de dominio
    payment_kwargs = self.domain_service.convert_ids_to_instances(payment_data)
    payment = Payment.objects.create(**payment_kwargs)
```

## 🔄 Flujo de Conversión

### Entrada (Caso de Uso)

```python
payment_data = {
    'user_id': 123,           # ID
    'advisor_id': 45,         # ID
    'invoice_id': 789,        # ID
    'amount': Decimal('500.00'),
    'payment_method': 'BT'
}
```

### Proceso (PaymentDomainService)

```python
# Convierte IDs a instancias usando repositorios
converted_data = {
    'user': <Usuarios: id=123>,          # Instancia
    'advisor': <Usuarios: id=45>,        # Instancia
    'invoice': <Invoice: id=789>,        # Instancia
    'amount': Decimal('500.00'),
    'payment_method': 'BT'
}
```

### Resultado (PaymentRepository)

```python
# Crea el pago con instancias reales
Payment.objects.create(**converted_data)
```

## 📊 Beneficios

### 1. Separación de Responsabilidades

- ✅ **Caso de Uso**: Lógica de negocio de alto nivel
- ✅ **Repositorio**: Persistencia de datos
- ✅ **Servicio de Dominio**: Conversión y validación

### 2. Uso de Repositorios

- ✅ No se accede directamente a `Usuarios.objects.get()`
- ✅ Se usa `UsersRepository.get_user_by_id()`
- ✅ Facilita el testing con mocks

### 3. Validación Centralizada

- ✅ Valida existencia de usuarios
- ✅ Valida existencia de facturas
- ✅ Valida existencia de conceptos de pago
- ✅ Lanza `ValidationError` con mensajes descriptivos

### 4. Consistencia

- ✅ Mismo patrón usado en `InvoiceRepository`
- ✅ Reutilizable en otros casos de uso

## 🔍 Comparación: Antes vs Después

### Antes (Acceso Directo a Modelos)

```python
# ❌ Acceso directo desde el repositorio
try:
    user = Usuarios.objects.get(pk=user_id)
except Usuarios.DoesNotExist:
    raise ValidationError(...)
```

**Problemas**:

- Dificulta el testing (no se puede mockear fácilmente)
- Acopla el repositorio con la implementación de Django ORM
- Duplica código de validación

### Después (Uso de Repositorios)

```python
# ✅ Uso de repositorio
user = self.users_repository.get_user_by_id(user_id)
if not user:
    raise ValidationError(...)
```

**Ventajas**:

- Fácil de testear (se mockea el repositorio)
- Desacoplado de la implementación de Django
- Código de validación centralizado

## 📝 Documentación Creada

1. **GUIA_SERVICIO_DOMINIO_PAGOS.md**
    - Descripción completa del servicio
    - Ejemplos de uso para ambos flujos
    - Diagrama de arquitectura
    - Lista de validaciones automáticas
    - Errores comunes y soluciones

2. **Actualización de README.md**
    - Agregada referencia a la nueva guía

## 🧪 Testing

El servicio está listo para ser testeado:

```python
from unittest.mock import Mock
from apps.pagos.domain.interface.services import PaymentDomainService


def test_convert_ids_to_instances():
    # Mock de repositorios
    service = PaymentDomainService()
    service.users_repository = Mock()
    service.invoice_repository = Mock()

    # Configurar mocks
    service.users_repository.get_user_by_id.return_value = Mock(id=123)

    # Test
    result = service.convert_ids_to_instances({'user_id': 123})
    assert 'user' in result
```

## ⚡ Método `bulk_create`

El método `bulk_create()` de Django ORM crea múltiples registros en **una sola consulta SQL**:

```python
# ❌ Ineficiente (N consultas)
for allocation in allocations:
    PaymentAllocation.objects.create(**allocation)

# ✅ Eficiente (1 consulta)
PaymentAllocation.objects.bulk_create(allocation_objects)
```

**Ventajas**:

- 🚀 Mucho más rápido con grandes volúmenes
- 📉 Reduce carga en la base de datos
- ✅ Se ejecuta dentro de `transaction.atomic()`

## 🎯 Casos de Uso Soportados

### 1. Pago Exonerado (con Factura)

```python
payment_data = {
    'user_id': 123,
    'invoice_id': 789,      # ✅ Factura ya existe
    'payment_method': 'EX',
    'amount': Decimal('0.00')
}
```

### 2. Pago Anticipado (sin Factura)

```python
payment_data = {
    'user_id': 123,
    'invoice_id': None,     # ✅ Sin factura aún
    'payment_method': 'BT',
    'amount': Decimal('500.00')
}
```

## 🚀 Próximos Pasos

1. ✅ **Completado**: Refactorización del servicio de dominio
2. ✅ **Completado**: Documentación completa
3. ⏳ **Pendiente**: Crear tests unitarios para `PaymentDomainService`
4. ⏳ **Pendiente**: Crear tests de integración para `PaymentRepository`
5. ⏳ **Pendiente**: Documentar el caso de uso `CreatePayment` completo

## 📦 Archivos Modificados/Creados

### Creados

- ✅ `apps/pagos/domain/interface/services/__init__.py`
- ✅ `apps/pagos/domain/interface/services/payment_service.py`
- ✅ `apps/pagos/docs/GUIA_SERVICIO_DOMINIO_PAGOS.md`
- ✅ `apps/pagos/docs/REFACTORIZACION_SERVICIO_DOMINIO.md` (este archivo)

### Modificados

- ✅ `apps/pagos/infrastructure/repository/payment_repository.py`
- ✅ `apps/pagos/docs/README.md`

## 💡 Conclusión

La refactorización mejora significativamente:

- **Arquitectura**: Sigue principios de Clean Architecture
- **Testabilidad**: Repositorios son fáciles de mockear
- **Mantenibilidad**: Lógica centralizada y reutilizable
- **Consistencia**: Mismo patrón en toda la aplicación

El sistema ahora está preparado para manejar ambos flujos de pago (con y sin factura) de forma robusta y escalable.

