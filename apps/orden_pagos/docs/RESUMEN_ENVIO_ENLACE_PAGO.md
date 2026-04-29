# Implementación de Envío de Enlace de Pago - Órdenes de Pago

## Resumen

Se ha implementado exitosamente la funcionalidad para enviar enlaces de pago por correo electrónico a estudiantes y
asesores cuando se crea o actualiza una orden de pago.

## Archivos Creados

### 1. **Templates HTML**

#### `apps/orden_pagos/templates/correo-enlace-pago-orden.html`

- Plantilla de correo electrónico para enviar al estudiante y asesor
- Incluye:
    - Saludo personalizado
    - Número de orden y monto total
    - Opción de incluir credenciales de acceso
    - Botón de "Pagar aquí" con enlace directo
    - Mensaje de PDF adjunto

#### `apps/orden_pagos/templates/pdf_orden_pago.html`

- Plantilla para generar el PDF de la orden de pago
- Incluye:
    - Información del estudiante
    - Detalle de la orden (número, fecha, estado)
    - Información del programa (si aplica)
    - Tabla de conceptos de pago con descuentos
    - Total a pagar
    - Branding de LC Mundo

### 2. **Módulo de Tareas (Celery)**

#### `apps/orden_pagos/tasks.py`

Contiene dos funciones principales:

##### `enviar_enlace_pago_orden(order_id, enviar_clave, password_nueva, base_url)`

- Tarea asíncrona para enviar el enlace de pago
- Valida que la orden esté en estado PENDING
- Genera el PDF de la orden usando WeasyPrint
- Envía correos a:
    - Estudiante con enlace y PDF
    - Asesor con copia del enlace y PDF
- Actualiza `payment_link_date` automáticamente
- Manejo robusto de errores con logging
- Retorna diccionario con resultado del envío

##### `generar_pdf_orden_pago(payment_order, base_url)`

- Función auxiliar para generar PDF de una orden
- Usa la estructura completa de la orden
- Aplica estilos CSS existentes del sistema

### 3. **Serializer para Validación**

#### `apps/orden_pagos/infrastructure/serializers/payment_order_input_serializer.py`

Se agregó:

##### `SendPaymentLinkSerializer`

- Valida parámetros de entrada para el envío
- Campos:
    - `send_password` (boolean): Si se debe enviar contraseña
    - `new_password` (string): Contraseña a enviar
- Validación: Si `send_password=True`, `new_password` es requerido

### 4. **Endpoint en ViewSet**

#### `apps/orden_pagos/presentation/views/payment_order_viewset.py`

Se agregó:

##### `send_payment_link(request, pk)`

- **Ruta**: `POST /api/v1/payment-orders/{id}/send-payment-link/`
- **Funcionalidad**:
    - Valida datos de entrada con `SendPaymentLinkSerializer`
    - Verifica que la orden esté en estado PENDING
    - Ejecuta tarea asíncrona de envío
    - Retorna información de confirmación con task_id
- **Respuestas**:
    - 200: Envío iniciado correctamente
    - 400: Error de validación o estado inválido
    - 404: Orden no encontrada
    - 500: Error interno del servidor

## Características Implementadas

### ✅ Validaciones

- Solo órdenes en estado PENDING pueden enviar enlace
- Validación de contraseña si se requiere
- Validación de existencia de la orden

### ✅ Generación de PDF

- PDF completo con estructura de la orden
- Incluye información del programa
- Tabla detallada de conceptos de pago
- Descuentos aplicados
- Branding corporativo

### ✅ Envío de Correos

- Correo personalizado al estudiante
- Correo de notificación al asesor
- PDF adjunto en ambos correos
- Opción de incluir credenciales de acceso
- Asunto dinámico según tipos de pago

### ✅ Proceso Asíncrono

- Usa Celery para no bloquear la respuesta
- Retorna task_id para seguimiento
- Logging completo de operaciones
- Manejo de errores robusto

### ✅ Actualización Automática

