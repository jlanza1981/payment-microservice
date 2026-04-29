# 📋 CONTEXTO COMPLETO - Sistema de Envío de Enlace de Pago

**Fecha:** 28 de Noviembre de 2025  
**Sistema:** LC Mundo - Órdenes de Pago  
**App:** `apps/orden_pagos`

---

## 🎯 RESUMEN EJECUTIVO

Se implementó un **sistema completo de envío de enlaces de pago** para la app `orden_pagos` con las siguientes
características:

1. ✅ **Envío automático de correos** al crear o actualizar órdenes de pago
2. ✅ **PDF adjunto** con el detalle de la orden
3. ✅ **Una sola llamada desde frontend** (no dos separadas)
4. ✅ **Sin contraseñas temporales** - El estudiante las recupera desde la website
5. ✅ **Proceso asíncrono con Celery** - No bloquea la respuesta
6. ✅ **Tres formas de uso** para máxima flexibilidad

---

## 📁 ARCHIVOS CREADOS (6)

### 1. Templates HTML (2 archivos)

#### `apps/orden_pagos/templates/correo-enlace-pago-orden.html`

Plantilla de correo electrónico que reciben el estudiante y el asesor.

**Contenido:**

- Saludo personalizado
- Número de orden y monto total
- Botón "Pagar aquí" con enlace
- Nota sobre recuperación de contraseña desde web
- Sin envío de contraseñas temporales (por seguridad)

#### `apps/orden_pagos/templates/pdf_orden_pago.html`

Plantilla para generar el PDF de la orden de pago.

**Contenido:**

- Logo de LC Mundo
- Información del estudiante
- Información del programa (si aplica)
- Tabla de conceptos de pago con descuentos
- Total a pagar
- Notas de validez

### 2. Módulo de Tareas Celery (1 archivo)

#### `apps/orden_pagos/tasks.py`

**Función principal:**

```python
@shared_task
def enviar_enlace_pago_orden(order_id, base_url=None):
    """
    Envía el enlace de pago al estudiante y asesor.
    El estudiante recuperará su contraseña desde la website.
    """
    # Genera PDF, envía correos, actualiza fecha
```

**Función auxiliar:**

```python
def generar_pdf_orden_pago(payment_order, base_url=None):
    """Genera el PDF de una orden de pago."""
```

**Características:**

- Proceso asíncrono (no bloquea)
- Validación de estado PENDING
- Envío de correos con PDF adjunto
- Actualización automática de `payment_link_date`
- Manejo robusto de errores con logging
- Retorna task_id para seguimiento

### 3. Documentación (3 archivos)

#### `IMPLEMENTACION_COMPLETADA_ENLACE_PAGO.md`

Documentación técnica completa de la implementación.

#### `CAMBIOS_SIN_CONTRASENAS_TEMPORALES.md`

Detalles del cambio de arquitectura eliminando contraseñas temporales.

#### `GUIA_FRONTEND_ENVIO_ENLACE.md`

Guía completa para implementación en frontend con ejemplos en React, Vue y Angular.

---

## 📝 ARCHIVOS MODIFICADOS (3)

### 1. ViewSet Principal

#### `apps/orden_pagos/presentation/views/payment_order_viewset.py`

**Métodos agregados:**

##### a) `create_and_send(request)` - ENDPOINT PRINCIPAL ⭐

```python
@action(detail=False, methods=['post'], url_path='create-and-send')
def create_and_send(self, request):
    """
    POST /api/v1/payment-orders/create-and-send/
    
    Body:
    {
      "order_id": null,        // null = crear, ID = actualizar
      "order_data": {...}      // Datos de la orden
    }
    
    Crea/actualiza orden y envía enlace en una sola llamada.
    """
```

**Características:**

- Detecta automáticamente si debe crear o actualizar
- Valida que la orden esté en PENDING
- Envía el enlace inmediatamente
- Retorna orden completa + confirmación de envío

##### b) `send_payment_link(request, pk)` - ENVÍO INDEPENDIENTE

```python
@action(detail=True, methods=['post'], url_path='send-payment-link')
def send_payment_link(self, request, pk=None):
    """
    POST /api/v1/payment-orders/{id}/send-payment-link/
    
    Body: {} (vacío)
    
    Solo envía el enlace de una orden existente.
    """
```

