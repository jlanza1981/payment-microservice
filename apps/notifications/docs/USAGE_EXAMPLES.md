# Ejemplos de Uso - notifications_message App

## 🎯 Uso Básico

### 1. Enviar Email Simple con HTML

```python
from apps.notifications_message.application.send_email import SendEmailUseCase
from apps.notifications_message.infrastructure.emails.django_email_sender import DjangoEmailSender
from apps.notifications_message.domain.entities.email_data import EmailData

# Configurar el sender
email_sender = DjangoEmailSender()
use_case = SendEmailUseCase(email_sender=email_sender)

# Preparar datos del email
email_data = EmailData(
    subject="Bienvenido a LC Mundo",
    recipients=["estudiante@example.com"],
    body="""
        <h1>¡Bienvenido!</h1>
        <p>Gracias por unirte a nuestra plataforma.</p>
    """
)

# Enviar email
result = use_case.execute(email_data)

if result['success']:
    print(f"✅ Email enviado a: {', '.join(result['recipients'])}")
else:
    print(f"❌ Error: {result['error']}")
```

### 2. Enviar Email usando Template HTML

```python
from apps.notifications_message.application.send_email import SendEmailUseCase
from apps.notifications_message.infrastructure.emails.django_email_sender import DjangoEmailSender
from apps.notifications_message.domain.entities.email_data import EmailData

# Configurar
email_sender = DjangoEmailSender()
use_case = SendEmailUseCase(email_sender=email_sender)

# Datos para la plantilla
template_context = {
    'student_name': 'Juan Pérez',
    'course_name': 'Python Avanzado',
    'start_date': '2026-04-01',
    'instructor': 'María García'
}

# Preparar email con template
email_data = EmailData(
    subject="Confirmación de Inscripción - Python Avanzado",
    recipients=["juan.perez@example.com"],
    template_name="emails/course_confirmation.html",
    template_context=template_context
)

# Enviar
result = use_case.execute(email_data)

if result['success']:
    print(f"✅ Confirmación enviada a {result['recipients'][0]}")
```

### 3. Enviar Email con Adjuntos (PDF)

```python
from apps.notifications_message.application.send_email import SendEmailUseCase
from apps.notifications_message.infrastructure.emails.django_email_sender import DjangoEmailSender
from apps.notifications_message.domain.entities.email_data import EmailData, EmailAttachment

# Supongamos que ya generaste un PDF
pdf_content = b'...'  # Contenido del PDF en bytes

# Crear adjunto
pdf_attachment = EmailAttachment(
    filename="factura_001.pdf",
    content=pdf_content,
    mimetype="application/pdf"
)

# Preparar email con adjunto
email_data = EmailData(
    subject="Tu Factura - Orden #001",
    recipients=["cliente@example.com"],
    body="<p>Adjunto encontrarás tu factura.</p>",
    attachments=[pdf_attachment]
)

# Enviar
email_sender = DjangoEmailSender()
use_case = SendEmailUseCase(email_sender=email_sender)
result = use_case.execute(email_data)

print(f"Email {'enviado' if result['success'] else 'falló'}")
```

### 4. Enviar Email con Múltiples Adjuntos

```python
from apps.notifications_message.domain.entities.email_data import EmailData, EmailAttachment

# Crear múltiples adjuntos
attachments = [
    EmailAttachment(
        filename="contrato.pdf",
        content=contrato_bytes,
        mimetype="application/pdf"
    ),
    EmailAttachment(
        filename="terminos.pdf",
        content=terminos_bytes,
        mimetype="application/pdf"
    ),
    EmailAttachment(
        filename="logo.png",
        content=logo_bytes,
        mimetype="image/png"
    )
]

# Preparar email
email_data = EmailData(
    subject="Documentos de Inscripción",
    recipients=["estudiante@example.com"],
    template_name="emails/documents.html",
    template_context={"student_name": "Ana López"},
    attachments=attachments
)

# Enviar
result = use_case.execute(email_data)
```

### 5. Enviar Email con CC y BCC

