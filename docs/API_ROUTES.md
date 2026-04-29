# 📍 RUTAS DE LA API - Payment Microservice

## 🎯 Rutas Principales

### Documentación Swagger UI
```
http://localhost:8000/api/v1/api-docs/
```
**Descripción:** Interfaz interactiva Swagger UI con todos los endpoints, schemas y posibilidad de probar la API.

### API Base
```
http://localhost:8000/api/v1/
```
**Descripción:** Base URL de todos los endpoints de la API.

### Health Check
```
http://localhost:8000/api/v1/health
```
**Descripción:** Endpoint para verificar el estado del servicio.

**Ejemplo:**
```bash
curl http://localhost:8000/api/v1/health

# Respuesta:
{
  "status": "healthy",
  "service": "payment-microservice",
  "version": "1.0.0"
}
```

### Admin Panel
```
http://localhost:8000/admin/
```
**Descripción:** Panel de administración de Django.

---

## 🔗 Endpoints por Recurso

### Payment Orders (Órdenes de Pago)
```
GET    /api/v1/payment-orders/          # Listar órdenes
POST   /api/v1/payment-orders/          # Crear orden
GET    /api/v1/payment-orders/{id}/     # Obtener detalle
PUT    /api/v1/payment-orders/{id}/     # Actualizar
DELETE /api/v1/payment-orders/{id}/     # Eliminar
```

### Payments (Pagos)
```
GET    /api/v1/payments/                # Listar pagos
POST   /api/v1/payments/                # Registrar pago
GET    /api/v1/payments/{id}/           # Obtener detalle
```

### PayPal Webhooks
```
POST   /api/v1/paypal/webhook/          # Webhook de PayPal
```

### Stripe Webhooks
```
POST   /api/v1/stripe/webhook/          # Webhook de Stripe
```

---

## 📊 Comparación con Proyecto API Original

### Proyecto API Original (LC Mundo)
```
http://localhost:8000/api/v1/api-docs/
```

### Payment Microservice (Este proyecto)
```
http://localhost:8000/api/v1/api-docs/
```

✅ **Mismo patrón de URLs** para mantener consistencia.

---

## 🔧 Configuración en el Código

### config/urls.py

```python
from ninja import NinjaAPI

# Configuración de la API
api = NinjaAPI(
    title="Payment Microservice API",
    version="1.0.0",
    docs_url="/api-docs/",  # ← Ruta relativa de documentación
)

# Registro en urlpatterns
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', api.urls),  # ← API montada en /api/v1/
]

# Resultado: /api/v1/ + /api-docs/ = /api/v1/api-docs/
```

### Registrar Routers

```python
from apps.orden_pagos.presentation.api.routers.router import router as payment_orders_router

# Agregar routers a la API
api.add_router("/payment-orders/", payment_orders_router, tags=["Payment Orders"])

# Resultado: /api/v1/payment-orders/
```

---

## 🚀 Ejemplos de Uso

### 1. Ver Documentación
```bash
# Abrir en navegador
http://localhost:8000/api/v1/api-docs/
```

### 2. Health Check
```bash
curl http://localhost:8000/api/v1/health

# Respuesta
{
  "status": "healthy",
  "service": "payment-microservice",
  "version": "1.0.0"
}
```

### 3. Listar Órdenes de Pago (cuando esté implementado)
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/v1/payment-orders/

# Respuesta
[
  {
    "id": 1,
    "order_number": "PO-2026-00001",
    "total_order": 1000.00,
    "status": "PENDING"
  }
]
```

### 4. Crear Orden de Pago
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"student_id": 1, "advisor_id": 2, "concepts": [...]}' \
     http://localhost:8000/api/v1/payment-orders/
```

---

## 📝 Notas Importantes

### 1. Swagger UI Interactivo
La documentación en `/api/v1/api-docs/` permite:
- ✅ Ver todos los endpoints
- ✅ Probar requests directamente desde el navegador
- ✅ Ver schemas de request/response
- ✅ Autenticación con Bearer Token

### 2. OpenAPI JSON
También disponible en:
```
http://localhost:8000/api/v1/openapi.json
```

### 3. Autenticación
Los endpoints protegidos requieren Bearer Token:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/v1/payment-orders/
```

---

## 🔍 Verificar Configuración

### Opción 1: Con el servidor corriendo
```bash
# Iniciar servidor
python manage.py runserver

# Visitar
http://localhost:8000/api/v1/api-docs/
```

### Opción 2: Con Docker
```bash
# Levantar servicios
docker-compose up

# Visitar
http://localhost:8000/api/v1/api-docs/
```

---

## 📚 Documentación Adicional

- **Django Ninja Docs:** https://django-ninja.rest-framework.com/
- **OpenAPI Spec:** https://swagger.io/specification/

---

## ✅ Resumen Rápido

| Recurso | URL |
|---------|-----|
| **Documentación** | `http://localhost:8000/api/v1/api-docs/` |
| **API Base** | `http://localhost:8000/api/v1/` |
| **Health Check** | `http://localhost:8000/api/v1/health` |
| **Admin** | `http://localhost:8000/admin/` |
| **OpenAPI JSON** | `http://localhost:8000/api/v1/openapi.json` |

---

**✨ Rutas actualizadas para seguir el mismo patrón del proyecto API original! ✨**

