# 🔄 ACTUALIZACIÓN: Integración con Patrón de Sistema

## ✅ CAMBIOS APLICADOS

He actualizado la configuración de Django Ninja para seguir **tu patrón existente de URLs con `<sistema>`**.

---

## 📍 **URLS ACTUALIZADAS**

### Antes (con `/ninja/`):

```
❌ /api/v1/ninja/payment-orders/
❌ /api/v1/ninja/docs/
```

### Ahora (siguiendo tu patrón):

```
✅ /api/v1/lcmundo/ordenes-pago/
✅ /api/v1/lcmundo/api-docs/
```

---

## 🎯 **Comparación: DRF vs Ninja**

### API DRF (Existente):

```
URL Base: /api/v1/<sistema>/orden_pagos/

Ejemplos:
├── GET  /api/v1/lcmundo/orden_pagos/payment-order/
├── POST /api/v1/lcmundo/orden_pagos/payment-order/
└── GET  /api/v1/lcmundo/orden_pagos/payment-order/1/
```

### API Ninja (Nueva):

```
URL Base: /api/v1/<sistema>/ordenes-pago/

Ejemplos:
├── GET  /api/v1/lcmundo/ordenes-pago/
├── POST /api/v1/lcmundo/ordenes-pago/
├── GET  /api/v1/lcmundo/ordenes-pago/1/
└── GET  /api/v1/lcmundo/api-docs/  ← Documentación Swagger
```

**Nota:** Usé `ordenes-pago` (con guión) en lugar de `orden_pagos` para:

- Diferenciar claramente de la API DRF
- Seguir convenciones REST (kebab-case en URLs)
- Facilitar la migración gradual

---

## 🏗️ **Arquitectura de URLs**

```python
# api/urls.py

api = NinjaAPI(
    title="LC Mundo API",
    version="2.0.0",
    docs_url="/api-docs/",  # ← Documentación relativa al sistema
)

# Registrar apps con nombres descriptivos en español
api.add_router("/ordenes-pago/", payment_orders_router, tags=["Órdenes de Pago"])

urlpatterns = [
    # ...rutas existentes de DRF...
    
    # DRF: Patrón existente
    path('api/v1/<str:sistema>/orden_pagos/', include('apps.orden_pagos.urls_V1')),
    
    # Ninja: Mismo patrón, diferentes endpoints
    path('api/v1/<str:sistema>/', api.urls),  # ← Integrado aquí
]
```

### ¿Por qué funciona?

Django evalúa las rutas **en orden**. Cuando llega una petición:

1. **DRF captura:** `/api/v1/lcmundo/orden_pagos/*`
2. **Ninja captura:** `/api/v1/lcmundo/ordenes-pago/*` y `/api/v1/lcmundo/api-docs/`

No hay conflicto porque **los paths son diferentes** después del `<sistema>`.

---

## 🚀 **CÓMO USAR AHORA**

### 1. Documentación Swagger:

Para **cualquier sistema**:

```
http://localhost:8000/api/v1/lcmundo/api-docs/
http://localhost:8000/api/v1/otro_sistema/api-docs/
http://localhost:8000/api/v1/demo/api-docs/
```

### 2. Endpoints de Órdenes de Pago:

**Listar órdenes:**

```bash
GET /api/v1/lcmundo/ordenes-pago/
Authorization: Bearer tu_token
```

**Crear orden:**

```bash
POST /api/v1/lcmundo/ordenes-pago/
Authorization: Bearer tu_token
Content-Type: application/json

{
    "student": 123,
    "advisor": 5,
    "payment_details": [...]
}
```

**Obtener orden específica:**

```bash
GET /api/v1/lcmundo/ordenes-pago/1/
Authorization: Bearer tu_token
```

**Buscar por número:**

```bash
GET /api/v1/lcmundo/ordenes-pago/by-number/OP202400001/
Authorization: Bearer tu_token
```

### 3. Endpoints Completos:

```
Base: /api/v1/{sistema}/ordenes-pago/

├── GET    /                              Listar órdenes
├── POST   /                              Crear orden
├── GET    /{id}/                         Obtener orden
├── PUT    /{id}/                         Actualizar orden
├── DELETE /{id}/                         Anular orden
├── GET    /by-number/{number}/           Buscar por número
├── POST   /{id}/mark-as-paid/            Marcar como pagada
├── POST   /{id}/cancel/                  Cancelar orden
├── POST   /{id}/verify/                  Verificar orden
├── POST   /{id}/change-status/           Cambiar estado
├── GET    /{id}/structure/               Estructura JSON
├── POST   /{id}/send-payment-link/       Enviar link
└── POST   /create-and-send/              Crear y enviar
```

---

## 🎨 **Personalización de Nombres**

Si prefieres otros nombres para las rutas, es muy fácil cambiarlos:

### Opción 1: Nombre en inglés

```python
api.add_router("/payment-orders/", payment_orders_router)
# URL: /api/v1/lcmundo/payment-orders/
```

### Opción 2: Nombre en español con guión bajo

```python
api.add_router("/orden_pagos/", payment_orders_router)
# URL: /api/v1/lcmundo/orden_pagos/  ← Conflicto con DRF!
```

### Opción 3: Nombre descriptivo en español

```python
api.add_router("/ordenes/", payment_orders_router)
# URL: /api/v1/lcmundo/ordenes/
```

### Opción 4: Con prefijo "api"

```python
api.add_router("/api/ordenes-pago/", payment_orders_router)
# URL: /api/v1/lcmundo/api/ordenes-pago/
```

---

## 📊 **Ventajas de Esta Arquitectura**

### ✅ Consistencia

- Sigue tu patrón existente `<sistema>`
- Mismo formato para todas las APIs
- Fácil de entender para el equipo

### ✅ Flexibilidad

- Soporta múltiples sistemas sin configuración extra
- Mismo código sirve para `lcmundo`, `demo`, `test`, etc.

### ✅ Migración Gradual

- DRF y Ninja conviven sin conflictos
- Puedes migrar endpoint por endpoint
- Zero downtime garantizado

### ✅ URLs Limpias

- Sin palabras técnicas como "ninja" o "v2"
- Nombres descriptivos en español
- Profesional para usuarios finales

---

## 🔄 **Migración del Frontend**

Cuando actualices el frontend, el cambio es mínimo:

### Antes (DRF):

```javascript
const API_BASE = '/api/v1/lcmundo/orden_pagos/payment-order/';

// Listar
fetch(`${API_BASE}`, {
    headers: { 'Authorization': `Token ${token}` }
});
```

### Ahora (Ninja):

```javascript
const API_BASE = '/api/v1/lcmundo/ordenes-pago/';

// Listar
fetch(`${API_BASE}`, {
    headers: { 'Authorization': `Bearer ${token}` }  // ← Cambio de Token a Bearer
});
```

**Solo 2 cambios:**

1. URL: `orden_pagos/payment-order/` → `ordenes-pago/`
2. Auth: `Token` → `Bearer`

---

## 📝 **Ejemplo Completo de Uso**

```bash
# 1. Obtener token (usando el sistema actual DRF)
curl -X POST http://localhost:8000/api/v1/lcmundo/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Respuesta: {"token": "abc123xyz..."}

# 2. Ver documentación Swagger
# Abrir en navegador:
# http://localhost:8000/api/v1/lcmundo/api-docs/

# 3. Listar órdenes con la nueva API
curl http://localhost:8000/api/v1/lcmundo/ordenes-pago/ \
  -H "Authorization: Bearer abc123xyz..."

# 4. Crear una orden
curl -X POST http://localhost:8000/api/v1/lcmundo/ordenes-pago/ \
  -H "Authorization: Bearer abc123xyz..." \
  -H "Content-Type: application/json" \
  -d '{
    "student": 1,
    "advisor": 1,
    "payment_details": [{
      "payment_type": 1,
      "amount": 1000.00
    }]
  }'

# 5. Obtener orden específica
curl http://localhost:8000/api/v1/lcmundo/ordenes-pago/1/ \
  -H "Authorization: Bearer abc123xyz..."
```

---

## 🎯 **RESUMEN DE CAMBIOS**

| Aspecto           | Antes                           | Ahora                             |
|-------------------|---------------------------------|-----------------------------------|
| **URL Base**      | `/api/v1/ninja/payment-orders/` | `/api/v1/{sistema}/ordenes-pago/` |
| **Documentación** | `/api/v1/ninja/docs/`           | `/api/v1/{sistema}/api-docs/`     |
| **Patrón**        | Ruta estática                   | Patrón dinámico con sistema       |
| **Nombres**       | Inglés (technical)              | Español (user-friendly)           |
| **Integración**   | Ruta separada                   | Mismo patrón que DRF              |

---

## ✅ **CONCLUSIÓN**

Ahora la API Ninja está **completamente integrada con tu arquitectura existente**:

- ✅ Usa el mismo patrón `<str:sistema>`
- ✅ URLs en español más amigables
- ✅ Sin palabras técnicas como "ninja"
- ✅ Documentación accesible por sistema
- ✅ Convive perfectamente con DRF

**Para probar:**

```bash
python manage.py runserver
```

**Luego visita:**

```
http://localhost:8000/api/v1/lcmundo/api-docs/
```

🎉 **¡Listo para usar!**

