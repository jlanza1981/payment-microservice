# Arquitectura de Schemas y Serializers de Pydantic

Este documento explica la separación entre **Schemas de Pydantic** y **Model Serializers personalizados**.

## Estructura de Archivos

```
apps/orden_pagos/presentation/api/schemas/
├── __init__.py                    # Exports públicos
├── input_schemas.py               # Schemas de entrada (request)
├── output_schemas.py              # Schemas de salida (response)
├── filter_schemas.py              # Schemas para filtros
└── model_serializers.py           # 🆕 Serializers personalizados para Django models
```

## ¿Por qué separar los Model Serializers?

### Antes (Mezclado)

```python
# output_schemas_payment_order.py - TODO mezclado
class PaymentOrderDetailSchema(Schema):
    id: int
    payment_concept: int

    @model_serializer(mode='wrap')
    def serialize_model(self, serializer):
        # 80 líneas de lógica de transformación aquí
        payment_concept = getattr(obj, 'payment_concept', None)
        payment_concept_id = payment_concept.id if hasattr(payment_concept, 'id') else payment_concept
        # ... más lógica
```

**Problemas**:

- ❌ Mezcla responsabilidades (definición de schema + lógica de transformación)
- ❌ Difícil de testear
- ❌ Código muy largo y difícil de mantener
- ❌ Confunde schemas de Pydantic con serializers

### Después (Separado)

```python
# output_schemas_payment_order.py - SOLO definición de schemas
class PaymentOrderDetailSchema(Schema):
    id: int
    payment_concept: int

    @model_serializer(mode='wrap')
    def serialize_model(self, serializer):
        if isinstance(self, dict):
            return serializer(self)
        return PaymentOrderDetailModelSerializer.serialize(self)
```

```python
# model_serializers_payment_order.py - SOLO lógica de transformación
class PaymentOrderDetailModelSerializer:
    @staticmethod
    def serialize(obj) -> dict:
        # Toda la lógica de transformación aquí
        payment_concept = getattr(obj, 'payment_concept', None)
        payment_concept_id = payment_concept.id if hasattr(payment_concept, 'id') else payment_concept
        # ... más lógica
        return data
```

**Beneficios**:

- ✅ Separación clara de responsabilidades
- ✅ Fácil de testear cada parte independientemente
- ✅ Código más limpio y mantenible
- ✅ Reutilizable en otros contextos (ej: cálculo de totales)

## Componentes

### 1. Output Schemas (`output_schemas.py`)

**Responsabilidad**: Definir la estructura de los datos de respuesta

```python
class PaymentOrderDetailSchema(Schema):
    """Define QUÉ campos tiene la respuesta"""
    id: int
    payment_concept: int
    payment_concept_name: Optional[str]

    # ... más campos

    @model_serializer(mode='wrap')
    def serialize_model(self, serializer):
        """Delega la transformación al serializer"""
        return PaymentOrderDetailModelSerializer.serialize(self)
```

### 2. Model Serializers (`model_serializers.py`)

**Responsabilidad**: Transformar modelos Django a diccionarios con IDs

```python
class PaymentOrderDetailModelSerializer:
    """Define CÓMO transformar el modelo Django"""

    @staticmethod
    def serialize(obj) -> dict:
        """Convierte instancias Django a dict con IDs"""
        # Extraer IDs de ForeignKeys
        payment_concept = getattr(obj, 'payment_concept', None)
        payment_concept_id = payment_concept.id if payment_concept else None

        return {
            'id': obj.id,
            'payment_concept': payment_concept_id,  # ID, no instancia
            # ... más campos
        }

    @staticmethod
    def calculate_sub_total(obj) -> Decimal:
        """Métodos auxiliares para cálculos"""
        # Lógica de cálculo
        return subtotal
```

## Casos de Uso

### Caso 1: Serialización automática en API

```python
# En el router de Django Ninja
@router.get("/{order_id}/", response=PaymentOrderSchema)
def get_order(request, order_id: int):
    order = repository.get_by_id(order_id)
    return order  # ✅ El schema usa el model_serializer automáticamente
```

### Caso 2: Cálculo de totales manualmente

```python
# En cualquier parte del código
from apps.orden_pagos.presentation.api.schemas import PaymentOrderDetailModelSerializer

details = order.payment_order_details.all()
total = sum(
    PaymentOrderDetailModelSerializer.calculate_sub_total(detail)
    for detail in details
)
```

### Caso 3: Testing unitario

```python
# test_model_serializers.py
def test_serialize_payment_detail():
    detail = PaymentOrderDetails.objects.create(...)
    result = PaymentOrderDetailModelSerializer.serialize(detail)

    assert result['payment_concept'] == detail.payment_concept.id
    assert isinstance(result['payment_concept'], int)  # No instancia
```

