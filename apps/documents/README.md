# Aplicación: Documents

## Descripción

Esta aplicación maneja la generación de documentos PDF del sistema, específicamente para facturas y órdenes de pago.

## Arquitectura Hexagonal

```
documents/
├── domain/             # Capa de Dominio (Lógica de Negocio Pura)
│   └── ports/         # Puertos/Interfaces
│       └── pdf_generator.py  # PDFGenerator (Interfaz)
│
├── application/        # Capa de Aplicación (Casos de Uso)
│   └── generate_pdf.py  # GeneratePaymentPDFUseCase
│
└── infrastructure/     # Capa de Infraestructura (Adaptadores)
    └── pdf/           # Adaptadores para generación de PDF
        ├── weasyprint_pdf_generator.py  # Implementación con WeasyPrint
        └── templates/  # Plantillas HTML para PDF
```

## Funcionalidad Principal

- **Generación de PDFs**: Facturas y órdenes de pago usando WeasyPrint

## Uso

### Generar un PDF de pago

```python
from apps.documents.application.generate_pdf import GeneratePDFUseCase
from apps.documents.infrastructure.pdf.weasyprint_pdf_generator import WeasyPrintPDFGenerator

# Configurar generador
pdf_generator = WeasyPrintPDFGenerator()

# Crear caso de uso
use_case = GeneratePDFUseCase(pdf_generator=pdf_generator)

# Datos de la orden de pago
payment_data = {
    'order_number': 'ORD-2026-001',
    'student_name': 'Juan Pérez',
    'student_email': 'juan@example.com',
    'items': [
        {'description': 'Matrícula', 'amount': 500.00},
        {'description': 'Material', 'amount': 100.00}
    ],
    'subtotal': 600.00,
    'tax': 60.00,
    'total': 660.00
}

# Ejecutar generación
pdf_content, relative_path = use_case.execute(
    data_structure=payment_data,
    template_name='payment_orders/pdf_order_payment.html',
    css_filename='pdf_order_payment.css',
    folder='payment_orders',
    document_type='payment_order'  # Tipo de documento para el nombre del archivo
)

# Guardar ruta relativa en el modelo
payment_order.pdf_file_path = relative_path  # "payment_orders/payment_order_abc123.pdf"
payment_order.save()

print(f"PDF generado: {relative_path}")
print(f"Tamaño: {len(pdf_content)} bytes")
```

**📖 Ver más ejemplos en [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)**

## Plantillas

Las plantillas HTML para PDFs se almacenan en:

```
templates/
├── payments/
│   └── payment_order_template.html
└── invoices/
    └── invoice_template.html
```

## Almacenamiento

Los PDFs generados se almacenan en la carpeta especificada dentro de `MEDIA_ROOT`:

```
media/
├── payment_orders/
│   └── invoice_*.pdf
└── invoices/
    └── invoice_*.pdf
```

## Extensibilidad

### Agregar un nuevo generador de PDF

1. Crear una clase en `infrastructure/pdf/` implementando `PDFGenerator`
2. Implementar el método `generate_payment_pdf`
3. Inyectar el nuevo generador en el caso de uso

## Dependencias

- **WeasyPrint**: Para generar PDFs desde HTML+CSS

## Instalación de WeasyPrint

```bash
pip install WeasyPrint
```

En algunos sistemas operativos, WeasyPrint requiere dependencias adicionales. Consultar la [documentación oficial](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation).

## Notas

- Esta aplicación está enfocada específicamente en la generación de PDFs de pago
- No incluye modelos de Django ni persistencia de documentos
- Funciona como una utilidad de generación de PDFs a partir de plantillas HTML

