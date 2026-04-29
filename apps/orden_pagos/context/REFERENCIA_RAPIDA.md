# 🚀 REFERENCIA RÁPIDA - Sistema de Órdenes de Pago

**Última actualización:** 28 de Noviembre de 2025

---

## 📋 ARCHIVOS DE CONTEXTO COMPLETO

Para iniciar en un nuevo chat, consulta:

1. **`CONTEXTO_COMPLETO_SISTEMA_ORDEN_PAGOS.md`** - Contexto completo del sistema
2. **`CONTEXTO_COMPLETO_ENVIO_ENLACE_PAGO.md`** - Contexto específico de envío de enlaces

---

## 🏗️ ARQUITECTURA

```
apps/orden_pagos/
├── domain/          # Lógica de negocio pura
├── application/     # Casos de uso
├── infrastructure/  # Implementaciones técnicas
└── presentation/    # API REST (ViewSets)
```

---

## 🗄️ MODELOS PRINCIPALES

### PaymentOrder (Orden de Pago)

- `order_number` - Generado automático (OP202400001)
- `status` - PENDING, PAID, VERIFIED, CANCELLED
- `total_order` - Calculado automáticamente
- `payment_link_date` - Fecha de envío del enlace

### PaymentOrderDetails (Detalles)

- `payment_type` - Tipo de pago (I, M, B, C, etc.)
- `amount` - Monto neto
- `discount_type` - percentage, fixed
- `discount_amount` - Monto del descuento
- `sub_total` - Total después de descuento

### PaymentOrderProgram (Programa)

- Información del programa educativo
- `price_week`, `duration`, `material_cost`
- `total_enrollment` - Calculado automático

---

## 🔗 ENDPOINTS PRINCIPALES

### Crear y Enviar (Recomendado)

```http
POST /api/v1/payment-orders/create-and-send/
Body: { order_id: null, order_data: {...} }
```

### CRUD Básico

```http
GET    /api/v1/payment-orders/              # Listar
POST   /api/v1/payment-orders/              # Crear
GET    /api/v1/payment-orders/{id}/         # Obtener
PUT    /api/v1/payment-orders/{id}/         # Actualizar
DELETE /api/v1/payment-orders/{id}/         # Cancelar
```

### Acciones Especiales

```http
POST /api/v1/payment-orders/{id}/send-payment-link/  # Enviar enlace
POST /api/v1/payment-orders/{id}/mark-as-paid/       # Marcar pagado
POST /api/v1/payment-orders/{id}/verify/             # Verificar
POST /api/v1/payment-orders/{id}/cancel/             # Cancelar
GET  /api/v1/payment-orders/{id}/structure/          # Ver estructura
```

---

## 📧 ENVÍO DE ENLACES

### Tarea Celery

```python
from apps.orden_pagos.tasks import enviar_enlace_pago_orden

# Envío asíncrono
result = enviar_enlace_pago_orden.delay(order_id=1, base_url=base_url)
```

### Plantillas

- `correo-enlace-pago-orden.html` - Email al estudiante/asesor
- `pdf_orden_pago.html` - PDF adjunto con detalle

### Características

- ✅ Sin contraseñas temporales
- ✅ PDF generado automáticamente
- ✅ Correo a estudiante y asesor
- ✅ Actualiza `payment_link_date`

---

## 🔄 ESTADOS Y TRANSICIONES

```
PENDING → PAID → VERIFIED
   ↓
CANCELLED
```

### Reglas

- Solo PENDING puede actualizarse
- Solo PENDING → PAID
- Solo PENDING → CANCELLED
- Solo PAID → VERIFIED

---

## 💰 TIPOS DE PAGO

| Código | Descripción             | Requiere Programa |
|--------|-------------------------|-------------------|
| **I**  | Inscripción             | ✅                 |
| **M**  | Matrícula               | ✅                 |
| **B**  | Inscripción + Matrícula | ✅                 |
| **C**  | Cargo Administrativo    | ❌                 |
| **E**  | Extensión               | ✅                 |
| **P**  | Abono                   | ✅                 |
| **T**  | Insc + Mat + Cargo      | ✅                 |

---

## 🧮 CÁLCULOS

### Descuentos

```python
# Porcentual
descuento = amount * (discount_amount / 100)

# Fijo
descuento = discount_amount

# Subtotal
sub_total = amount - descuento
```

### Total Orden

```python
total_order = sum(detail.sub_total for detail in details)
```

---

## 💻 EJEMPLO FRONTEND (React)

```javascript
// Crear y enviar enlace en una sola llamada
const response = await fetch('/api/v1/payment-orders/create-and-send/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        order_id: null,  // null = crear, ID = actualizar
        order_data: {
            student_id: 123,
            advisor_id: 5,
            payment_details: [
                {
                    payment_type_id: 1,
                    amount: 1000.00,
                    discount_type: "percentage",
                    discount_amount: 10.00
                }
            ],
            payment_program: {
                program_type_id: 1,
                institution_id: 10,
                country_id: 5,
                city_id: 15,
                start_date: "2025-01-15",
                duration: 12,
                duration_type: "w",
                price_week: 250.00
            }
        }
    })
});

const result = await response.json();
console.log('Orden:', result.order_number);
console.log('Enlace enviado a:', result.student_email);
```

---

## ⚙️ SERVICIOS REQUERIDOS

### Celery Worker

```bash
celery -A api worker -l info
```

### Redis (Broker)

```bash
redis-server
```

---

## 📚 DOCUMENTACIÓN COMPLETA

Ver archivos en:

- `apps/orden_pagos/context/` - Contexto completo
- `apps/orden_pagos/docs/` - Documentación técnica

---

## 🔍 BÚSQUEDA RÁPIDA

### Filtros disponibles

```
?status=PENDING
?student_id=123
?advisor_id=5
?date_from=2025-01-01
?date_to=2025-12-31
?page=1
?per_page=10
```

---

## ⚡ COMANDOS ÚTILES

### Pruebas manuales

```python
# Django shell
python
manage.py
shell

from apps.orden_pagos.models import PaymentOrder

# Ver órdenes
PaymentOrder.objects.all()

# Ver detalles
order = PaymentOrder.objects.get(order_number='OP202400001')
order.payment_order_details.all()
order.payment_order_program
```

---

## 🐛 DEBUGGING

### Logs importantes

```python
import logging

logger = logging.getLogger(__name__)

# Ver logs de tareas Celery
# Ver: errores.log o salida de Celery worker
```

### Errores comunes

1. **"Estado inválido"** - Verificar transiciones de estado
2. **"No se puede actualizar"** - Solo PENDING se actualiza
3. **"Error al enviar correo"** - Verificar configuración EMAIL en settings
4. **"Task no ejecuta"** - Verificar que Celery worker esté corriendo

---

## ✅ CHECKLIST PARA NUEVO CHAT

Cuando inicies un nuevo chat sobre órdenes de pago, proporciona:

1. ✅ Este archivo (`REFERENCIA_RAPIDA.md`)
2. ✅ `CONTEXTO_COMPLETO_SISTEMA_ORDEN_PAGOS.md`
3. ✅ Describe qué necesitas implementar/modificar
4. ✅ Indica si es frontend o backend
5. ✅ Menciona si afecta envío de correos

---

**Contacto:** Equipo de Desarrollo API  
**Versión:** 1.0.0