## Serializers Disponibles

### `PaymentOrderDetailModelSerializer`

Transforma `PaymentOrderDetails` a diccionario:

- Convierte `payment_concept` (instancia) → ID (int)
- Convierte `type_administrative_cost` (instancia) → ID (int)
- Calcula `sub_total` con descuentos

**Métodos**:

- `serialize(obj) -> dict`: Serialización completa
- `calculate_sub_total(obj) -> Decimal`: Solo cálculo de subtotal

### `PaymentOrderProgramModelSerializer`

Transforma `PaymentOrderProgram` a diccionario:

- Convierte todas las ForeignKeys a IDs:
    - `program_type`, `institution`, `city` → int
    - `country` → str (código de 3 chars)
    - `program`, `intensity`, `material_cost_type` → int (opcional)
- Calcula campos derivados:
    - `tuition_subtotal`: precio_semana × duración
    - `total_material`: costo de materiales
    - `total_enrollment`: matrícula + materiales

**Métodos**:

- `serialize(obj) -> dict`: Serialización completa
- `calculate_tuition_subtotal(obj) -> Decimal`: Solo matrícula
- `calculate_total_material(obj) -> Decimal`: Solo materiales
- `calculate_total_enrollment(obj) -> Decimal`: Total completo

## Flujo de Datos

```
1. Django ORM carga modelo con ForeignKeys (instancias)
   PaymentOrder.objects.get(id=1)
   ↓
2. Schema Pydantic recibe el modelo
   PaymentOrderSchema.model_validate(order)
   ↓
3. @model_serializer intercepta la serialización
   PaymentOrderDetailSchema.serialize_model()
   ↓
4. Delega al Model Serializer
   PaymentOrderDetailModelSerializer.serialize(obj)
   ↓
5. Extrae IDs de las instancias
   payment_concept.id → int
   ↓
6. Pydantic valida el diccionario
   {'payment_concept': 1}  ✅ int válido
   ↓
7. JSON response con IDs
   {"payment_concept": 1}
```

## Diferencias con DRF Serializers

| Aspecto        | DRF Serializers               | Pydantic Model Serializers  |
|----------------|-------------------------------|-----------------------------|
| **Ubicación**  | `infrastructure/serializers/` | `presentation/api/schemas/` |
| **Tecnología** | Django REST Framework         | Pydantic v2                 |
| **Framework**  | ViewSets (viejo)              | Django Ninja (nuevo)        |
| **Propósito**  | API DRF (deprecada)           | API Ninja (actual)          |
| **Estado**     | Mantener temporalmente        | En uso activo               |

## Migración en Progreso

Actualmente coexisten:

- ✅ **API nueva**: Django Ninja + Pydantic (usar este)
- ⚠️ **API vieja**: DRF ViewSets (mantener hasta completar migración)

Una vez completada la migración a Django Ninja:

1. Eliminar `infrastructure/serializers/payment_order_serializer.py`
2. Eliminar `presentation/views/payment_order_viewset.py`
3. Mantener solo los schemas de Pydantic

## Buenas Prácticas

### ✅ Hacer

- Mantener los schemas ligeros (solo definición de campos)
- Poner la lógica de transformación en model_serializers
- Reutilizar métodos de cálculo entre schemas
- Testear los serializers independientemente

### ❌ Evitar

- Mezclar lógica de transformación en el schema
- Duplicar código de cálculo
- Hacer transformaciones complejas en el `@model_serializer`
- Crear dependencias circulares

## Ejemplo de Test

```python
# tests/test_model_serializers.py
import pytest
from decimal import Decimal
from apps.orden_pagos.presentation.api.schemas import PaymentOrderDetailModelSerializer


@pytest.mark.django_db
def test_serialize_payment_detail_with_discount():
    # Arrange
    detail = PaymentOrderDetails.objects.create(
        amount=Decimal('100.00'),
        discount_type='P',
        discount_amount=Decimal('10.00'),
        payment_concept=payment_concept_fixture,
    )

    # Act
    result = PaymentOrderDetailModelSerializer.serialize(detail)

    # Assert
    assert result['amount'] == Decimal('100.00')
    assert result['sub_total'] == Decimal('90.00')  # 10% descuento
    assert result['payment_concept'] == payment_concept_fixture.id
    assert isinstance(result['payment_concept'], int)
```

## Conclusión

La separación de schemas y model_serializers proporciona:

- 🎯 Código más limpio y organizado
- 🧪 Mejor testabilidad
- 🔧 Mayor mantenibilidad
- ♻️ Reutilización de lógica
- 📚 Código autodocumentado

Esta arquitectura sigue los principios SOLID y facilita el crecimiento futuro del sistema.