- Actualiza `payment_link_date` al enviar
- Mantiene historial de envíos

## Uso del Endpoint

### Ejemplo 1: Envío Simple

```bash
POST /api/v1/payment-orders/1/send-payment-link/
Content-Type: application/json
Authorization: Bearer TOKEN

{}
```

### Ejemplo 2: Envío con Contraseña

```bash
POST /api/v1/payment-orders/1/send-payment-link/
Content-Type: application/json
Authorization: Bearer TOKEN

{
  "send_password": true,
  "new_password": "temporal123"
}
```

### Respuesta Exitosa

```json
{
  "message": "El enlace de pago para la orden OP202400001 está siendo enviado.",
  "order_number": "OP202400001",
  "task_id": "abc123-def456-ghi789",
  "student_email": "estudiante@example.com",
  "advisor_email": "asesor@example.com"
}
```

## Integración con el Sistema Existente

La implementación se basa en el código existente de `apps/website/tasks.py` (función `EnviarEnlacePago`), adaptado a la
arquitectura de la app `orden_pagos`:

### Similitudes con el Sistema Original

- Uso de WeasyPrint para generar PDFs
- Plantillas HTML con Django templates
- Envío de correos con `EmailMultiAlternatives`
- Adjuntar PDF a los correos
- Envío a estudiante y asesor
- Opción de incluir credenciales

### Mejoras Implementadas

- Proceso asíncrono con Celery
- Validación con serializers de DRF
- Arquitectura limpia (separación de responsabilidades)
- Mejor manejo de errores
- Logging estructurado
- Respuesta inmediata al cliente
- Task ID para seguimiento

## Dependencias Requeridas

Las siguientes dependencias ya están en el proyecto:

- Django
- Django REST Framework
- Celery
- WeasyPrint
- django.core.mail

## Próximos Pasos (Opcional)

1. **Configurar URL de Pago Real**: Actualizar el enlace de pago en `tasks.py` línea 56
2. **Personalizar Plantillas**: Ajustar diseño de correo y PDF según necesidades
3. **Agregar Tests**: Crear tests unitarios y de integración
4. **Webhook de Estado**: Implementar endpoint para recibir confirmación de pago
5. **Notificaciones**: Agregar notificaciones push o SMS
6. **Panel de Seguimiento**: Dashboard para ver estado de envíos

## Documentación

Se actualizó el archivo `PAYMENT_ORDERS_API_DOCUMENTATION.md` con:

- Descripción completa del endpoint
- Ejemplos de uso
- Respuestas posibles
- Notas sobre funcionalidades

## Testing Manual

Para probar la funcionalidad:

1. Crear una orden de pago en estado PENDING
2. Llamar al endpoint `send-payment-link`
3. Verificar que se reciben los correos
4. Comprobar que el PDF se genera correctamente
5. Verificar que `payment_link_date` se actualiza

```bash
# Crear orden
POST /api/v1/payment-orders/

# Enviar enlace
POST /api/v1/payment-orders/1/send-payment-link/

# Verificar la orden
GET /api/v1/payment-orders/1/
```

## Notas Importantes

1. **Celery debe estar corriendo**: Asegúrate de que el worker de Celery esté activo
2. **Configuración de Email**: Verifica que `EMAIL_HOST_USER` esté configurado en settings
3. **Base URL**: La URL de pago debe configurarse según tu dominio
4. **CSS del PDF**: Usa el archivo existente `static/css/pdf_planilla.css`
5. **Plantilla Base**: El correo extiende `base_correo.html` que debe existir

## Configuración Adicional Requerida

En `settings.py`, asegúrate de tener:

```python
# Email configuration
EMAIL_HOST_USER = 'tu_email@example.com'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_PASSWORD = 'tu_password'

# Celery configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Base URL for PDF generation
BASE_DIR = Path(__file__).resolve().parent.parent
```

---

**Fecha de Implementación**: 28 de Noviembre de 2025
**Desarrollado para**: Sistema de Órdenes de Pago - LC Mundo

