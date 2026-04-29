# Endpoints de Conceptos de Pago

## Descripción

Nuevos endpoints agregados para gestionar conceptos de pago y categorías. Permiten obtener los conceptos de pago
organizados por categorías.

## Endpoints Disponibles

### 1. Obtener Categorías con Conceptos Agrupados

**Endpoint:** `GET /api/v1/payment-orders/payment-concepts/categories-with-concepts/`

**Descripción:** Retorna todas las categorías de pago con sus conceptos anidados. Útil para formularios donde se
necesita mostrar conceptos organizados por categoría.

**Autenticación:** Requerida (Token)

**Respuesta:**

```json
[
  {
    "id": 1,
    "code": "CURSO",
    "name": "Cursos y Programas",
    "requires_program": true,
    "concepts": [
      {
        "id": 1,
        "code": "I",
        "name": "Inscripción",
        "category_id": 1,
        "is_active": true,
        "description": "Inscripción a curso",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
      },
      {
        "id": 2,
        "code": "M",
        "name": "Matrícula",
        "category_id": 1,
        "is_active": true,
        "description": "Matrícula de curso",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
      }
    ]
  },
  {
    "id": 2,
    "code": "ADMIN",
    "name": "Costos Administrativos",
    "requires_program": false,
    "concepts": [
      {
        "id": 10,
        "code": "C",
        "name": "Costo Administrativo",
        "category_id": 2,
        "is_active": true,
        "description": "Costos administrativos varios",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
      }
    ]
  }
]
```

### 2. Obtener Todos los Conceptos de Pago

**Endpoint:** `GET /api/v1/payment-orders/payment-concepts/`

**Descripción:** Retorna todos los conceptos de pago activos (sin agrupar por categoría).

**Autenticación:** Requerida (Token)

**Respuesta:**

