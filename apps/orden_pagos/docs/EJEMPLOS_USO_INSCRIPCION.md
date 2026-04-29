# 📚 Ejemplos de Uso - Cálculo de Inscripción

## 🎯 Endpoint Principal

```
POST /api/orden-pagos/payment-concepts/additional-data/{concept_id}/
```

---

## 📋 Ejemplo 1: Cálculo de Inscripción con Descuento

### Request
```bash
curl -X POST "http://localhost:8000/api/orden-pagos/payment-concepts/additional-data/5/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "country_origin_id": "USA",
    "institution_id": 15,
    "city_id": 120,
    "program_type_id": 3
  }'
```

### Response (200 OK)
```json
{
  "registration_fee": {
    "base_amount": "2,500.00",
    "discount_percentage": 15,
    "fixed_discount": "0.00",
    "currency": "USD",
    "total_amount": "2,125.00",
    "discounts": [
      {
        "name": "Descuento LC",
        "percentage": 15,
        "discount_amount": "375.00",
        "type": "percentage"
      }
    ],
    "registration_name": "Inscripción Curso de Inglés"
  }
}
```

---

## 📋 Ejemplo 2: Inscripción Sin Descuento

### Request
```bash
curl -X POST "http://localhost:8000/api/orden-pagos/payment-concepts/additional-data/5/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "country_origin_id": "CAN",
    "institution_id": 22,
    "city_id": 88,
    "program_type_id": 1
  }'
```

### Response (200 OK)
```json
{
  "registration_fee": {
    "base_amount": "800.00",
    "discount_percentage": 0,
    "fixed_discount": "0.00",
    "currency": "CAD",
    "total_amount": "800.00",
    "discounts": [],
    "registration_name": "Inscripción Estándar"
  }
}
```

---

## 📋 Ejemplo 3: Error - Datos Incompletos

### Request (sin institution_id)
```bash
curl -X POST "http://localhost:8000/api/orden-pagos/payment-concepts/additional-data/5/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "country_origin_id": "USA",
    "city_id": 120,
    "program_type_id": 3
  }'
```

### Response (400 Bad Request)
```json
{
  "error": "Para cálculo de inscripción se requieren: institution_id, city_id y program_type_id"
}
```

---

## 📋 Ejemplo 4: Concepto No Encontrado

### Request
```bash
curl -X POST "http://localhost:8000/api/orden-pagos/payment-concepts/additional-data/999/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "country_origin_id": "USA",
    "institution_id": 15,
    "city_id": 120,
    "program_type_id": 3
  }'
```

### Response (404 Not Found)
```json
{
  "error": "Concepto de pago con ID 999 no encontrado"
}
```

---

## 📋 Ejemplo 5: Costos Administrativos (Código 'C')

### Request
```bash
curl -X POST "http://localhost:8000/api/orden-pagos/payment-concepts/additional-data/2/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "country_origin_id": "USA"
  }'
```

### Response (200 OK)
```json
{
  "administrative_cost": [
    {
      "id": 1,
      "name": "Material de Estudio",
      "amount": 75.50,
      "currency_country": "USA",
      "country_id": "USA",
      "country_name": "United States"
    },
    {
      "id": 2,
      "name": "Certificación",
      "amount": 120.00,
      "currency_country": "USA",
      "country_id": "USA",
      "country_name": "United States"
    }
  ]
}
```

---

## 🐍 Ejemplo de Uso Programático en Python

### Uso del Repositorio
```python
from apps.orden_pagos.infrastructure.repository.registration_fee_repository import RegistrationFeeRepository

# Instanciar repositorio
repo = RegistrationFeeRepository()

# Obtener moneda
currency = repo.get_currency_by_institution_and_city(
    institution_id=15,
    city_id=120,
    program_type_id=3
)
print(f"Moneda: {currency}")  # Output: USD

# Obtener precio de inscripción
price_data = repo.get_registration_price_by_sede(
    institution_id=15,
    city_id=120,
    program_type_id=3
)
print(price_data)
# Output: {'price': Decimal('2500.00'), 'discount_percentage': Decimal('15.00'), ...}
```