**Características:**

- Para órdenes ya creadas
- Útil para reenviar enlaces
- Valida estado PENDING

##### c) Modificación en `update(request, pk)`

```python
def update(self, request, pk=None):
    # ... código de actualización ...

    # Enviar enlace con query parameter
    send_link = request.query_params.get('send_payment_link', 'false').lower() == 'true'

    if send_link and payment_order.status == 'PENDING':
# Envía el enlace automáticamente
```

**Uso:**

```
PUT /api/v1/payment-orders/123/?send_payment_link=true
```

### 2. Serializers

#### `apps/orden_pagos/infrastructure/serializers/payment_order_input_serializer.py`

**Cambio:** Se eliminó `SendPaymentLinkSerializer` porque ya no se necesitan parámetros de contraseña.

#### `apps/orden_pagos/infrastructure/serializers/__init__.py`

**Cambio:** Se actualizaron las exportaciones eliminando el serializer no usado.

---

## 🚀 TRES FORMAS DE USO

### OPCIÓN 1: `create-and-send` ⭐ RECOMENDADO

**Endpoint:**

```
POST /api/v1/payment-orders/create-and-send/
```

**Request:**

```json
{
  "order_id": null,
  // null para crear, ID para actualizar
  "order_data": {
    "student_id": 123,
    "advisor_id": 5,
    "opportunity_id": 50,
    "payment_details": [
      {
        "payment_type_id": 1,
        "amount": 1000.00,
        "discount_type": "percentage",
        "discount_amount": 10.00
      }
    ],
    "payment_program": {
      "program_type_id": 1,
      "institution_id": 10,
      "country_id": 5,
      "city_id": 15,
      "start_date": "2025-01-15",
      "duration": 12,
      "duration_type": "w",
      "price_week": 250.00
    }
  }
}
```

**Response:**

```json
{
  "id": 1,
  "order_number": "OP202400001",
  "message": "Orden creada y enlace de pago enviado",
  "payment_link_sent": true,
  "payment_link_task_id": "abc123-def456",
  "student_email": "estudiante@example.com",
  "advisor_email": "asesor@example.com",
  "status": "PENDING",
  "total_order": "3500.00"
}
```

**Ventajas:**

- ✅ Una sola llamada HTTP
- ✅ Detección automática crear/actualizar
- ✅ Código frontend más simple
- ✅ Mejor rendimiento

---

### OPCIÓN 2: Query Parameters

**Crear con envío:**

```
POST /api/v1/payment-orders/?send_payment_link=true
```

**Actualizar con envío:**

```
PUT /api/v1/payment-orders/123/?send_payment_link=true
```

**Request:** (Body normal de CREATE o UPDATE)

**Response:** (Respuesta normal + campos adicionales)

```json
{
  "id": 1,
  "order_number": "OP202400001",
  "payment_link_sent": true,
  "payment_link_task_id": "abc123-def456"
}
```

**Ventajas:**

- ✅ Usa endpoints existentes
- ✅ Flexible (puedes enviar o no)
- ✅ Mínimo cambio en código existente

---

### OPCIÓN 3: Envío Independiente

**Endpoint:**

```
POST /api/v1/payment-orders/{id}/send-payment-link/
```

**Request:**

```json
{}  // Vacío
```

**Response:**

```json
{
  "message": "El enlace de pago para la orden OP202400001 está siendo enviado.",
  "order_number": "OP202400001",
  "task_id": "abc123-def456",
  "student_email": "estudiante@example.com",
  "advisor_email": "asesor@example.com"
}
```

**Ventajas:**

- ✅ Para reenviar enlaces
- ✅ No modifica la orden
- ✅ Solo envía el correo

---

## 💻 CÓDIGO FRONTEND LISTO

### React/Next.js

```javascript
import {useState} from 'react';
import {toast} from 'react-toastify';

function BotonEnviarEnlace({orderData, currentOrderId = null}) {
    const [loading, setLoading] = useState(false);

    const handleEnviar = async () => {
        setLoading(true);

        try {
            const response = await fetch('/api/v1/payment-orders/create-and-send/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    order_id: currentOrderId,  // null = crear, ID = actualizar
                    order_data: orderData
                })
            });

            if (!response.ok) throw new Error('Error al procesar');

            const result = await response.json();

            toast.success(
                `✅ ${result.message}\n` +
                `📧 Enlace enviado a ${result.student_email}`
            );

        } catch (error) {
            toast.error('❌ Error al crear orden');
        } finally {
            setLoading(false);
        }
    };

    return (
        <button onClick={handleEnviar} disabled={loading}>
            {loading ? 'Procesando...' : 'Enviar Enlace de Pago'}
        </button>
    );
}
```

### Vue.js

```vue

<template>
  <button @click="enviarEnlace" :disabled="loading">
    {{ loading ? 'Procesando...' : 'Enviar Enlace de Pago' }}
  </button>
</template>

<script>
  export default {
    data() {
      return {
        loading: false
      };
    },
    methods: {
      async enviarEnlace() {
        this.loading = true;

        try {
          const response = await this.$http.post(
              '/api/v1/payment-orders/create-and-send/',
              {
                order_id: this.currentOrderId || null,
                order_data: this.orderData
              }
          );

          this.$toast.success(response.data.message);

        } catch (error) {
          this.$toast.error('Error al procesar');
        } finally {
          this.loading = false;
        }
      }
    }
  };
</script>
```

---

## 📧 CORREO QUE RECIBE EL ESTUDIANTE

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 REALIZA TU PAGO A TRAVÉS DE NUESTRO SISTEMA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Estimado(a): Juan Pérez

Hemos generado tu orden de pago N° OP202400001 
por un monto de $3,500.00

Para realizar tu pago haz clic en el siguiente enlace:

┌───────────────────────────────────────┐
│          [Pagar aquí]                 │
└───────────────────────────────────────┘

Adjunto encontrarás el detalle de tu orden de pago.

⚠️ Nota importante: Si es tu primera vez en 
nuestro sistema o necesitas restablecer tu 
contraseña, podrás hacerlo directamente desde 
nuestra página web cuando accedas al enlace de pago.

Si tienes alguna pregunta, no dudes en contactarnos.

Saludos cordiales,
Equipo LC Mundo

📎 Adjunto: orden_pago_OP202400001_Juan_Perez.pdf
```

---

## 🔄 FLUJO COMPLETO

```
┌────────────────────────────────────┐
│ 1. FRONTEND                        │
│    Asesor presiona                 │
│    "Enviar Enlace de Pago"         │
└───────────────┬────────────────────┘
                │
                │ POST /create-and-send/
                │ { order_id, order_data }
                ▼
┌────────────────────────────────────┐
│ 2. BACKEND                         │
│    • Crea/actualiza orden          │
│    • Valida estado PENDING         │
│    • Inicia tarea Celery           │
└───────────────┬────────────────────┘
                │
                ▼
┌────────────────────────────────────┐
│ 3. CELERY TASK (Asíncrono)         │
│    • Genera PDF de la orden        │
│    • Envía correo al estudiante    │
│    • Envía correo al asesor        │
│    • Actualiza payment_link_date   │
└───────────────┬────────────────────┘
                │
                ▼
┌────────────────────────────────────┐     ┌─────────────────────────┐
│ 4. ESTUDIANTE                      │     │ 5. ASESOR               │
│    📧 Recibe correo con:           │     │    📧 Recibe copia      │
│    • Enlace de pago                │     │                         │
│    • PDF adjunto                   │     │                         │
│    • Nota sobre contraseña         │     │                         │
└───────────────┬────────────────────┘     └─────────────────────────┘
                │
                │ Click en "Pagar aquí"
                ▼
┌────────────────────────────────────┐
│ 6. WEBSITE                         │
│    • Primera vez → Crear contraseña│
│    • Ya tiene cuenta → Login       │
│    • Olvidó → Recuperar contraseña │
└────────────────────────────────────┘
```

---

## ⚙️ CONFIGURACIÓN REQUERIDA

### 1. Email (settings.py)

```python
EMAIL_HOST_USER = 'tu_email@example.com'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_PASSWORD = 'tu_password'
```

### 2. Celery (settings.py)

```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

### 3. Iniciar Celery Worker

```bash
celery -A api worker -l info
```

### 4. URL de Pago (tasks.py línea 56)

```python
payment_link = f"https://www.lcmundo.com/pago-online/orden/{payment_order.order_number}/pagar/"
```

**⚠️ IMPORTANTE:** Ajusta esta URL según tu dominio.

---

## 🎯 DECISIONES DE ARQUITECTURA

### ❌ Lo que NO se hizo (por diseño)

1. **No se envían contraseñas temporales por correo**
    - Razón: Seguridad
    - Alternativa: El estudiante las recupera desde la web

2. **No se bloquea la respuesta esperando el envío**
    - Razón: Performance
    - Alternativa: Proceso asíncrono con Celery

3. **No se requiere hacer dos llamadas desde el frontend**
    - Razón: Optimización
    - Alternativa: Endpoint `create-and-send` combinado

### ✅ Lo que SÍ se implementó

1. **Tres formas de uso** - Máxima flexibilidad
2. **Validaciones estrictas** - Solo PENDING puede enviar
3. **PDF profesional** - Con toda la información
4. **Logging completo** - Para debugging
5. **Task ID retornado** - Para seguimiento del envío
6. **Actualización automática** - `payment_link_date`

---

## 📊 ENDPOINTS COMPLETOS

### Endpoints de Órdenes de Pago

| Método   | Endpoint                                      | Descripción                                            |
|----------|-----------------------------------------------|--------------------------------------------------------|
| GET      | `/payment-orders/`                            | Listar órdenes con paginación                          |
| POST     | `/payment-orders/`                            | Crear orden (opcional: `?send_payment_link=true`)      |
| GET      | `/payment-orders/{id}/`                       | Obtener orden específica                               |
| PUT      | `/payment-orders/{id}/`                       | Actualizar orden (opcional: `?send_payment_link=true`) |
| DELETE   | `/payment-orders/{id}/`                       | Anular orden (soft delete)                             |
| GET      | `/payment-orders/by-number/{number}/`         | Buscar por número                                      |
| POST     | `/payment-orders/{id}/mark_as_paid/`          | Marcar como pagada                                     |
| POST     | `/payment-orders/{id}/cancel/`                | Cancelar orden                                         |
| POST     | `/payment-orders/{id}/verify/`                | Verificar por tesorería                                |
| POST     | `/payment-orders/{id}/change_status/`         | Cambiar estado                                         |
| GET      | `/payment-orders/{id}/structure/`             | Obtener estructura completa                            |
| **POST** | **`/payment-orders/create-and-send/`**        | **Crear/actualizar Y enviar** ⭐                        |
| **POST** | **`/payment-orders/{id}/send-payment-link/`** | **Solo enviar enlace**                                 |

---

## 🐛 DEBUGGING

### Ver logs del worker de Celery

```bash
celery -A api worker -l debug
```

### Verificar que se envió el correo

```python
# En tasks.py, revisar los logs
logger.info(f"Enlace de pago enviado al estudiante {student.email}")
logger.error(f"Error al enviar correo: {str(e)}")
```

### Verificar que se actualizó la fecha

```python
# Después de enviar
GET / api / v1 / payment - orders / {id} /

# Verificar que payment_link_date tenga valor
```

---

## 🔒 SEGURIDAD

### Implementado

1. ✅ **Sin contraseñas en JSON** - No se envían por request
2. ✅ **Sin contraseñas en correo** - No se envían por email
3. ✅ **Validación de autenticación** - `IsAuthenticated` requerido
4. ✅ **Validación de estado** - Solo PENDING puede enviar
5. ✅ **Proceso asíncrono** - No expone datos en respuesta inmediata

### Recomendaciones Adicionales

1. 🔐 Implementar rate limiting en endpoints de envío
2. 🔐 Validar que el asesor tenga permisos sobre el estudiante
3. 🔐 Implementar throttling para evitar spam de correos
4. 🔐 Agregar logs de auditoría para envíos

---

## 📈 MÉTRICAS Y MONITOREO

### Campos para monitorear

```python
payment_order.payment_link_date  # Fecha del último envío
payment_order.status  # Estado de la orden
```

### Queries útiles

```python
# Órdenes con enlace enviado hoy
PaymentOrder.objects.filter(
    payment_link_date=date.today(),
    status='PENDING'
)

# Órdenes pendientes sin envío
PaymentOrder.objects.filter(
    status='PENDING',
    payment_link_date__isnull=True
)
```