```json
[
  {
    "id": 1,
    "code": "I",
    "name": "Inscripción",
    "category_id": 1,
    "is_active": true,
    "description": "Inscripción a curso",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  {
    "id": 2,
    "code": "M",
    "name": "Matrícula",
    "category_id": 1,
    "is_active": true,
    "description": "Matrícula de curso",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

### 3. Obtener Conceptos por Categoría

**Endpoint:** `GET /api/v1/payment-orders/payment-concepts/by-category/{category_id}/`

**Descripción:** Retorna todos los conceptos de una categoría específica.

**Autenticación:** Requerida (Token)

**Parámetros de URL:**

- `category_id` (int): ID de la categoría

**Ejemplo:** `GET /api/v1/payment-orders/payment-concepts/by-category/1/`

**Respuesta:**

```json
[
  {
    "id": 1,
    "code": "I",
    "name": "Inscripción",
    "category_id": 1,
    "is_active": true,
    "description": "Inscripción a curso",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  {
    "id": 2,
    "code": "M",
    "name": "Matrícula",
    "category_id": 1,
    "is_active": true,
    "description": "Matrícula de curso",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

### 4. Obtener Conceptos Agrupados por Categoría (Formato Diccionario)

**Endpoint:** `GET /api/v1/payment-orders/payment-concepts/grouped-by-category/`

**Descripción:** Retorna todos los conceptos agrupados por categoría en formato de lista de diccionarios, donde cada
diccionario tiene el código de la categoría como clave y un array de conceptos detallados como valor.

**Autenticación:** Requerida (Token)

**Formato especial:** Este endpoint está diseñado para facilitar la renderización en formularios donde necesitas agrupar
conceptos por categoría usando el código de la categoría como identificador.

**Respuesta:**

```json
[
  {
    "PROGRAM": [
      {
        "id": 1,
        "code": "I",
        "name": "Inscripción",
        "category_id": 1,
        "category_code": "PROGRAM",
        "category_name": "Cursos y Programas",
        "is_active": true,
        "description": "Inscripción a curso",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
      },
      {
        "id": 2,
        "code": "M",
        "name": "Matrícula",
        "category_id": 1,
        "category_code": "PROGRAM",
        "category_name": "Cursos y Programas",
        "is_active": true,
        "description": "Matrícula de curso",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
      }
    ]
  },
  {
    "ADMIN": [
      {
        "id": 10,
        "code": "C",
        "name": "Costo Administrativo",
        "category_id": 2,
        "category_code": "ADMIN",
        "category_name": "Costos Administrativos",
        "is_active": true,
        "description": "Costos administrativos varios",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
      }
    ]
  }
]
```

## Arquitectura

### Schemas (Pydantic)

- `PaymentConceptSchema`: Schema individual para un concepto de pago
- `PaymentCategorySchema`: Schema individual para una categoría
- `PaymentCategoryWithConceptsSchema`: Schema para categoría con sus conceptos anidados
- `PaymentConceptDetailSchema`: Schema detallado con información de categoría incluida

**Ubicación:** `apps/orden_pagos/presentation/api/schemas/output_schemas.py`

### Repositorio

- `PaymentConceptRepository`: Maneja operaciones de base de datos para conceptos y categorías
- Incluye optimización con `prefetch_related` para evitar N+1 queries
- Método `get_concepts_grouped_by_category()`: Retorna conceptos en formato de diccionario agrupado

**Ubicación:** `apps/orden_pagos/infrastructure/repository/payment_concept_repository.py`

### Casos de Uso

- `GetCategoriesWithConceptsUseCase`: Obtiene categorías con conceptos agrupados
- `GetAllConceptsUseCase`: Obtiene todos los conceptos activos
- `GetConceptsByCategory`: Obtiene conceptos de una categoría específica
- `GetConceptsGroupedByCategoryUseCase`: Obtiene conceptos en formato diccionario agrupado por categoría

**Ubicación:** `apps/orden_pagos/application/use_cases/get_payment_concepts.py`

### Router

Los endpoints están registrados en el router principal de Django Ninja.

**Ubicación:** `apps/orden_pagos/presentation/api/router.py`

## Uso desde Frontend

### Ejemplo 1: Cargar conceptos agrupados en un formulario

```javascript
// Obtener categorías con conceptos
const response = await fetch('/api/v1/payment-orders/payment-concepts/categories-with-concepts/', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});

const categories = await response.json();

// Renderizar en el formulario
categories.forEach(category => {
    console.log(`Categoría: ${category.name}`);
    category.concepts.forEach(concept => {
        console.log(`  - ${concept.name} (${concept.code})`);
    });
});
```

### Ejemplo 2: Usar formato de diccionario agrupado

```javascript
// Obtener conceptos en formato diccionario agrupado
const response = await fetch('/api/v1/payment-orders/payment-concepts/grouped-by-category/', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});

const groupedConcepts = await response.json();

// Acceder directamente por código de categoría
groupedConcepts.forEach(categoryObj => {
    const categoryCode = Object.keys(categoryObj)[0]; // Ej: "PROGRAM"
    const concepts = categoryObj[categoryCode];

    console.log(`Categoría: ${categoryCode}`);
    concepts.forEach(concept => {
        console.log(`  - ${concept.name} (${concept.code})`);
        console.log(`    Categoría: ${concept.category_name}`);
    });
});

// Crear un objeto para acceso rápido
const conceptsByCategory = {};
groupedConcepts.forEach(categoryObj => {
    const categoryCode = Object.keys(categoryObj)[0];
    conceptsByCategory[categoryCode] = categoryObj[categoryCode];
});

// Ahora puedes acceder directamente:
const programConcepts = conceptsByCategory['PROGRAM'];
const adminConcepts = conceptsByCategory['ADMIN'];
```

## Notas

- Todos los endpoints requieren autenticación con token
- Solo se retornan conceptos activos (`is_active = true`)
- Las queries están optimizadas con `select_related` y `prefetch_related`
- Los conceptos se ordenan alfabéticamente por nombre

