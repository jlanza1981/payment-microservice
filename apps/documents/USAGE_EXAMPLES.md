# Ejemplos de Uso - Documents App

## 🎯 Uso Básico

### 1. Generar PDF de Orden de Pago

```python
from apps.documents.application.generate_pdf import GeneratePDFUseCase
from apps.documents.infrastructure.pdf.weasyprint_pdf_generator import WeasyPrintPDFGenerator

# Configurar el generador
pdf_generator = WeasyPrintPDFGenerator()
use_case = GeneratePDFUseCase(pdf_generator=pdf_generator)

# Datos de la orden de pago
payment_data = {
    'order_number': 'OP-2026-001',
    'student_name': 'Juan Pérez',
    'student_email': 'juan@example.com',
    'date': '2026-03-04',
    'items': [
        {'description': 'Matrícula Curso Python', 'quantity': 1, 'price': 500.00},
        {'description': 'Material Didáctico', 'quantity': 1, 'price': 100.00}
    ],
    'subtotal': 600.00,
    'tax': 60.00,
    'total': 660.00
}

# Generar el PDF
try:
    pdf_content, relative_path = use_case.execute(
        data_structure=payment_data,
        template_name='payment_orders/pdf_order_payment.html',
        css_filename='pdf_order_payment.css',
        folder='payment_orders',
        document_type='payment_order'
    )
    
    # Guardar la ruta en el modelo
    payment_order.pdf_file_path = relative_path  # "payment_orders/payment_order_abc123.pdf"
    payment_order.save()
    
    print(f"✅ PDF generado: {relative_path}")
    print(f"✅ Tamaño: {len(pdf_content)} bytes")
    
except PDFGenerationError as e:
    print(f"❌ Error al generar PDF: {e}")
except PDFStorageError as e:
    print(f"❌ Error al guardar PDF: {e}")
```

### 2. Generar PDF de Factura

```python
# Datos de la factura
invoice_data = {
    'invoice_number': 'FAC-2026-001',
    'invoice_date': '2026-03-04',
    'student_name': 'María García',
    'student_email': 'maria@example.com',
    'student_dni': '12345678A',
    'items': [
        {'concept': 'Inscripción Evento', 'amount': 200.00},
        {'concept': 'Certificado', 'amount': 50.00}
    ],
    'subtotal': 250.00,
    'discount': 25.00,
    'tax': 22.50,
    'total': 247.50
}

# Generar PDF
pdf_content, relative_path = use_case.execute(
    data_structure=invoice_data,
    template_name='invoices/pdf_invoice.html',
    css_filename='pdf_invoice.css',
    folder='invoices',
    document_type='invoice'  # ✅ Ahora se llama "invoice_*.pdf"
)

# Guardar en el modelo
invoice.pdf_file_path = relative_path  # "invoices/invoice_def456.pdf"
invoice.save()
```

### 3. Generar PDF de Recibo

```python
# Datos del recibo
receipt_data = {
    'receipt_number': 'REC-2026-001',
    'payment_date': '2026-03-04',
    'student_name': 'Carlos López',
    'amount_paid': 500.00,
    'payment_method': 'Transferencia bancaria',
    'concept': 'Pago matrícula curso'
}

# Generar PDF
pdf_content, relative_path = use_case.execute(
    data_structure=receipt_data,
    template_name='receipts/payment_receipt.html',
    css_filename='payment_receipt.css',
    folder='receipts',
    document_type='receipt'  # ✅ Se llama "receipt_*.pdf"
)

# Guardar en el modelo
payment.receipt_path = relative_path  # "receipts/receipt_ghi789.pdf"
payment.save()
```

---

## 🔧 Uso Avanzado

### 4. Especificar Ruta de Salida Personalizada

```python
from pathlib import Path
from django.conf import settings

# Ruta personalizada
custom_path = Path(settings.MEDIA_ROOT) / 'invoices' / '2026' / '03' / 'invoice_custom.pdf'

# Generar con ruta personalizada
pdf_content, relative_path = use_case.execute(
    data_structure=invoice_data,
    template_name='invoices/pdf_invoice.html',
    css_filename='pdf_invoice.css',
    folder='invoices',
    document_type='invoice',
    output_path=str(custom_path)  # ✅ Ruta personalizada
)

# relative_path será: "invoices/2026/03/invoice_custom.pdf"
```

### 5. Usar Directamente el Generador (sin UseCase)

Si el UseCase no agrega valor en tu caso, puedes usar el generador directamente:

```python
from apps.documents.infrastructure.pdf.weasyprint_pdf_generator import WeasyPrintPDFGenerator

# Crear generador directamente
pdf_generator = WeasyPrintPDFGenerator()

# Generar PDF
pdf_content, relative_path = pdf_generator.generate_pdf(
    data_structure=payment_data,
    template_name='payment_orders/pdf_order_payment.html',
    css_filename='pdf_order_payment.css',
    folder='payment_orders',
    document_type='payment_order'
)
```

### 6. Manejo de Errores Específicos

```python
from apps.documents.infrastructure.pdf.weasyprint_pdf_generator import (
    PDFGenerationError,
    PDFStorageError
)

try:
    pdf_content, relative_path = use_case.execute(...)
    
except PDFGenerationError as e:
    # Error al generar el PDF (template, WeasyPrint, CSS, etc.)
    logger.error(f"Fallo en generación: {e}")
    # Notificar al usuario, reintentar, etc.
    
except PDFStorageError as e:
    # Error al guardar el archivo (permisos, espacio en disco, etc.)
    logger.error(f"Fallo en almacenamiento: {e}")
    # Notificar al administrador, verificar permisos, etc.
    
except Exception as e:
    # Cualquier otro error inesperado
    logger.error(f"Error inesperado: {e}")
```

