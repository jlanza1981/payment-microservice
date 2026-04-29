# Refactorización: Cálculo de Inscripción con DDD

## 📋 Resumen

Se ha refactorizado el método `CalcularInscripcion` a una arquitectura hexagonal siguiendo los principios DDD (Domain-Driven Design) utilizados en la app `orden_pagos`.

## 🏗️ Estructura Implementada

### 1. **Repositorio** - Capa de Infraestructura
**Archivo**: `apps/orden_pagos/infrastructure/repository/registration_fee_repository.py`

Responsabilidades:
- Consultar precios de inscripción por sede (`PreciosFijosSedes`)
- Obtener moneda del país de la sede
- Abstraer el acceso a datos

Métodos principales:
- `get_currency_by_institution_and_city()`: Obtiene el símbolo de moneda
- `get_registration_price_by_sede()`: Consulta precios fijos de inscripción

### 2. **Caso de Uso** - Capa de Aplicación
**Archivo**: `apps/orden_pagos/application/use_cases/calculate_registration_fee.py`

Responsabilidades:
- Orquesta la lógica de negocio del cálculo de inscripción
- Aplica descuentos porcentuales
- Formatea los montos para la respuesta

Método principal:
- `execute(institution_id, city_id, program_type_id)`: Calcula inscripción con descuentos

### 3. **Schema de Input** - Capa de Presentación
**Archivo**: `apps/orden_pagos/presentation/api/schemas/input_schemas_payment_concepts.py`

Se actualizó para incluir:
- `institution_id`: ID de la institución
- `city_id`: ID de la ciudad
- `program_type_id`: ID del tipo de programa (categoría)

### 4. **Router** - Capa de Presentación
**Archivo**: `apps/orden_pagos/presentation/api/payment_concept_router.py`

Se integró el nuevo caso de uso en el endpoint:
```
POST /additional-data/{concept_id}/
```

## 🔄 Flujo de Datos

```
Client Request (POST)
    ↓
payment_concept_router.get_additional_data_for_concept()
    ↓
CalculateRegistrationFeeUseCase.execute()
    ↓
RegistrationFeeRepository (consultas a DB)
    ↓
Response JSON
```

## 📝 Diferencias con el Método Original

### ❌ Método Original
```python
def CalcularInscripcion(planilla, institucion, ciudad, tipo_programa):
    # Lógica de negocio mezclada con acceso a datos
    # Consultas directas a modelos Django
    # Sin separación de responsabilidades
```

### ✅ Método Refactorizado (DDD)
```python
# Repositorio: Acceso a datos
class RegistrationFeeRepository:
    def get_registration_price_by_sede(...)

# Caso de Uso: Lógica de negocio
class CalculateRegistrationFeeUseCase:
    def execute(...)

# Router: Presentación
def get_additional_data_for_concept(...)
```

## 🎯 Uso del Endpoint

### Request
```http
POST /api/orden-pagos/payment-concepts/additional-data/1/
Content-Type: application/json
Authorization: Bearer <token>

{
  "country_origin_id": "USA",
  "institution_id": 123,
  "city_id": 456,
  "program_type_id": 789
}
```

### Response (Código 'I' - Inscripción)
```json
{
  "registration_fee": {
    "amount": "1,500.00",
    "discount_percentage": 10,
    "fixed_discount": "0.00",
    "currency": "USD",
    "total_amount": "1,350.00",
    "discounts": [
      {
        "name": "Descuento LC",
        "percentage": 10,
        "discount_amount": "150.00",
        "type": "percentage"
      }
    ],
    "registration_name": "Inscripción Premium"
  }
}
```

## 🚀 Beneficios de la Refactorización

1. **Separación de Responsabilidades**: Cada capa tiene una responsabilidad clara
2. **Testeable**: Los casos de uso pueden ser testeados independientemente
3. **Mantenible**: Cambios en la lógica o en el acceso a datos no afectan otras capas
4. **Reutilizable**: El repositorio y caso de uso pueden ser usados en otros contextos
5. **Escalable**: Fácil agregar nuevos cálculos o reglas de negocio

## 📦 Archivos Modificados

- ✅ `registration_fee_repository.py` (nuevo)
- ✅ `calculate_registration_fee.py` (nuevo)
- ✅ `__init__.py` (actualizado - exports)
- ✅ `payment_concept_router.py` (actualizado - integración)
- ✅ `input_schemas_payment_concepts.py` (actualizado - nuevos campos)

## 🔍 Notas Importantes

- **Se eliminó la lógica de "planilla"** según lo solicitado
- Los descuentos fijos quedaron en `0.00` (no aplicables en este contexto)
- La moneda por defecto es `USD` si no se encuentra la sede
- Los montos se formatean con separadores de miles (ej: `1,500.00`)

## 🧪 Testing Recomendado

```python
# Test del repositorio
def test_get_registration_price_by_sede():
    repo = RegistrationFeeRepository()
    result = repo.get_registration_price_by_sede(123, 456, 789)
    assert result is not None

# Test del caso de uso
def test_calculate_registration_fee():
    repo = Mock(RegistrationFeeRepository)
    use_case = CalculateRegistrationFeeUseCase(repo)
    result = use_case.execute(123, 456, 789)
    assert 'total_amount' in result
```
