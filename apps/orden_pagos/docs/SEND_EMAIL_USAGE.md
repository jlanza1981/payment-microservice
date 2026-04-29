# SendEmailUseCase - Caso de Uso para Envío de Correos

## Descripción

`SendEmailUseCase` es un caso de uso genérico y reutilizable para el envío de correos electrónicos con soporte para:

- Múltiples destinatarios
- Contenido HTML mediante plantillas Django
- Archivos adjuntos
- CC y BCC
- Logging automático de éxitos y errores

## Clases Principales

### EmailAttachment

Dataclass que representa un archivo adjunto para el correo.

**Atributos:**

- `filename` (str): Nombre del archivo
- `content` (bytes): Contenido del archivo en bytes
- `mimetype` (str): Tipo MIME del archivo (por defecto: 'application/octet-stream')

### EmailData

Dataclass que encapsula todos los datos necesarios para enviar un correo.

**Atributos obligatorios:**

- `subject` (str): Asunto del correo
- `recipients` (List[str]): Lista de destinatarios

**Atributos opcionales:**

- `template_name` (str): Nombre de la plantilla HTML a renderizar
- `template_context` (Dict[str, Any]): Contexto para la plantilla
- `body` (str): Cuerpo del correo (alternativa a template_name)
- `attachments` (List[EmailAttachment]): Lista de archivos adjuntos
- `from_email` (str): Email del remitente (por defecto usa settings.EMAIL_HOST_USER)
- `cc` (List[str]): Lista de destinatarios en copia
- `bcc` (List[str]): Lista de destinatarios en copia oculta

**Nota:** Debe proporcionar al menos `body` o `template_name`.

### SendEmailUseCase

Caso de uso principal para el envío de correos.

**Método principal:**

- `execute(email_data: EmailData) -> Dict[str, Any]`: Envía el correo y retorna el resultado

**Retorno:**

```python
{
    'success': bool,
    'message': str,
    'recipients': List[str],
    'subject': str,
    'error': str  # Solo si success es False
}
```

## Ejemplos de Uso

### Ejemplo 1: Correo Simple con Plantilla

```python
from apps.orden_pagos.application.use_cases import SendEmailUseCase, EmailData

# Crear instancia del caso de uso
email_sender = SendEmailUseCase()

# Preparar datos del correo
email_data = EmailData(
    subject='Bienvenido a nuestra plataforma',
    recipients=['estudiante@example.com'],
    template_name='email-welcome.html',
    template_context={
        'nombre': 'Juan',
        'apellido': 'Pérez'
    }
)

# Enviar correo
result = email_sender.execute(email_data)

if result['success']:
    print(f"Correo enviado a {result['recipients']}")
else:
    print(f"Error: {result['error']}")
```

### Ejemplo 2: Correo con Archivo Adjunto PDF

```python
from apps.orden_pagos.application.use_cases import (
    SendEmailUseCase,
    EmailData,
    EmailAttachment
)

# Leer el contenido del PDF
with open('documento.pdf', 'rb') as f:
    pdf_content = f.read()

# Crear adjunto
attachment = EmailAttachment(
    filename='documento.pdf',
    content=pdf_content,
    mimetype='application/pdf'
)

# Preparar datos del correo
email_data = EmailData(
    subject='Documento adjunto',
    recipients=['cliente@example.com'],
    template_name='email-documento.html',
    template_context={'mensaje': 'Adjunto encontrarás el documento solicitado'},
    attachments=[attachment]
)

# Enviar correo
email_sender = SendEmailUseCase()
result = email_sender.execute(email_data)
```

### Ejemplo 3: Correo con Múltiples Destinatarios y CC