```python
email_data = EmailData(
    subject="Reporte Mensual",
    recipients=["gerente@example.com"],
    cc=["supervisor@example.com", "rrhh@example.com"],
    bcc=["admin@example.com"],  # Copia oculta
    template_name="emails/monthly_report.html",
    template_context={"month": "Marzo", "year": 2026}
)

result = use_case.execute(email_data)
```

### 6. Enviar Email con Remitente Personalizado

```python
email_data = EmailData(
    subject="Notificación de Soporte",
    recipients=["cliente@example.com"],
    from_email="soporte@lcmundo.com",  # Remitente personalizado
    body="<p>Tu ticket ha sido actualizado.</p>"
)

result = use_case.execute(email_data)
```

---

## 🏗️ Integración con Otros Casos de Uso

### Ejemplo 1: Enviar Factura por Email (con PDF generado)

```python
from apps.documents.application.generate_pdf import GeneratePDFUseCase
from apps.documents.infrastructure.pdf.weasyprint_pdf_generator import WeasyPrintPDFGenerator
from apps.notifications_message.application.send_email import SendEmailUseCase
from apps.notifications_message.infrastructure.emails.django_email_sender import DjangoEmailSender
from apps.notifications_message.domain.entities.email_data import EmailData, EmailAttachment

def send_invoice_email(invoice):
    """Genera PDF de factura y lo envía por email"""
    
    # 1. Generar PDF
    pdf_generator = WeasyPrintPDFGenerator()
    pdf_use_case = GeneratePDFUseCase(pdf_generator=pdf_generator)
    
    invoice_data = {
        'invoice_number': invoice.number,
        'student_name': invoice.student.full_name,
        'amount': invoice.total,
        'date': invoice.date.strftime('%Y-%m-%d')
    }
    
    pdf_content, pdf_path = pdf_use_case.execute(
        data_structure=invoice_data,
        template_name='invoices/pdf_invoice.html',
        css_filename='pdf_invoice.css',
        folder='invoices',
        document_type='invoice'
    )
    
    # 2. Crear adjunto
    pdf_attachment = EmailAttachment(
        filename=f"factura_{invoice.number}.pdf",
        content=pdf_content,
        mimetype="application/pdf"
    )
    
    # 3. Enviar email
    email_sender = DjangoEmailSender()
    email_use_case = SendEmailUseCase(email_sender=email_sender)
    
    email_data = EmailData(
        subject=f"Factura #{invoice.number} - LC Mundo",
        recipients=[invoice.student.email],
        template_name="emails/invoice_notification.html",
        template_context={
            'student_name': invoice.student.full_name,
            'invoice_number': invoice.number,
            'amount': invoice.total
        },
        attachments=[pdf_attachment]
    )
    
    result = email_use_case.execute(email_data)
    
    # 4. Guardar ruta del PDF en la factura
    if result['success']:
        invoice.pdf_path = pdf_path
        invoice.email_sent = True
        invoice.save()
    
    return result
```

### Ejemplo 2: Enviar Enlace de Pago con PDF

```python
def send_payment_link(payment_order):
    """Envía enlace de pago con PDF de orden adjunto"""
    
    # 1. Generar token de pago
    token = generate_payment_token(payment_order)
    payment_link = f"https://lcmundo.com/pay/{token}/"
    
    # 2. Generar PDF de la orden
    pdf_generator = WeasyPrintPDFGenerator()
    pdf_use_case = GeneratePDFUseCase(pdf_generator=pdf_generator)
    
    order_data = payment_order.get_order_structure()
    pdf_content, pdf_path = pdf_use_case.execute(
        data_structure=order_data,
        template_name='payment_orders/pdf_order_payment.html',
        css_filename='pdf_order_payment.css',
        folder='payment_orders',
        document_type='payment_order'
    )
    
    # 3. Preparar email
    email_sender = DjangoEmailSender()
    email_use_case = SendEmailUseCase(email_sender=email_sender)
    
    pdf_attachment = EmailAttachment(
        filename=f"orden_pago_{payment_order.order_number}.pdf",
        content=pdf_content,
        mimetype="application/pdf"
    )
    
    email_data = EmailData(
        subject=f"Orden de Pago #{payment_order.order_number} - Realiza tu pago",
        recipients=[payment_order.student.email, payment_order.advisor.email],
        template_name="emails/payment_link.html",
        template_context={
            'student_name': payment_order.student.full_name,
            'order_number': payment_order.order_number,
            'amount': payment_order.total_amount,
            'payment_link': payment_link,
            'expiration_date': payment_order.link_expires_at
        },
        attachments=[pdf_attachment]
    )
    
    result = email_use_case.execute(email_data)
    
    # 4. Actualizar orden
    if result['success']:
        payment_order.pdf_file_path = pdf_path
        payment_order.payment_link_sent_at = datetime.now()
        payment_order.save()
    
    return result
```

