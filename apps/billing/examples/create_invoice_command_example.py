"""
Script de ejemplo para crear una factura usando CreateInvoiceFromDictCommand.

Este script demuestra cómo crear una factura exonerada con los datos proporcionados.
"""

from decimal import Decimal

from django.db import transaction

from apps.billing.application.commands import CreateInvoiceFromDictCommand
from apps.billing.application.use_cases import CreateInvoiceUseCase
from apps.billing.domain.interface.services import InvoiceDomainService
from apps.billing.infrastructure.repository import InvoiceRepository


def create_invoice_example():
    """
    Crea una factura de ejemplo usando el comando.

    Datos de entrada:
    - Student ID: 123
    - Advisor ID: 456
    - Payment Order ID: 789
    - Detalle: Registro administrativo LC mundo ($200.00)
    - Status: E (Exonerada)
    - Currency: USD
    """

    print("=" * 60)
    print("CREANDO FACTURA CON COMMAND PATTERN")
    print("=" * 60)

    # 1. Crear el comando con los datos
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
        taxes=Decimal('0.00'),
        notes="Primera factura del estudiante"
    )

    print(f"\n📋 Comando creado:")
    print(f"   Student: {command.student}")
    print(f"   Advisor: {command.advisor}")
    print(f"   Payment Order: {command.payment_order}")
    print(f"   Status: {command.status}")
    print(f"   Currency: {command.currency}")
    print(f"   Detalles: {len(command.invoice_details)} línea(s)")

    # 2. Configurar las dependencias
    print(f"\n🔧 Configurando dependencias...")
    domain_service = InvoiceDomainService()
    repository = InvoiceRepository()
    use_case = CreateInvoiceUseCase(domain_service, repository)

    # 3. Ejecutar el caso de uso
    try:
        print(f"\n⚙️  Ejecutando caso de uso...")

        with transaction.atomic():
            invoice = use_case.execute_from_command(command)

        print(f"\n✅ ¡FACTURA CREADA EXITOSAMENTE!")
        print(f"   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"   ID: {invoice.id}")
        print(f"   Número: {invoice.invoice_number}")
        print(f"   Estado: {invoice.get_status_display()} ({invoice.status})")
        print(f"   Subtotal: ${invoice.subtotal}")
        print(f"   Impuestos: ${invoice.taxes}")
        print(f"   Total: ${invoice.total}")
        print(f"   Saldo Pendiente: ${invoice.balance_due}")
        print(f"   Moneda: {invoice.currency}")
        print(f"   Creada: {invoice.created_at}")

        if invoice.notes:
            print(f"   Notas: {invoice.notes}")

        print(f"\n📄 Detalles de la factura:")
        for idx, detail in enumerate(invoice.details.all(), 1):
            print(f"   {idx}. {detail.description}")
            print(f"      Concepto: {detail.concept.name}")
            print(f"      Cantidad: {detail.quantity}")
            print(f"      Precio Unitario: ${detail.unit_price}")
            print(f"      Descuento: ${detail.discount}")
            print(f"      Subtotal: ${detail.subtotal}")

        print(f"\n🔗 Relaciones:")
        print(f"   Estudiante: {invoice.user.get_full_name()} (ID: {invoice.user.id})")
        print(f"   Asesor: {invoice.advisor.get_full_name()} (ID: {invoice.advisor.id})")
        print(f"   Orden de Pago: {invoice.payment_order.order_number} (ID: {invoice.payment_order.id})")

        print(f"\n" + "=" * 60)

        return invoice

    except Exception as e:
        print(f"\n❌ ERROR AL CREAR LA FACTURA")
        print(f"   {type(e).__name__}: {e}")
        print(f"\n" + "=" * 60)
        raise


def create_invoice_from_dict():
    """
    Alternativa: Crear factura usando diccionario directamente.
    """

    print("=" * 60)
    print("CREANDO FACTURA CON DICCIONARIO (MÉTODO ALTERNATIVO)")
    print("=" * 60)

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
        "taxes": 0.00,
        "notes": "Primera factura del estudiante"
    }

    print(f"\n📋 Datos recibidos:")
    print(f"   Student: {data['student']}")
    print(f"   Advisor: {data['advisor']}")
    print(f"   Payment Order: {data['payment_order']}")

    # Configurar dependencias
    print(f"\n🔧 Configurando dependencias...")
    domain_service = InvoiceDomainService()
    repository = InvoiceRepository()
    use_case = CreateInvoiceUseCase(domain_service, repository)

    # Ejecutar
    try:
        print(f"\n⚙️  Ejecutando caso de uso...")
        invoice = use_case.execute(data)

        print(f"\n✅ ¡FACTURA CREADA EXITOSAMENTE!")
        print(f"   Número: {invoice.invoice_number}")
        print(f"   Total: ${invoice.total}")
        print(f"   Estado: {invoice.get_status_display()}")
        print(f"\n" + "=" * 60)

        return invoice

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(f"\n" + "=" * 60)
        raise


if __name__ == "__main__":
    # Puedes ejecutar cualquiera de los dos métodos:

    # Método 1: Usando Command Pattern (recomendado)
    invoice = create_invoice_example()

    # Método 2: Usando diccionario directo
    # invoice = create_invoice_from_dict()