```python
from apps.orden_pagos.application.use_cases import SendEmailUseCase, EmailData

email_data = EmailData(
    subject='Notificación importante',
    recipients=['estudiante@example.com', 'tutor@example.com'],
    cc=['admin@example.com'],
    bcc=['registro@example.com'],
    template_name='email-notificacion.html',
    template_context={
        'titulo': 'Actualización del sistema',
        'mensaje': 'Se ha actualizado el sistema...'
    }
)

email_sender = SendEmailUseCase()
result = email_sender.execute(email_data)
```

### Ejemplo 4: Correo con Body HTML Directo (sin plantilla)

```python
from apps.orden_pagos.application.use_cases import SendEmailUseCase, EmailData

html_body = """
<html>
    <body>
        <h1>Hola Mundo</h1>
        <p>Este es un correo de prueba.</p>
    </body>
</html>
"""

email_data = EmailData(
    subject='Correo de prueba',
    recipients=['test@example.com'],
    body=html_body
)

email_sender = SendEmailUseCase()
result = email_sender.execute(email_data)
```

### Ejemplo 5: Uso en Otro Caso de Uso (Composición)

```python
from apps.orden_pagos.application.use_cases import SendEmailUseCase, EmailData, EmailAttachment


class SendInvoiceUseCase:
    """Caso de uso para enviar facturas por correo."""

    def __init__(self, email_sender=None):
        self.email_sender = email_sender or SendEmailUseCase()

    def execute(self, invoice_id: int):
        # Obtener factura
        invoice = self.get_invoice(invoice_id)

        # Generar PDF
        pdf_content = self.generate_pdf(invoice)

        # Crear adjunto
        attachment = EmailAttachment(
            filename=f'factura_{invoice.number}.pdf',
            content=pdf_content,
            mimetype='application/pdf'
        )

        # Preparar correo
        email_data = EmailData(
            subject=f'Factura N° {invoice.number}',
            recipients=[invoice.customer.email],
            template_name='email-invoice.html',
            template_context={'invoice': invoice},
            attachments=[attachment]
        )

        # Enviar usando el caso de uso
        result = self.email_sender.execute(email_data)

        return result
```

## Validaciones Automáticas

El caso de uso valida automáticamente:

1. Que haya al menos un destinatario
2. Que el asunto no esté vacío
3. Que los emails tengan formato básico válido (contienen @)
4. Que se proporcione `body` o `template_name`

## Logging

El caso de uso registra automáticamente:

- **Info**: Cuando el correo se envía exitosamente
- **Error**: Cuando ocurre un error al enviar el correo
- **Debug**: Cuando se agregan archivos adjuntos

## Manejo de Errores

Todos los errores son capturados y devueltos en el resultado, no se propagan excepciones (excepto `ValidationError` para
datos inválidos).

```python
result = email_sender.execute(email_data)

if not result['success']:
    # Manejar error
    logger.error(f"Error al enviar correo: {result['error']}")
    # Notificar al usuario, reintentar, etc.
```

## Testing

Para pruebas unitarias, puedes mockear el caso de uso:

```python
from unittest.mock import Mock

# Crear mock
mock_email_sender = Mock()
mock_email_sender.execute.return_value = {
    'success': True,
    'message': 'Correo enviado exitosamente',
    'recipients': ['test@example.com'],
    'subject': 'Test'
}

# Usar en tu caso de uso
use_case = MiCasoDeUso(email_sender=mock_email_sender)
result = use_case.execute()

# Verificar que se llamó
mock_email_sender.execute.assert_called_once()
```

## Configuración Requerida

Asegúrate de tener configurado en `settings.py`:

```python
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu_email@gmail.com'
EMAIL_HOST_PASSWORD = 'tu_contraseña'
```

## Ventajas de Este Enfoque

1. **Reutilizable**: Un solo lugar para la lógica de envío de correos
2. **Testeable**: Fácil de mockear para pruebas
3. **Mantenible**: Cambios en la lógica de correo solo en un lugar
4. **Logging centralizado**: Todos los correos se registran de forma consistente
5. **Validación automática**: Previene errores comunes
6. **Flexible**: Soporta múltiples casos de uso