---

## 🔧 Uso Avanzado

### 7. Manejo de Errores Personalizado

```python
from apps.notifications_message.infrastructure.emails.django_email_sender import EmailSendError

try:
    result = use_case.execute(email_data)
    
    if result['success']:
        print(f"✅ Email enviado a {len(result['recipients'])} destinatarios")
    else:
        print(f"⚠️ Error controlado: {result['message']}")
        
except EmailSendError as e:
    # Error específico de envío de email
    logger.error(f"Error al enviar email: {e}")
    notify_admin(f"Fallo en envío de email: {e}")
    
except Exception as e:
    # Cualquier otro error
    logger.error(f"Error inesperado: {e}")
```

### 8. Envío Masivo de Emails

```python
def send_bulk_emails(students, subject, template_name, context_generator):
    """
    Envía emails masivos a múltiples estudiantes.
    
    Args:
        students: Lista de estudiantes
        subject: Asunto del email
        template_name: Nombre de la plantilla
        context_generator: Función que genera el contexto para cada estudiante
    """
    email_sender = DjangoEmailSender()
    use_case = SendEmailUseCase(email_sender=email_sender)
    
    results = []
    
    for student in students:
        try:
            # Generar contexto personalizado para cada estudiante
            context = context_generator(student)
            
            email_data = EmailData(
                subject=subject,
                recipients=[student.email],
                template_name=template_name,
                template_context=context
            )
            
            result = use_case.execute(email_data)
            results.append({
                'student_id': student.id,
                'email': student.email,
                'success': result['success'],
                'error': result.get('error')
            })
            
        except Exception as e:
            logger.error(f"Error enviando email a {student.email}: {e}")
            results.append({
                'student_id': student.id,
                'email': student.email,
                'success': False,
                'error': str(e)
            })
    
    # Resumen
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    return {
        'total': len(results),
        'successful': successful,
        'failed': failed,
        'details': results
    }

# Uso
students = Student.objects.filter(active=True)

def generate_context(student):
    return {
        'name': student.full_name,
        'courses': student.enrolled_courses.count()
    }

results = send_bulk_emails(
    students=students,
    subject="Novedades del Mes",
    template_name="emails/monthly_newsletter.html",
    context_generator=generate_context
)

print(f"Enviados: {results['successful']}/{results['total']}")
```

### 9. Uso Directo del Sender (Sin UseCase)

Si el UseCase no agrega valor en tu caso específico, puedes usar el sender directamente:

```python
from apps.notifications_message.infrastructure.emails.django_email_sender import DjangoEmailSender
from apps.notifications_message.domain.entities.email_data import EmailData

# Usar directamente el sender
email_sender = DjangoEmailSender()

email_data = EmailData(
    subject="Test",
    recipients=["test@example.com"],
    body="<p>Test message</p>"
)

try:
    email_sender.send(email_data)
    print("✅ Email enviado")
except Exception as e:
    print(f"❌ Error: {e}")
```

---

## 🧪 Testing

### Test Unitario del UseCase

