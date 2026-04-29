# Aplicación: Notifications

## Descripción

Esta aplicación maneja el envío y gestión de notificaciones del sistema.

## Arquitectura Hexagonal

```
notifications/
├── domain/             # Capa de Dominio (Lógica de Negocio Pura)
│   ├── entities.py    # Entidades: NotificationEntity
│   └── interfaces.py  # Contratos: NotificationRepositoryInterface, NotificationSenderInterface
│
├── application/        # Capa de Aplicación (Casos de Uso)
│   └── use_cases.py   # SendNotificationUseCase, GetNotificationsByRecipientUseCase
│
└── infrastructure/     # Capa de Infraestructura (Adaptadores)
    ├── models.py      # Modelo Django: Notification
    ├── repository.py  # Implementación: NotificationRepository
    └── senders.py     # Implementaciones: EmailSender, SMSSender, PushSender, InAppSender
```

## Tipos de Notificaciones

- **EMAIL**: Notificaciones por correo electrónico
- **SMS**: Notificaciones por mensaje de texto
- **PUSH**: Notificaciones push móviles
- **IN_APP**: Notificaciones dentro de la aplicación

## Estados de Notificación

- **PENDING**: Pendiente de envío
- **SENT**: Enviada
- **DELIVERED**: Entregada
- **FAILED**: Falló el envío
- **READ**: Leída por el usuario

## Uso

### Enviar una notificación por email

```python
from apps.notifications_message.application.use_cases import SendNotificationUseCase, SendNotificationCommand
from apps.notifications_message.domain.entities.entities import NotificationType
from apps.notifications_message.infrastructure.repository import NotificationRepository
from apps.notifications_message.infrastructure.senders import EmailNotificationSender

# Configurar dependencias
repository = NotificationRepository()
senders = [EmailNotificationSender()]

# Crear caso de uso
use_case = SendNotificationUseCase(repository, senders)

# Crear comando
command = SendNotificationCommand(
    recipient='user@example.com',
    notification_type=NotificationType.EMAIL,
    subject='Bienvenido',
    content='<h1>Hola!</h1><p>Gracias por registrarte.</p>',
    metadata={'user_id': 123}
)

# Ejecutar
result = use_case.execute(command)
```

### Obtener notificaciones de un usuario

```python
from apps.notifications_message.application.use_cases import GetNotificationsByRecipientUseCase
from apps.notifications_message.infrastructure.repository import NotificationRepository

repository = NotificationRepository()
use_case = GetNotificationsByRecipientUseCase(repository)

notifications = use_case.execute('user@example.com')
```

## Templates de Email

Las plantillas HTML para emails se almacenan en:

```
infrastructure/emails/templates/
├── invoices/
│   └── invoice_email.html
├── payment_orders/
│   └── payment_link.html
└── receipts/
    └── receipt_email.html
```

## Extensibilidad

### Agregar un nuevo sender de email

1. Crear una clase en `infrastructure/emails/` implementando el puerto `EmailSender`
2. Implementar el método `send(email_data: EmailData) -> None`
3. Inyectar el nuevo sender en el caso de uso

Ejemplo:
```python
from apps.notifications_message.domain.ports.email_sender import EmailSender
from apps.notifications_message.domain.entities.email_data import EmailData

class SendGridEmailSender(EmailSender):
    def send(self, email_data: EmailData) -> None:
        # Implementar envío con SendGrid API
        pass
```

## Configuración de Django Email

Configurar el backend de email en `settings.py`:

```python
# Para desarrollo (emails en consola)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Para producción (SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu_email@gmail.com'
EMAIL_HOST_PASSWORD = 'tu_password'
DEFAULT_FROM_EMAIL = 'noreply@lcmundo.com'
```

## Dependencias

- **Django**: Backend de email integrado
- **django.core.mail**: Para envío de emails
- **django.template.loader**: Para renderizado de templates

## Notas

- Esta aplicación está enfocada específicamente en el envío de emails
- No incluye modelos de Django ni persistencia de notificaciones
- Funciona como una utilidad de envío de correos con templates HTML
- Los errores se manejan mediante excepciones que el caso de uso captura y loggea

## Testing

Para testear el envío de emails en desarrollo:

```python
from django.core import mail

# Después de enviar un email en tests
assert len(mail.outbox) == 1
assert mail.outbox[0].subject == "Test Subject"
assert mail.outbox[0].to == ["test@example.com"]
```

## Mejores Prácticas

1. ✅ Siempre usar templates HTML para emails complejos
2. ✅ Validar datos antes de crear `EmailData`
3. ✅ Manejar errores apropiadamente con try-except
4. ✅ Usar adjuntos solo cuando sea necesario
5. ✅ Personalizar el remitente según el tipo de email
6. ✅ Configurar SPF, DKIM y DMARC en producción