---

## 🏗️ Integración con Modelos Django

### Ejemplo con Payment Model

```python
# models.py
from django.db import models

class Payment(models.Model):
    student = models.ForeignKey('profiles.Student', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    
    # 📄 Campo para guardar la ruta del PDF
    pdf_file_path = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        help_text='Ruta relativa del PDF en MEDIA_ROOT'
    )
    
    def generate_pdf(self):
        """Genera el PDF del pago"""
        from apps.documents.application.generate_pdf import GeneratePDFUseCase
        from apps.documents.infrastructure.pdf.weasyprint_pdf_generator import WeasyPrintPDFGenerator
        
        pdf_generator = WeasyPrintPDFGenerator()
        use_case = GeneratePDFUseCase(pdf_generator=pdf_generator)
        
        # Preparar datos
        payment_data = {
            'order_number': f'PAY-{self.id}',
            'student_name': self.student.full_name,
            'amount': str(self.amount),
            'date': self.payment_date.strftime('%Y-%m-%d'),
        }
        
        # Generar PDF
        pdf_content, relative_path = use_case.execute(
            data_structure=payment_data,
            template_name='payments/payment_receipt.html',
            css_filename='payment_receipt.css',
            folder='payments',
            document_type='payment'
        )
        
        # Guardar ruta
        self.pdf_file_path = relative_path
        self.save(update_fields=['pdf_file_path'])
        
        return relative_path
    
    def get_pdf_url(self):
        """Obtiene la URL del PDF"""
        if self.pdf_file_path:
            return f"{settings.MEDIA_URL}{self.pdf_file_path}"
        return None
    
    def get_pdf_full_path(self):
        """Obtiene la ruta completa del PDF en el sistema"""
        if self.pdf_file_path:
            return Path(settings.MEDIA_ROOT) / self.pdf_file_path
        return None
```

### Uso en una Vista o Endpoint

```python
# views.py
from django.http import FileResponse, Http404
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['POST'])
def generate_payment_pdf(request, payment_id):
    """Genera el PDF de un pago"""
    try:
        payment = Payment.objects.get(id=payment_id)
        relative_path = payment.generate_pdf()
        
        return Response({
            'success': True,
            'message': 'PDF generado exitosamente',
            'pdf_url': payment.get_pdf_url(),
            'pdf_path': relative_path
        })
        
    except Payment.DoesNotExist:
        return Response({'error': 'Pago no encontrado'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
def download_payment_pdf(request, payment_id):
    """Descarga el PDF de un pago"""
    try:
        payment = Payment.objects.get(id=payment_id)
        
        if not payment.pdf_file_path:
            raise Http404("PDF no generado")
        
        pdf_path = payment.get_pdf_full_path()
        
        if not pdf_path.exists():
            raise Http404("Archivo PDF no encontrado")
        
        return FileResponse(
            open(pdf_path, 'rb'),
            content_type='application/pdf',
            filename=pdf_path.name
        )
        
    except Payment.DoesNotExist:
        raise Http404("Pago no encontrado")
```

---

## 🧪 Testing

### Test Unitario del Generador

```python
# tests/test_pdf_generator.py
from unittest.mock import patch, MagicMock
from django.test import TestCase
from apps.documents.infrastructure.pdf.weasyprint_pdf_generator import (
    WeasyPrintPDFGenerator,
    PDFGenerationError
)

class TestWeasyPrintPDFGenerator(TestCase):
    
    def setUp(self):
        self.generator = WeasyPrintPDFGenerator()
        
    @patch('apps.documents.infrastructure.pdf.weasyprint_pdf_generator.render_to_string')
    @patch('apps.documents.infrastructure.pdf.weasyprint_pdf_generator.HTML')
    def test_generate_pdf_success(self, mock_html, mock_render):
        """Prueba generación exitosa de PDF"""
        # Mock del template
        mock_render.return_value = "<html><body>Test</body></html>"
        
        # Mock de WeasyPrint
        mock_html_obj = MagicMock()
        mock_html_obj.write_pdf.return_value = b'PDF_CONTENT'
        mock_html.return_value = mock_html_obj
        
        # Ejecutar
        pdf_content, relative_path = self.generator.generate_pdf(
            data_structure={'test': 'data'},
            template_name='test/template.html',
            css_filename='test.css',
            folder='test_folder',
            document_type='test'
        )
        
        # Verificar
        self.assertEqual(pdf_content, b'PDF_CONTENT')
        self.assertIn('test_folder/', relative_path)
        self.assertIn('test_', relative_path)
        self.assertTrue(relative_path.endswith('.pdf'))
```

---

## 📝 Notas Importantes

### ✅ Rutas Relativas vs Absolutas

El generador **siempre retorna rutas RELATIVAS** a `MEDIA_ROOT`:

```python
# ✅ CORRECTO - Ruta relativa (guardar en BD)
pdf_file_path = "payment_orders/payment_order_abc123.pdf"

# ❌ INCORRECTO - Ruta absoluta (no guardar en BD)
pdf_file_path = "/home/user/project/media/payment_orders/payment_order_abc123.pdf"
```

### 🎨 CSS Externo

Si usas CSS externo en los templates HTML, asegúrate de que sea accesible:

```html
<!-- ⚠️ Puede fallar si el sitio está caído -->
<link rel="stylesheet" href="https://www.lcmundo.com/static/css/styles.css"/>

<!-- ✅ Mejor: CSS inline o archivos locales -->
<style>
    body { font-family: Arial; }
</style>
```

### 📦 Dependencias

Asegúrate de tener WeasyPrint instalado:

```bash
pip install WeasyPrint
```

En algunos sistemas necesitas dependencias adicionales. Ver: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation

