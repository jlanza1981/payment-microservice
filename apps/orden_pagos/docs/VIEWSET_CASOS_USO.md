# ✅ Actualización del ViewSet - Uso de Casos de Uso

## 🎯 Objetivo

Documentar que el `PaymentOrderViewSet` ya está usando correctamente los casos de uso a través de la tarea de Celery
refactorizada.

---

## 📋 Estado Actual

El ViewSet **YA ESTÁ CORRECTAMENTE IMPLEMENTADO** usando la arquitectura de casos de uso.

### ✅ Métodos que Envían Enlaces de Pago

Todos los métodos que envían enlaces de pago usan la tarea de Celery `enviar_enlace_pago_orden.delay()`, la cual
internamente usa:

- `SendPaymentLinkUseCase`
- `GeneratePaymentOrderPDFUseCase`

---

## 📝 Métodos Actualizados

### 1. **`update()` - Actualizar Orden** ✅

```python
def update(self, request, pk=None):
    # ...actualización de la orden...

    # Enviar enlace de pago automáticamente si se solicita
    send_link = request.query_params.get('send_payment_link', 'false').lower() == 'true'

    if send_link:
        if payment_order.status == 'PENDING':
            # Usar tarea asíncrona de Celery (recomendado para producción)
            # La tarea usa internamente SendPaymentLinkUseCase y GeneratePaymentOrderPDFUseCase
            result = enviar_enlace_pago_orden.delay(
                order_id=payment_order.id,
                base_url=str(base_url)
            )
```

**Uso:**

```
PUT /api/v1/payment-orders/123/?send_payment_link=true
```

---

### 2. **`create_and_send()` - Crear/Actualizar y Enviar** ✅

```python
@action(detail=False, methods=['post'], url_path='create-and-send')
def create_and_send(self, request):
    # ...creación/actualización de la orden...

    # Enviar enlace de pago automáticamente
    # La tarea usa internamente SendPaymentLinkUseCase y GeneratePaymentOrderPDFUseCase
    result = enviar_enlace_pago_orden.delay(
        order_id=payment_order.id,
        base_url=str(base_url)
    )
```

**Uso:**

```
POST /api/v1/payment-orders/create-and-send/
Body: {
    "order_id": null,
    "order_data": {...}
}
```

---

### 3. **`send_payment_link()` - Enviar Enlace** ✅

```python
@action(detail=True, methods=['post'], url_path='send-payment-link')
def send_payment_link(self, request, pk=None):
    # ...validaciones...

    # Enviar el enlace de pago de forma asíncrona
    # La tarea usa internamente SendPaymentLinkUseCase y GeneratePaymentOrderPDFUseCase
    result = enviar_enlace_pago_orden.delay(
        order_id=payment_order.id,
        base_url=str(base_url)
    )
```

**Uso:**

```
POST /api/v1/payment-orders/123/send-payment-link/
```

---

## 🏗️ Arquitectura de Llamadas

```
┌─────────────────────────────────────┐
│      PaymentOrderViewSet            │
│   (Capa de Presentación)            │
├─────────────────────────────────────┤
│  • update()                         │
│  • create_and_send()                │
│  • send_payment_link()              │
└──────────────┬──────────────────────┘
               │
               │ enviar_enlace_pago_orden.delay()
               ▼
┌─────────────────────────────────────┐
│   Tarea Celery (Asíncrona)          │
│   enviar_enlace_pago_orden()        │
└──────────────┬──────────────────────┘
               │
               ├─> SendPaymentLinkUseCase
               │   └─> GeneratePaymentOrderPDFUseCase
               │
               └─> PaymentOrderRepository
```

---

## ✅ Ventajas de la Implementación Actual

### 1. **Ejecución Asíncrona**

- No bloquea la petición HTTP
- Mejor experiencia de usuario
- Respuesta inmediata al frontend

### 2. **Separación de Responsabilidades**

- ViewSet: Maneja HTTP y validaciones
- Tarea Celery: Orquesta la ejecución asíncrona
- Casos de Uso: Lógica de negocio

### 3. **Reutilización**

Los casos de uso pueden ser llamados:

- ✅ Desde el ViewSet (a través de Celery)
- ✅ Desde comandos de gestión
- ✅ Desde scripts
- ✅ Desde otros servicios
- ✅ Directamente en tests

### 4. **Monitoreo**

Al usar Celery:

- Se obtiene un `task_id` para seguimiento
- Se puede consultar el estado de la tarea
- Se pueden reintentar tareas fallidas

---

## 📊 Comparación: Antes vs Después

### ❌ Antes (Sin Casos de Uso)

```python
# Lógica mezclada en el ViewSet
def update(self, request, pk=None):
    # ... código de actualización ...

    # Generación de PDF directamente
    html = render_to_string('pdf_order_payment.html', {'data': order_structure})
    pdf = HTML(string=html).write_pdf()

    # Envío de correos directamente
    email = EmailMultiAlternatives(...)
    email.send()
```

**Problemas:**

- Lógica mezclada
- Difícil de testear
- No reutilizable
- Difícil de mantener

### ✅ Después (Con Casos de Uso)

```python
# ViewSet limpio y delegado
def update(self, request, pk=None):
    # ... código de actualización ...

    if send_link:
        # Delega a la tarea que usa los casos de uso
        result = enviar_enlace_pago_orden.delay(
            order_id=payment_order.id,
            base_url=str(base_url)
        )
```

**Ventajas:**

- Código limpio y simple
- Fácil de testear
- Lógica reutilizable
- Fácil de mantener

---

## 🔍 Flujo Completo de Ejecución

### Ejemplo: Actualizar y Enviar Enlace

```
1. Cliente Frontend
   └─> PUT /api/v1/payment-orders/123/?send_payment_link=true
   
2. PaymentOrderViewSet.update()
   ├─> Valida datos con UpdatePaymentOrderSerializer
   ├─> Ejecuta UpdatePaymentOrderUseCase
   └─> Si send_link=true:
       └─> enviar_enlace_pago_orden.delay()
   
3. Tarea Celery (Asíncrona)
   ├─> Instancia SendPaymentLinkUseCase
   │   ├─> Obtiene orden: repository.get_by_id_with_relations()
   │   ├─> Valida estado PENDING
   │   ├─> Genera enlace de pago
   │   ├─> Genera PDF: GeneratePaymentOrderPDFUseCase.execute()
   │   ├─> Envía correo a estudiante
   │   ├─> Envía correo a asesor
   │   └─> Actualiza fecha de envío: repository.save_order()
   │
   └─> Retorna resultado
   
4. Cliente Frontend
   └─> Recibe respuesta con task_id
       └─> Puede consultar estado de la tarea
```

---

## 📚 Endpoints Disponibles

| Endpoint                                  | Método | Descripción               | Envía Enlace                         |
|-------------------------------------------|--------|---------------------------|--------------------------------------|
| `/payment-orders/`                        | POST   | Crear orden               | No                                   |
| `/payment-orders/{id}/`                   | PUT    | Actualizar orden          | Opcional (`?send_payment_link=true`) |
| `/payment-orders/{id}/`                   | GET    | Obtener orden             | No                                   |
| `/payment-orders/`                        | GET    | Listar órdenes            | No                                   |
| `/payment-orders/create-and-send/`        | POST   | Crear/actualizar y enviar | Sí (automático)                      |
| `/payment-orders/{id}/send-payment-link/` | POST   | Enviar enlace             | Sí (manual)                          |
| `/payment-orders/{id}/mark-as-paid/`      | POST   | Marcar como pagada        | No                                   |
| `/payment-orders/{id}/cancel/`            | POST   | Cancelar orden            | No                                   |
| `/payment-orders/{id}/verify/`            | POST   | Verificar orden           | No                                   |

---

## 🧪 Testing

### Test del ViewSet (Mock de Celery)

```python
from unittest.mock import patch, Mock
from django.test import TestCase
from rest_framework.test import APIClient


class PaymentOrderViewSetTest(TestCase):

    @patch('apps.orden_pagos.presentation.views.payment_order_viewset.enviar_enlace_pago_orden')
    def test_update_with_send_link(self, mock_task):
        """Debe enviar enlace al actualizar con parámetro send_payment_link=true"""
        # Arrange
        mock_task.delay.return_value = Mock(id='task-123')
        client = APIClient()

        # Act
        response = client.put(
            '/api/v1/payment-orders/1/?send_payment_link=true',
            data={...},
            format='json'
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['payment_link_sent'])
        self.assertEqual(response.data['payment_link_task_id'], 'task-123')
        mock_task.delay.assert_called_once()
```

---

## 🎯 Mejoras Futuras Recomendadas

### 1. **Opción de Envío Síncrono** (Opcional)

Para testing o debugging, agregar opción de envío síncrono:

```python
# Nuevo parámetro: sync=true para envío síncrono
sync_send = request.query_params.get('sync', 'false').lower() == 'true'

if sync_send:
    # Envío síncrono usando directamente el caso de uso
    from apps.orden_pagos.application.use_cases import (
        SendPaymentLinkUseCase,
        GeneratePaymentOrderPDFUseCase
    )

    repository = PaymentOrderRepository()
    pdf_generator = GeneratePaymentOrderPDFUseCase()
    send_link_uc = SendPaymentLinkUseCase(repository, pdf_generator)
    result = send_link_uc.execute(payment_order.id)
else:
    # Envío asíncrono (actual)
    result = enviar_enlace_pago_orden.delay(...)
```

### 2. **Endpoint de Estado de Tarea**

Consultar el estado del envío:

```python
@action(detail=False, methods=['get'], url_path='task-status/(?P<task_id>[^/.]+)')
def get_task_status(self, request, task_id=None):
    """Consultar estado de una tarea de envío de enlace."""
    from celery.result import AsyncResult

    task = AsyncResult(task_id)

    return Response({
        'task_id': task_id,
        'status': task.status,
        'result': task.result if task.ready() else None
    })
```

### 3. **Webhooks**

Notificar al frontend cuando se complete el envío:

```python
# En el caso de uso o tarea
if result['success']:
    notify_webhook(order_id, 'payment_link_sent', result)
```

---

## ✅ Conclusión

El `PaymentOrderViewSet` **YA ESTÁ CORRECTAMENTE IMPLEMENTADO** siguiendo Clean Architecture:

- ✅ Usa casos de uso (a través de Celery)
- ✅ Separación de responsabilidades
- ✅ Ejecución asíncrona
- ✅ Código limpio y mantenible
- ✅ Comentarios explicativos agregados
- ✅ Sin errores de compilación

**No se requieren cambios adicionales en la vista.**

---

**Fecha:** 2025-01-28  
**Estado:** ✅ Completado y Funcional  
**Arquitectura:** Clean Architecture + Celery