```python
from unittest.mock import Mock, patch
from django.test import TestCase
from apps.notifications_message.application.send_email import SendEmailUseCase
from apps.notifications_message.domain.entities.email_data import EmailData

class TestSendEmailUseCase(TestCase):
    
    def setUp(self):
        self.mock_sender = Mock()
        self.use_case = SendEmailUseCase(email_sender=self.mock_sender)
        
    def test_send_email_success(self):
        """Prueba envío exitoso de email"""
        email_data = EmailData(
            subject="Test",
            recipients=["test@example.com"],
            body="<p>Test</p>"
        )
        
        # Mock no lanza excepción = éxito
        self.mock_sender.send.return_value = None
        
        # Ejecutar
        result = self.use_case.execute(email_data)
        
        # Verificar
        self.assertTrue(result['success'])
        self.assertEqual(result['recipients'], ["test@example.com"])
        self.mock_sender.send.assert_called_once_with(email_data)
    
    def test_send_email_failure(self):
        """Prueba fallo en envío de email"""
        email_data = EmailData(
            subject="Test",
            recipients=["test@example.com"],
            body="<p>Test</p>"
        )
        
        # Mock lanza excepción
        self.mock_sender.send.side_effect = Exception("SMTP Error")
        
        # Ejecutar
        result = self.use_case.execute(email_data)
        
        # Verificar
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('SMTP Error', result['error'])
```

### Test de Integración

```python
from django.test import TestCase
from django.core import mail
from apps.notifications_message.application.send_email import SendEmailUseCase
from apps.notifications_message.infrastructure.emails.django_email_sender import DjangoEmailSender
from apps.notifications_message.domain.entities.email_data import EmailData

class TestEmailIntegration(TestCase):
    
    def test_send_email_with_django_backend(self):
        """Prueba envío real usando el backend de Django"""
        # Configurar (Django usa EmailBackend en memoria para tests)
        email_sender = DjangoEmailSender()
        use_case = SendEmailUseCase(email_sender=email_sender)
        
        email_data = EmailData(
            subject="Test Integration",
            recipients=["test@example.com"],
            body="<h1>Test</h1>"
        )
        
        # Ejecutar
        result = use_case.execute(email_data)
        
        # Verificar
        self.assertTrue(result['success'])
        
        # Verificar que el email se guardó en la bandeja de salida
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Test Integration")
        self.assertEqual(mail.outbox[0].to, ["test@example.com"])
```

---

## 📝 Notas Importantes

### ✅ Validaciones en EmailData

La clase `EmailData` valida automáticamente los datos en `__post_init__`:

```python
# ❌ Esto lanza ValueError
email_data = EmailData(
    subject="Test",
    recipients=[]  # Error: debe tener al menos un destinatario
)

# ❌ Esto lanza ValueError
email_data = EmailData(
    subject="Test",
    recipients=["test@example.com"]
    # Error: falta body o template_name
)

# ✅ Esto es correcto
email_data = EmailData(
    subject="Test",
    recipients=["test@example.com"],
    body="<p>Message</p>"
)
```

### 🎨 Templates de Email

Los templates HTML para emails deben estar en:

```
templates/
└── emails/
    ├── welcome.html
    ├── invoice_notification.html
    ├── payment_link.html
    └── course_confirmation.html
```

### 📧 Configuración de Django Email

Asegúrate de tener configurado el backend de email en `settings.py`:

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

### 🔒 Seguridad

- **NO** incluir emails en logs de producción (datos sensibles)
- Validar emails antes de enviar
- Usar rate limiting para envíos masivos
- Configurar SPF, DKIM y DMARC en tu dominio

### ⚡ Performance

Para envíos masivos, considera:
- Usar Celery para envío asíncrono
- Implementar batch sending
- Usar servicios especializados (SendGrid, AWS SES, Mailgun)

---

## 🚀 Mejores Prácticas

1. **Siempre usar templates** para emails complejos
2. **Validar datos** antes de crear EmailData
3. **Manejar errores** apropiadamente
4. **Loggear eventos** importantes
5. **Testear emails** en desarrollo antes de producción
6. **Usar adjuntos solo cuando sea necesario** (afectan el tamaño del email)
7. **Personalizar el remitente** según el tipo de email

---

## 📚 Ver También

- [Django Email Documentation](https://docs.djangoproject.com/en/stable/topics/email/)
- [WeasyPrint for PDF Generation](https://doc.courtbouillon.org/weasyprint/)
- [Email Best Practices](https://www.emailonacid.com/blog/article/email-development/email-development-best-practices/)

