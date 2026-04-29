# ✅ Implementación de Excepción para Intensidad Requerida

## 🎯 Cambio Implementado

Se ha implementado correctamente una **excepción personalizada** que **detiene el flujo de ejecución** cuando la intensidad es requerida pero no se proporciona para cursos de idiomas.

---

## 📦 Archivos Creados

### 1. **Módulo de Excepciones del Dominio** ✅
**Archivo**: `apps/orden_pagos/domain/exceptions.py`

```python
class IntensityRequiredException(Exception):
    """
    Excepción lanzada cuando se requiere una intensidad para calcular precios
    pero no se proporciona.
    """
    def __init__(self, message: str = "La intensidad es requerida para este programa"):
        self.message = message
        super().__init__(self.message)
```

**Otras excepciones incluidas**:
- `InvalidProgramTypeException`
- `PricingNotFoundException`

---

## 🔧 Archivos Modificados

### 1. **Repositorio** ✅
**Archivo**: `headquarters_pricing_repository.py`

**Antes**:
```python
if not intensity_id:
    result['error'] = 'La intensidad es requerida...'
    result['requires_intensity'] = True
    return result  # ❌ Continúa el flujo con valores vacíos
```

**Después**:
```python
if not intensity_id:
    raise IntensityRequiredException(
        "La intensidad es requerida para este programa"
    )  # ✅ Detiene la ejecución inmediatamente
```

### 2. **Caso de Uso: Matrícula** ✅
**Archivo**: `calculate_tuition_fee.py`

**Eliminado**:
```python
# Ya no es necesario verificar el error manualmente
if pricing.get('error') and pricing.get('requires_intensity'):
    return {...}  # ❌ Código eliminado
```

**Ahora**:
```python
# La excepción se propaga automáticamente
pricing = self.repository.get_language_course_pricing(...)
# Si no hay intensity_id, se lanza IntensityRequiredException
```

### 3. **Caso de Uso: Material** ✅
**Archivo**: `calculate_material_cost.py`

**Eliminado**:
```python
if not intensity_id:
    return self._get_default_material_response()  # ❌ Código eliminado
```

**Ahora**:
```python
# La excepción se propaga automáticamente
pricing = self.repository.get_language_course_pricing(...)
# Si no hay intensity_id, se lanza IntensityRequiredException
```

### 4. **Router** ✅
**Archivo**: `payment_concept_router.py`

**Agregado manejo de excepción**:
```python
# Para Matrícula (M) y Extensión (E)
try:
    params = TuitionCalculationParams(...)
    tuition_fee = CalculateTuitionFeeUseCase(repository).execute(params)
    response_data['tuition_fee'] = tuition_fee
except IntensityRequiredException as e:
    return 400, {
        'error': str(e),
        'requires_intensity': True
    }

# Para Material (P)
try:
    material_cost = CalculateMaterialCostUseCase(repository).execute(...)
    response_data['material_cost'] = material_cost
except IntensityRequiredException as e:
    return 400, {
        'error': str(e),
        'requires_intensity': True
    }
```

---

## 📋 Respuesta del API

### Caso 1: Sin Intensidad (ERROR 400)

**Request**:
```json
POST /api/orden-pagos/payment-concepts/additional-data/M/
{
  "country_origin_id": "USA",
  "weeks": 12,
  "duration_type": "S",
  "institution_id": 15,
  "city_id": 120,
  "category_id": 3,
  "program_id": 45,
  "intensity_id": null  // ❌ Falta intensidad
}
```

**Response (400 Bad Request)**:
```json
{
  "error": "La intensidad es requerida para este programa",
  "requires_intensity": true
}
```

**Status Code**: `400 Bad Request` ✅

### Caso 2: Con Intensidad (ÉXITO 200)

**Request**:
```json
POST /api/orden-pagos/payment-concepts/additional-data/M/
{
  "country_origin_id": "USA",
  "weeks": 12,
  "duration_type": "S",
  "institution_id": 15,
  "city_id": 120,
  "category_id": 3,
  "program_id": 45,
  "intensity_id": 2  // ✅ Intensidad proporcionada
}
```

**Response (200 OK)**:
```json
{
  "tuition_fee": {
    "duration_type": "S",
    "weeks": 12,
    "lc_price": "3,600.00",
    "total_tuition": "43,200.00",
    "currency": "USD",
    "is_college": false
  }
}
```

**Status Code**: `200 OK` ✅

---

## 🎨 Manejo en el Frontend

### JavaScript/React:

```javascript
async function calculateTuition(data) {
  try {
    const response = await fetch('/api/orden-pagos/payment-concepts/additional-data/M/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(data)
    });
    
    const result = await response.json();
    
    // Verificar status code
    if (response.status === 400) {
      if (result.requires_intensity) {
        // Error específico de intensidad
        alert(result.error);
        showIntensitySelector();  // Mostrar selector
      } else {
        // Otro error de validación
        alert(result.error);
      }
      return null;
    }
    
    // Éxito
    return result.tuition_fee;
    
  } catch (error) {
    console.error('Error calculando matrícula:', error);
    alert('Error de conexión');
  }
}
```

### Vue.js:

