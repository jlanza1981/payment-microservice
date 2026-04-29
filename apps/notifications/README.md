# Aplicación: Notifications Message
## Descripción
Esta aplicación maneja el envío de correos electrónicos del sistema, incluyendo notificaciones, facturas, órdenes de pago y comunicaciones con estudiantes.
## Arquitectura Hexagonal
```
notifications_message/
├── domain/                     # Capa de Dominio (Lógica de Negocio Pura)
│   ├── entities/
│   │   └── email_data.py      # EmailData, EmailAttachment
│   └── ports/
│       └── email_sender.py    # EmailSender (Puerto/Interfaz)
│
├── application/                # Capa de Aplicación (Casos de Uso)
│   └── send_email.py          # SendEmailUseCase
│
└── infrastructure/             # Capa de Infraestructura (Adaptadores)
    └── emails/
        ├── django_email_sender.py  # Implementación con Django Email
        └── templates/              # Plantillas HTML para emails
```
## Funcionalidad Principal
- **Envío de Emails**: Usando el backend de email configurado en Django (SMTP, Console, etc.)
- **Soporte para Templates HTML**: Renderizado de plantillas con contexto
- **Adjuntos**: Envío de archivos adjuntos (PDFs, imágenes, etc.)
- **CC y BCC**: Soporte para copias y copias ocultas
- **Validaciones**: Validación automática de datos del email
## Uso
### Enviar un email simple
```python
from apps.notifications_message.application.send_email import SendEmailUseCase
from apps.notifications_message.infrastructure.emails.django_email_sender import DjangoEmailSender
from apps.notifications_message.domain.entities.email_data import EmailData
# Configurar sender
email_sender = DjangoEmailSender()
use_case = SendEmailUseCase(email_sender=email_sender)
# Preparar datos del email
email_data = EmailData(
    subject="Bienvenido a LC Mundo",
    recipients=["estudiante@example.com"],
    body="<h1>¡Bienvenido!</h1><p>Gracias por unirte.</p>"
)
# Enviar
result = use_case.execute(email_data)
if result['success']:
    print(f"Email enviado a: {', '.join(result['recipients'])}")
else:
    print(f"Error: {result['error']}")
```
### Enviar email con template HTML
```python
# Datos para la plantilla
template_context = {
    'student_name': 'Juan Pérez',
    'course_name': 'Python Avanzado',
    'start_date': '2026-04-01'
}
# Preparar email con template
email_data = EmailData(
    subject="Confirmación de Inscripción",
    recipients=["juan.perez@example.com"],
    template_name="emails/course_confirmation.html",
    template_context=template_context
)
result = use_case.execute(email_data)
```
### Enviar email con adjunto (PDF)
```python
from apps.notifications_message.domain.entities.email_data import EmailAttachment
# Crear adjunto
pdf_attachment = EmailAttachment(
    filename="factura_001.pdf",
    content=pdf_content,  # bytes del PDF
    mimetype="application/pdf"
)
# Preparar email
email_data = EmailData(
    subject="Tu Factura - Orden #001",
    recipients=["cliente@example.com"],
    body="<p>Adjunto encontrarás tu factura.</p>",
    attachments=[pdf_attachment]
)
result = use_case.execute(email_data)
```
**📖 Ver más ejemplos en [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)**
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
