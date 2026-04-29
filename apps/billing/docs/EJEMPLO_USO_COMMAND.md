# Ejemplo de Uso: CreateInvoiceFromDictCommand

## Crear Factura usando el Command Pattern

Este es un ejemplo de cómo crear una factura usando el comando con los datos proporcionados.

### Código Python

```python
from decimal import Decimal
from apps.billing.application.commands import CreateInvoiceFromDictCommand
from apps.billing.application.use_cases import CreateInvoiceUseCase
from apps.billing.domain.interface.services import InvoiceDomainService
from apps.billing.infrastructure.repository import InvoiceRepository

# Crear el comando con los datos
command = CreateInvoiceFromDictCommand(
    student=123,
    advisor=456,
    payment_order=789,
    invoice_details=[
        {
            "payment_concept": 1,
            "description": "Registro administrativo LC mundo",
            "quantity": 1,
            "unit_price": 200.00,
            "discount": 0.00
        }
    ],
    status="E",  # E = Exonerada
    currency="USD",
    notes="Primera factura del estudiante"
)

# Configurar dependencias
domain_service = InvoiceDomainService()
repository = InvoiceRepository()
use_case = CreateInvoiceUseCase(domain_service, repository)

# Ejecutar caso de uso con el comando
try:
    invoice = use_case.execute_from_command(command)
    print(f"✅ Factura creada exitosamente")
    print(f"   Número: {invoice.invoice_number}")
    print(f"   Total: ${invoice.total}")
    print(f"   Estado: {invoice.get_status_display()}")
    print(f"   ID: {invoice.id}")
except Exception as e:
    print(f"❌ Error al crear factura: {e}")
```

### O usando diccionario directamente (método actual)

```python
from apps.billing.application.use_cases import CreateInvoiceUseCase
from apps.billing.domain.interface.services import InvoiceDomainService
from apps.billing.infrastructure.repository import InvoiceRepository

# Configurar dependencias
domain_service = InvoiceDomainService()
repository = InvoiceRepository()
use_case = CreateInvoiceUseCase(domain_service, repository)

# Datos como diccionario
data = {
    "student": 123,
    "advisor": 456,
    "payment_order": 789,
    "invoice_details": [
        {
            "payment_concept": 1,
            "description": "Registro administrativo LC mundo",
            "quantity": 1,
            "unit_price": 200.00,
            "discount": 0.00
        }
    ],
    "status": "E",
    "currency": "USD",
    "notes": "Primera factura del estudiante"
}

# Ejecutar
try:
    invoice = use_case.execute(data)
    print(f"✅ Factura creada: {invoice.invoice_number}")
except Exception as e:
    print(f"❌ Error: {e}")
```

## Ventajas del Command Pattern

1. **Validación en tiempo de compilación** - Los tipos están definidos
2. **Documentación automática** - Los comandos son autodocumentados
3. **Reutilización** - Los comandos pueden ser serializados/deserializados
4. **Testing más fácil** - Fácil crear comandos de prueba
5. **Versionado** - Diferentes versiones de comandos para compatibilidad

## JSON Request → Command

Para convertir un JSON request a un comando:

```python
import json
from decimal import Decimal
from apps.billing.application.commands import CreateInvoiceFromDictCommand

# JSON recibido del cliente
json_data = '''
{
    "student": 123,
    "advisor": 456,
    "payment_order": 789,
    "invoice_details": [
        {
            "payment_concept": 1,
            "description": "Registro administrativo LC mundo",
            "quantity": 1,
            "unit_price": 200.00,
            "discount": 0.00
        }
    ],
    "status": "E",
    "currency": "USD",
    "notes": "Primera factura del estudiante"
}
'''

# Parsear JSON
data = json.loads(json_data)

# Convertir a comando
command = CreateInvoiceFromDictCommand(
    student=data['student'],
    advisor=data['advisor'],
    payment_order=data['payment_order'],
    invoice_details=data['invoice_details'],
    status=data.get('status', 'I'),
    currency=data.get('currency', 'USD'),
    taxes=Decimal(str(data.get('taxes', 0.00))),
    notes=data.get('notes')
)

# Ejecutar
invoice = use_case.execute_from_command(command)
```

## Uso en una Vista de Django REST Framework

```python
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal

from apps.billing.application.commands import CreateInvoiceFromDictCommand
from apps.billing.application.use_cases import CreateInvoiceUseCase
from apps.billing.domain.interface.services import InvoiceDomainService
from apps.billing.infrastructure.repository import InvoiceRepository


@api_view(['POST'])
def create_invoice_view(request):
    """
    Endpoint para crear facturas.
    
    POST /api/v1/billing/invoices/
    Body: {
        "student": 123,
        "advisor": 456,
        "payment_order": 789,
        "invoice_details": [...],
        "status": "E",
        "currency": "USD",
        "notes": "..."
    }
    """
    try:
        # Crear comando desde request data
        command = CreateInvoiceFromDictCommand(
            student=request.data['student'],
            advisor=request.data['advisor'],
            payment_order=request.data['payment_order'],
            invoice_details=request.data['invoice_details'],
            status=request.data.get('status', 'I'),
            currency=request.data.get('currency', 'USD'),
            taxes=Decimal(str(request.data.get('taxes', 0.00))),
            notes=request.data.get('notes')
        )

        # Configurar caso de uso
        domain_service = InvoiceDomainService()
        repository = InvoiceRepository()
        use_case = CreateInvoiceUseCase(domain_service, repository)

        # Ejecutar
        invoice = use_case.execute_from_command(command)

        return Response({
            'success': True,
            'message': 'Factura creada exitosamente',
            'data': {
                'id': invoice.id,
                'invoice_number': invoice.invoice_number,
                'total': str(invoice.total),
                'balance_due': str(invoice.balance_due),
                'status': invoice.status,
                'status_display': invoice.get_status_display()
            }
        }, status=status.HTTP_201_CREATED)

    except KeyError as e:
        return Response({
            'success': False,
            'message': f'Campo requerido faltante: {e}'
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            'success': False,
            'message': 'Error al crear la factura',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

## Estados de Factura Disponibles

- **B** - Borrador
- **I** - Emitida (default)
- **PP** - Parcialmente pagada
- **P** - Pagada
- **A** - Anulada
- **PV** - Pendiente por Verificar
- **V** - Verificada
- **R** - Reembolsada
- **E** - Exonerada

## Notas Importantes

1. El comando `CreateInvoiceFromDictCommand` acepta `invoice_details` como lista de diccionarios
2. El campo `status` es opcional, por defecto es "I" (Emitida)
3. Si `status="E"`, la factura se crea como exonerada (sin necesidad de pago)
4. El campo `taxes` se convierte automáticamente a Decimal
5. El caso de uso validará todos los datos antes de crear la factura