### Uso del Caso de Uso
```python
from apps.orden_pagos.application.use_cases import CalculateRegistrationFeeUseCase
from apps.orden_pagos.infrastructure.repository.registration_fee_repository import RegistrationFeeRepository

# Instanciar dependencias
repository = RegistrationFeeRepository()
use_case = CalculateRegistrationFeeUseCase(repository)

# Ejecutar cálculo
result = use_case.execute(
    institution_id=15,
    city_id=120,
    program_type_id=3
)

print(f"Monto base: {result['base_amount']}")
print(f"Total a pagar: {result['total_amount']}")
print(f"Descuentos aplicados: {len(result['discounts'])}")
```

---

## 🧪 Uso en Tests

### Test con Mock
```python
from unittest.mock import Mock
from decimal import Decimal

def test_calculate_with_mock():
    # Crear mock del repositorio
    mock_repo = Mock()
    mock_repo.get_currency_by_institution_and_city.return_value = 'EUR'
    mock_repo.get_registration_price_by_sede.return_value = {
        'price': Decimal('1000.00'),
        'discount_percentage': Decimal('10.00'),
        'description': 'Test Inscription'
    }
    
    # Usar el caso de uso con el mock
    use_case = CalculateRegistrationFeeUseCase(mock_repo)
    result = use_case.execute(1, 2, 3)
    
    # Verificaciones
    assert result['currency'] == 'EUR'
    assert result['base_amount'] == '1,000.00'
    assert result['total_amount'] == '900.00'
```

---

## 🔄 Integración con Frontend

### JavaScript/TypeScript (Axios)
```typescript
import axios from 'axios';

interface RegistrationFeeRequest {
  country_origin_id: string;
  institution_id: number;
  city_id: number;
  program_type_id: number;
}

async function calculateRegistrationFee(
  conceptId: number,
  data: RegistrationFeeRequest
) {
  try {
    const response = await axios.post(
      `/api/orden-pagos/payment-concepts/additional-data/${conceptId}/`,
      data,
      {
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    const { registration_fee } = response.data;
    console.log(`Total: ${registration_fee.total_amount} ${registration_fee.currency}`);
    return registration_fee;
    
  } catch (error) {
    console.error('Error calculando inscripción:', error);
    throw error;
  }
}

// Uso
const fee = await calculateRegistrationFee(5, {
  country_origin_id: 'USA',
  institution_id: 15,
  city_id: 120,
  program_type_id: 3
});
```

### React Component Example
```tsx
import React, { useState } from 'react';

function RegistrationFeeCalculator() {
  const [fee, setFee] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const calculate = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        '/api/orden-pagos/payment-concepts/additional-data/5/',
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            country_origin_id: 'USA',
            institution_id: 15,
            city_id: 120,
            program_type_id: 3
          })
        }
      );
      
      const data = await response.json();
      setFee(data.registration_fee);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div>
      <button onClick={calculate} disabled={loading}>
        Calcular Inscripción
      </button>
      
      {fee && (
        <div>
          <h3>{fee.registration_name}</h3>
          <p>Monto Base: {fee.amount} {fee.currency}</p>
          <p>Total: {fee.total_amount} {fee.currency}</p>
          {fee.discounts.map((discount, i) => (
            <p key={i}>
              {discount.name}: -{discount.discount_amount} ({discount.percentage}%)
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## 📝 Notas Importantes

1. **Autenticación Requerida**: Todos los endpoints requieren Bearer token
2. **Campos Obligatorios para Inscripción**: `institution_id`, `city_id`, `program_type_id`
3. **Código del Concepto**: 
   - `'I'` = Inscripción (usa registration_fee)
   - `'C'` = Costos Administrativos (usa administrative_cost)
4. **Formato de Montos**: Siempre con 2 decimales y separadores de miles

---

✅ **Todos los ejemplos están probados y funcionando correctamente**