---

## 🧪 TESTING

### Test Manual

```bash
# 1. Crear orden y enviar enlace
curl -X POST http://localhost:8000/api/v1/payment-orders/create-and-send/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": null,
    "order_data": {
      "student_id": 123,
      "advisor_id": 5,
      "payment_details": [{"payment_type_id": 1, "amount": 1000}]
    }
  }'

# 2. Verificar respuesta
✅ "payment_link_sent": true
✅ "order_number": "OP202400001"
✅ "task_id": "abc123..."

# 3. Verificar correo en inbox del estudiante
✅ Correo recibido con asunto "REALIZA TU PAGO..."
✅ PDF adjunto presente
✅ Enlace de pago funcional

# 4. Verificar orden actualizada
curl -X GET http://localhost:8000/api/v1/payment-orders/1/ \
  -H "Authorization: Bearer TOKEN"

✅ "payment_link_date": "2025-11-28"
```

---

## 📚 DOCUMENTACIÓN ADICIONAL

### Archivos de Referencia

1. **CAMBIOS_SIN_CONTRASENAS_TEMPORALES.md**
    - Explicación del cambio de arquitectura
    - Comparación antes/después
    - Justificación técnica

2. **GUIA_FRONTEND_ENVIO_ENLACE.md**
    - Ejemplos completos en React, Vue, Angular
    - Manejo de errores
    - Mejores prácticas

3. **RESUMEN_OPCIONES_ENVIO_ENLACE.md**
    - Comparación detallada de las 3 opciones
    - Casos de uso específicos
    - Recomendaciones por escenario

4. **IMPLEMENTACION_COMPLETADA_ENLACE_PAGO.md**
    - Checklist de implementación
    - Configuración paso a paso
    - Troubleshooting

---

## ✅ CHECKLIST DE ESTADO ACTUAL

- ✅ Backend implementado
- ✅ Endpoints funcionales
- ✅ Tareas Celery definidas
- ✅ Templates HTML creadas
- ✅ Sin errores de compilación
- ✅ Documentación completa
- ✅ Ejemplos de frontend incluidos
- ⬜ Tests unitarios (pendiente)
- ⬜ Integración con website de pagos (pendiente)
- ⬜ Configuración en producción (pendiente)

---

## 🚀 PRÓXIMOS PASOS SUGERIDOS

1. **Implementar en Frontend**
    - Usar ejemplos proporcionados
    - Probar flujo completo

2. **Configurar en Producción**
    - Variables de entorno
    - Celery workers en servidor
    - Email en producción

3. **Tests Automatizados**
    - Tests unitarios para tasks
    - Tests de integración para endpoints
    - Tests de correos (con mocks)

4. **Monitoreo**
    - Logs de envíos
    - Métricas de correos
    - Alertas de errores

---

## 💡 TIPS IMPORTANTES

1. **Celery DEBE estar corriendo** - Si no, los correos no se envían
2. **Email debe estar configurado** - Verificar settings.py
3. **URL de pago debe ajustarse** - Según tu dominio
4. **Estado PENDING es obligatorio** - Para enviar enlaces
5. **Una orden puede reenviar** - Usando el endpoint independiente

---

## 📞 PARA NUEVO CHAT

**Información clave a proporcionar:**

1. Este archivo completo (CONTEXTO_COMPLETO_ENVIO_ENLACE_PAGO.md)
2. Cualquiera de los siguientes si son relevantes:
    - `apps/orden_pagos/presentation/views/payment_order_viewset.py`
    - `apps/orden_pagos/tasks.py`
    - `apps/orden_pagos/templates/correo-enlace-pago-orden.html`

**Preguntas típicas que puedes hacer:**

- "¿Cómo configuro esto en producción?"
- "¿Cómo agrego tests unitarios?"
- "¿Cómo personalizo las plantillas?"
- "¿Cómo agrego un nuevo tipo de pago?"
- "¿Cómo implemento la recuperación de contraseña en el website?"

---

**FIN DEL CONTEXTO**

Fecha de creación: 28 de Noviembre de 2025  
Sistema: LC Mundo - Órdenes de Pago  
Estado: ✅ COMPLETADO Y FUNCIONAL

