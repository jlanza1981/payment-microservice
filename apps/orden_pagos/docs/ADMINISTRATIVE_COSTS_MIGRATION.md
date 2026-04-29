# Migración de Costos Administrativos - Documentación

## Resumen

Se ha completado exitosamente la migración de la funcionalidad de tipos de costos administrativos desde `PlanillaEnLinea.py` al módulo de órdenes de pago, siguiendo la arquitectura hexagonal y usando Django Ninja.

## Archivos Creados

### 1. Repositorio
**Ubicación:** `apps/orden_pagos/infrastructure/repository/administrative_cost_repository.py`

**Métodos:**
- `get_by_country_and_currency()`: Obtiene un costo específico por país, tipo y moneda
- `list_by_country()`: Lista tipos de costos activos por país
- `_reload_cost_type()`: Método privado que filtra por fecha y elimina duplicados

**Características:**
- Optimización de queries con `select_related` y `prefetch_related`
- Validación de fechas (fecha_inicio <= fecha_actual <= fecha_final)
- Eliminación de duplicados usando `set()`
- Moneda fija en USD (según requerimiento)

### 2. Casos de Uso
**Ubicación:** `apps/orden_pagos/application/use_cases/get_administrative_costs.py`

**Casos de uso implementados:**
- `GetAdministrativeCostByCountryUseCase`: Para obtener un costo específico
- `ListAdministrativeCostsByCountryUseCase`: Para listar costos activos por país

### 3. Schemas
**Ubicación:** `apps/orden_pagos/presentation/api/schemas/output_administrative_cost_schema.py`

**Schemas creados:**
- `AdministrativeCostSchema`: Schema de salida con campos:
  - `id`: ID del tipo de costo
  - `name`: Nombre del tipo de costo
  - `amount`: Monto del costo
  - `currency`: Moneda (USD)
  - `country_id`: ID del país
  - `country_name`: Nombre del país

- `AdministrativeCostFilterSchema`: Schema para filtros de entrada

**Método especial:**
- `from_data()`: Convierte tanto diccionarios como objetos ORM a schema

### 4. Router
**Ubicación:** `apps/orden_pagos/presentation/api/administrative_cost_router.py`

**Endpoints creados:**

#### GET `/api/v1/payment-orders/administrative-costs/by-country/{country_id}/`
- Obtiene un costo administrativo específico
- Query params: `cost_type`, `currency` (default: USD)
- Response: 200 (costo encontrado) | 404 (no encontrado)

#### GET `/api/v1/payment-orders/administrative-costs/list-by-country/{country_id}/`
- Lista todos los tipos de costos activos para un país
- Query params: `currency` (default: USD)
- Response: 200 (lista de costos)
- Filtra automáticamente por:
  - Rango de fechas válido
  - Estado activo
  - Elimina duplicados

## Integración

### Router Principal
El sub-router se registró en `router.py`:
```python
router.add_router("/administrative-costs", administrative_costs_router)
```

### Exports
Se actualizaron los `__init__.py` para exportar:
- Casos de uso en `application/use_cases/__init__.py`
- Schemas en `presentation/api/schemas/__init__.py`

## Arquitectura

```
Domain Layer
    └── (Sin cambios - usa modelos existentes)

Application Layer
    └── use_cases/
        └── get_administrative_costs.py
            ├── GetAdministrativeCostByCountryUseCase
            └── ListAdministrativeCostsByCountryUseCase

Infrastructure Layer
    └── repository/
        └── administrative_cost_repository.py
            └── AdministrativeCostRepository

Presentation Layer
    └── api/
        ├── administrative_cost_router.py (Router con endpoints)
        └── schemas/
            └── output_administrative_cost_schema.py
```

## Ventajas de la Implementación

1. **Arquitectura limpia**: Separación clara de responsabilidades (repositorio → caso de uso → router)
2. **Optimizada**: Queries eficientes con carga relacionada
3. **Reutilizable**: Casos de uso pueden usarse desde otros módulos
4. **Documentada**: OpenAPI automático con Django Ninja
5. **Consistente**: Sigue el mismo patrón de otros routers del proyecto
6. **Simplificada**: Eliminada lógica de código promocional innecesaria
7. **Moneda fija**: USD como requerimiento, simplifica la lógica

## Ejemplos de Uso

### Obtener costo específico
```bash
GET /api/v1/payment-orders/administrative-costs/by-country/1/?cost_type=5&currency=USD
```

**Response 200:**
```json
{
  "id": 5,
  "name": "Costo Administrativo Express",
  "amount": "75.00",
  "currency": "USD",
  "country_id": 1,
  "country_name": "Ecuador"
}
```

### Listar costos por país
```bash
GET /api/v1/payment-orders/administrative-costs/list-by-country/1/?currency=USD
```

**Response 200:**
```json
[
  {
    "id": 1,
    "name": "Costo Administrativo Base",
    "amount": "50.00",
    "currency": "USD",
    "country_id": 1,
    "country_name": "Ecuador"
  },
  {
    "id": 3,
    "name": "Costo Administrativo Express",
    "amount": "75.00",
    "currency": "USD",
    "country_id": 1,
    "country_name": "Ecuador"
  }
]
```

## Testing

Para probar los endpoints:

1. Iniciar el servidor
2. Acceder a `/api/docs` para ver la documentación interactiva
3. Los endpoints requieren autenticación Bearer token
4. Validar que los filtros de fecha funcionen correctamente

## Próximos Pasos

- [ ] Crear tests unitarios para el repositorio
- [ ] Crear tests de integración para los endpoints
- [ ] Documentar casos de uso específicos del negocio
- [ ] Considerar caché para resultados frecuentes