```vue
<template>
  <div>
    <div v-if="error" class="alert alert-danger">
      {{ error }}
      <select v-if="requiresIntensity" 
              v-model="selectedIntensity"
              @change="recalculate">
        <option value="">Seleccione intensidad</option>
        <option v-for="intensity in intensities" 
                :key="intensity.id" 
                :value="intensity.id">
          {{ intensity.name }}
        </option>
      </select>
    </div>
    
    <div v-else-if="tuitionData">
      <p>Total: {{ tuitionData.total_tuition }} {{ tuitionData.currency }}</p>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      tuitionData: null,
      error: null,
      requiresIntensity: false
    }
  },
  methods: {
    async calculateTuition() {
      try {
        const response = await this.$http.post('/api/.../M/', this.formData);
        
        if (response.status === 200) {
          this.tuitionData = response.data.tuition_fee;
          this.error = null;
          this.requiresIntensity = false;
        }
        
      } catch (error) {
        if (error.response?.status === 400) {
          const data = error.response.data;
          this.error = data.error;
          this.requiresIntensity = data.requires_intensity || false;
        }
      }
    }
  }
}
</script>
```

---

## 🏗️ Flujo de Ejecución

### Antes (Con Mensaje):
```
1. Frontend solicita cálculo sin intensity_id
2. Repositorio detecta falta de intensidad
3. Retorna diccionario con error
4. Caso de uso verifica error
5. Retorna diccionario con error al router
6. Router retorna 200 OK con error en el body ❌
7. Frontend debe verificar si hay error en respuesta exitosa ❌
```

### Después (Con Excepción):
```
1. Frontend solicita cálculo sin intensity_id
2. Repositorio detecta falta de intensidad
3. Lanza IntensityRequiredException ✅
4. Excepción se propaga automáticamente
5. Router captura excepción
6. Router retorna 400 Bad Request ✅
7. Frontend recibe error HTTP estándar ✅
```

---

## ✨ Beneficios de Usar Excepciones

### 1. **Detiene el Flujo Inmediatamente** ✅
- No continúa procesando con datos inválidos
- No hay cálculos incorrectos

### 2. **Status Code HTTP Apropiado** ✅
- `400 Bad Request` en lugar de `200 OK`
- Semántica HTTP correcta

### 3. **Código Más Limpio** ✅
- No hay verificaciones if/else anidadas
- La excepción se propaga automáticamente

### 4. **Validación Centralizada** ✅
- La validación está en un solo lugar (repositorio)
- No se duplica lógica en cada capa

### 5. **Fácil de Extender** ✅
- Se pueden agregar más excepciones
- Cada excepción tiene su propósito

---

## 🧪 Testing

### Test de la Excepción:

```python
import pytest
from apps.orden_pagos.domain.exceptions.intensity_exceptions import IntensityRequiredException
from apps.orden_pagos.infrastructure.repository.headquarters_pricing_repository import HeadquartersPriceRepository


def test_raises_exception_when_no_intensity():
    """Verifica que se lanza excepción cuando no hay intensidad."""
    repo = HeadquartersPriceRepository()

    with pytest.raises(IntensityRequiredException) as exc_info:
        repo.get_language_course_pricing(
            course_id=45,
            institution_id=15,
            city_id=120,
            category_id=3,
            intensity_id=None,  # Sin intensidad
            country_id='USA',
            weeks=12
        )

    assert "La intensidad es requerida" in str(exc_info.value)
```

### Test del Router:

```python
from unittest.mock import Mock, patch
from apps.orden_pagos.domain.exceptions.intensity_exceptions import IntensityRequiredException


def test_router_catches_intensity_exception(client):
    """Verifica que el router captura la excepción y retorna 400."""

    with patch(
            'apps.orden_pagos.infrastructure.repository.headquarters_pricing_repository.HeadquartersPriceRepository.get_language_course_pricing') as mock:
        mock.side_effect = IntensityRequiredException("La intensidad es requerida")

        response = client.post('/api/orden-pagos/payment-concepts/additional-data/M/', json={
            'country_origin_id': 'USA',
            'weeks': 12,
            'duration_type': 'S',
            'institution_id': 15,
            'city_id': 120,
            'category_id': 3,
            'program_id': 45,
            'intensity_id': None
        })

        assert response.status_code == 400
        assert response.json()['requires_intensity'] is True
        assert 'La intensidad es requerida' in response.json()['error']
```

---

## 📊 Comparación

| Aspecto | Antes (Mensaje) | Después (Excepción) |
|---------|-----------------|---------------------|
| **Detiene flujo** | ❌ No, continúa | ✅ Sí, inmediato |
| **Status HTTP** | ❌ 200 OK | ✅ 400 Bad Request |
| **Código limpio** | ❌ If/else anidados | ✅ Try/except simple |
| **Propagación** | ❌ Manual | ✅ Automática |
| **Validación** | ❌ En múltiples capas | ✅ Centralizada |
| **Semántica** | ❌ Incorrecta | ✅ Correcta |

---

## 🎯 Resumen

### ✅ Implementado Correctamente:
1. ✅ Excepción personalizada `IntensityRequiredException`
2. ✅ Lanzamiento en el repositorio
3. ✅ Propagación automática en casos de uso
4. ✅ Captura en el router con status 400
5. ✅ Mensaje claro para el frontend
6. ✅ Flag `requires_intensity` para lógica condicional
7. ✅ Sin errores de sintaxis

### 🚀 Resultado:
- **El flujo se detiene inmediatamente** si no hay intensidad
- **No se realizan cálculos** con datos inválidos
- **Status HTTP 400** correcto
- **Mensaje claro** al usuario final

---

¡Excepción implementada exitosamente! 🎉
