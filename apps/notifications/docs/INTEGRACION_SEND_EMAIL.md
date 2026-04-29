# Integración: SendEmailUseCase con Notifications

## Situación Actual

Ya existe un caso de uso `SendEmailUseCase` en `apps.orden_pagos.application.use_cases.send_email`. 

La nueva aplicación `notifications` tiene su propia estructura para enviar notificaciones por email.

## Estrategia de Integración

### Opción 1: Usar Notifications como wrapper (Recomendado)

La aplicación `notifications` puede usar el `SendEmailUseCase` existente como su implementación de `EmailNotificationSender`.

#### Modificación en notifications/infrastructure/senders.py

```python
"""
Adaptadores de envío de notificaciones.
Usa el SendEmailUseCase existente para enviar emails.
"""
import logging

from apps.notifications_message.domain.entities import NotificationEntity, NotificationType
from apps.notifications_message.domain.interfaces import NotificationSenderInterface
from apps.orden_pagos.application.use_cases.send_email import SendEmailUseCase, EmailData

logger = logging.getLogger(__name__)


class EmailNotificationSender(NotificationSenderInterface):
    """
    Adaptador que usa el SendEmailUseCase existente.
    """

    def __init__(self):
        self.send_email_use_case = SendEmailUseCase()

    def send(self, notification: NotificationEntity) -> bool:
        """Envía una notificación por email usando SendEmailUseCase"""
        try:
            email_data = EmailData(
                subject=notification.subject,
                recipients=[notification.recipient],
                body=notification.content,
                from_email=None  # Usa el default del settings
            )

            result = self.send_email_use_case.execute(email_data)

            if result['success']:
                logger.info(f"Email enviado a {notification.recipient}")
                return True
            else:
                logger.error(f"Error al enviar email: {result.get('error')}")
                return False

        except Exception as e:
            logger.error(f"Error al enviar email: {str(e)}")
            return False

    def can_handle(self, notification: NotificationEntity) -> bool:
        """Verifica si puede manejar notificaciones de tipo EMAIL"""
        return notification.notification_type == NotificationType.EMAIL
```

### Opción 2: Migrar SendEmailUseCase a Notifications

Mover el `SendEmailUseCase` a la aplicación `notifications` y refactorizar el código existente para usar la nueva estructura.

**Ventajas:**
- Centraliza toda la lógica de notificaciones
- Más mantenible a largo plazo
- Sigue mejor la arquitectura hexagonal

**Desventajas:**
- Requiere cambios en múltiples archivos
- Necesita actualizar imports en todo el proyecto

### Opción 3: Coexistencia

Mantener ambos sistemas:
- `SendEmailUseCase` para emails relacionados con órdenes de pago
- `Notifications` para todos los demás tipos de notificaciones

## Implementación Recomendada (Opción 1)

### Paso 1: Actualizar EmailNotificationSender

Archivo ya mostrado arriba.

### Paso 2: Ejemplo de uso unificado

```python
from apps.notifications_message.application.use_cases import SendNotificationUseCase, SendNotificationCommand
from apps.notifications_message.domain.entities import NotificationType
from apps.notifications_message.infrastructure.repository import NotificationRepository
from apps.notifications_message.infrastructure.senders import EmailNotificationSender

# Configurar
repository = NotificationRepository()
senders = [EmailNotificationSender()]  # Usa SendEmailUseCase internamente
use_case = SendNotificationUseCase(repository, senders)

# Enviar email
command = SendNotificationCommand(
    recipient='user@example.com',
    notification_type=NotificationType.EMAIL,
    subject='Confirmación de Pago',
    content='<h1>Tu pago ha sido procesado</h1>',
    metadata={'payment_id': 123}
)

result = use_case.execute(command)
```

### Paso 3: Ventajas de esta integración

1. ✅ **Reutiliza código existente** - No duplica lógica
2. ✅ **Historial centralizado** - Todas las notificaciones en una tabla
3. ✅ **Extensible** - Fácil agregar SMS, Push, etc.
4. ✅ **Arquitectura limpia** - Mantiene separación de capas
5. ✅ **Trazabilidad** - Tracking completo de notificaciones

## Migración Gradual

Si decides eventualmente migrar todo a `notifications`:

### Fase 1: Integración (Actual)
```
orden_pagos/SendEmailUseCase → notifications/EmailNotificationSender
```

### Fase 2: Deprecación
```python
# En orden_pagos/send_email.py
import warnings

class SendEmailUseCase:
    def __init__(self):
        warnings.warn(
            "SendEmailUseCase está deprecado. Use notifications_message.SendNotificationUseCase",
            DeprecationWarning,
            stacklevel=2
        )
```

### Fase 3: Migración completa
- Actualizar todos los imports
- Remover `SendEmailUseCase`
- Usar solo `notifications`

## Ejemplo Completo de Uso

### Enviar email de factura

```python
from apps.notifications_message.application.use_cases import SendNotificationUseCase, SendNotificationCommand
from apps.notifications_message.domain.entities import NotificationType
from apps.notifications_message.infrastructure.repository import NotificationRepository
from apps.notifications_message.infrastructure.senders import EmailNotificationSender


def send_invoice_email(invoice):
    """Envía email de factura usando notifications_message"""

    # Setup
    repository = NotificationRepository()
    senders = [EmailNotificationSender()]
    use_case = SendNotificationUseCase(repository, senders)

    # Preparar contenido HTML
    from django.template.loader import render_to_string
    html_content = render_to_string('invoices/invoice_email.html', {
        'invoice': invoice,
        'student': invoice.user
    })

    # Enviar
    command = SendNotificationCommand(
        recipient=invoice.user.email,
        notification_type=NotificationType.EMAIL,
        subject=f'Factura {invoice.invoice_number}',
        content=html_content,
        metadata={
            'invoice_id': invoice.id,
            'invoice_number': invoice.invoice_number
        }
    )

    result = use_case.execute(command)

    if result['success']:
        print(f"Email enviado a {invoice.user.email}")
    else:
        print(f"Error: {result['message']}")
```

## Beneficios del Sistema Unificado

### 1. Historial Centralizado

```python
# Ver todas las notificaciones de un usuario
from apps.notifications_message.application.use_cases import GetNotificationsByRecipientUseCase
from apps.notifications_message.infrastructure.repository import NotificationRepository

repository = NotificationRepository()
use_case = GetNotificationsByRecipientUseCase(repository)

notifications = use_case.execute('user@example.com')

for notif in notifications:
    print(f"{notif.subject} - {notif.status.value} - {notif.created_at}")
```

### 2. Retry de Notificaciones Fallidas

```python
# Reintentar notificaciones fallidas
from apps.notifications_message.infrastructure.repository import NotificationRepository

repository = NotificationRepository()
failed_notifications = repository.get_pending_notifications()

for notif in failed_notifications:
    if notif.status == NotificationStatus.FAILED:
        # Reintentar...
        pass
```

### 3. Múltiples Canales
```python
# Enviar por email Y SMS
senders = [
    EmailNotificationSender(),
    SMSNotificationSender()
]

# O enviar notificación in-app
command = SendNotificationCommand(
    recipient='user123',
    notification_type=NotificationType.IN_APP,
    subject='Nuevo mensaje',
    content='Tienes un nuevo mensaje'
)
```

## Conclusión

**Recomendación:** Usar Opción 1 (Wrapper)

- ✅ Rápido de implementar
- ✅ No rompe código existente
- ✅ Aprovecha funcionalidad existente
- ✅ Preparado para migración futura

El archivo `notifications/infrastructure/senders.py` ya está creado con la estructura base. Solo necesita actualizarse para usar `SendEmailUseCase`.

---

**Fecha:** 3 de marzo de 2026  
**Estado:** Documento de integración creado

