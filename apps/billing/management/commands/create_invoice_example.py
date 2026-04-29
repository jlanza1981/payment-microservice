"""
Django management command para crear una factura de ejemplo.

Uso:
    python manage.py create_invoice_example

Con datos personalizados:
    python manage.py create_invoice_example --student 123 --advisor 456 --order 789
"""

from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.billing.application.commands import CreateInvoiceFromDictCommand
from apps.billing.application.use_cases import CreateInvoiceUseCase
from apps.billing.domain.interface.services import InvoiceDomainService
from apps.billing.infrastructure.repository import InvoiceRepository


class Command(BaseCommand):
    help = 'Crea una factura de ejemplo usando el Command Pattern'

    def add_arguments(self, parser):
        parser.add_argument(
            '--student',
            type=int,
            default=123,
            help='ID del estudiante (default: 123)'
        )
        parser.add_argument(
            '--advisor',
            type=int,
            default=456,
            help='ID del asesor (default: 456)'
        )
        parser.add_argument(
            '--order',
            type=int,
            default=789,
            help='ID de la orden de pago (default: 789)'
        )
        parser.add_argument(
            '--status',
            type=str,
            default='E',
            choices=['B', 'I', 'E', 'PP', 'P', 'A', 'PV', 'V', 'R'],
            help='Estado de la factura (default: E - Exonerada)'
        )
        parser.add_argument(
            '--concept',
            type=int,
            default=1,
            help='ID del concepto de pago (default: 1)'
        )

    def handle(self, *args, **options):
        student_id = options['student']
        advisor_id = options['advisor']
        order_id = options['order']
        status = options['status']
        concept_id = options['concept']

        self.stdout.write("=" * 70)
        self.stdout.write(self.style.HTTP_INFO(" CREAR FACTURA CON COMMAND PATTERN "))
        self.stdout.write("=" * 70)
        self.stdout.write("")

        # Crear el comando
        command = CreateInvoiceFromDictCommand(
            student=student_id,
            advisor=advisor_id,
            payment_order=order_id,
            invoice_details=[
                {
                    "payment_concept": concept_id,
                    "description": "Registro administrativo LC mundo",
                    "quantity": 1,
                    "unit_price": 200.00,
                    "discount": 0.00
                }
            ],
            status=status,
            currency="USD",
            taxes=Decimal('0.00'),
            notes="Primera factura del estudiante - Creada desde management command"
        )

        self.stdout.write(f"📋 Datos del comando:")
        self.stdout.write(f"   • Student ID: {command.student}")
        self.stdout.write(f"   • Advisor ID: {command.advisor}")
        self.stdout.write(f"   • Payment Order ID: {command.payment_order}")
        self.stdout.write(f"   • Status: {command.status}")
        self.stdout.write(f"   • Currency: {command.currency}")
        self.stdout.write(f"   • Detalles: {len(command.invoice_details)} línea(s)")
        self.stdout.write("")

        # Configurar dependencias
        self.stdout.write("🔧 Configurando dependencias...")
        domain_service = InvoiceDomainService()
        repository = InvoiceRepository()
        use_case = CreateInvoiceUseCase(domain_service, repository)

        # Ejecutar el caso de uso
        try:
            self.stdout.write("⚙️  Ejecutando caso de uso...")
            self.stdout.write("")

            with transaction.atomic():
                invoice = use_case.execute_from_command(command)

            # Mostrar resultado
            self.stdout.write(self.style.SUCCESS("✅ ¡FACTURA CREADA EXITOSAMENTE!"))
            self.stdout.write("━" * 70)
            self.stdout.write(f"   ID: {invoice.id}")
            self.stdout.write(f"   Número: {invoice.invoice_number}")
            self.stdout.write(f"   Estado: {invoice.get_status_display()} ({invoice.status})")
            self.stdout.write(f"   Subtotal: ${invoice.subtotal}")
            self.stdout.write(f"   Impuestos: ${invoice.taxes}")
            self.stdout.write(self.style.SUCCESS(f"   Total: ${invoice.total}"))
            self.stdout.write(f"   Saldo Pendiente: ${invoice.balance_due}")
            self.stdout.write(f"   Moneda: {invoice.currency}")
            self.stdout.write(f"   Creada: {invoice.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

            if invoice.notes:
                self.stdout.write(f"   Notas: {invoice.notes}")

            self.stdout.write("")
            self.stdout.write("📄 Detalles de la factura:")
            for idx, detail in enumerate(invoice.details.all(), 1):
                self.stdout.write(f"   {idx}. {detail.description}")
                self.stdout.write(f"      • Concepto: {detail.concept.name}")
                self.stdout.write(f"      • Cantidad: {detail.quantity}")
                self.stdout.write(f"      • Precio Unitario: ${detail.unit_price}")
                self.stdout.write(f"      • Descuento: ${detail.discount}")
                self.stdout.write(f"      • Subtotal: ${detail.subtotal}")

            self.stdout.write("")
            self.stdout.write("🔗 Relaciones:")
            self.stdout.write(f"   • Estudiante: {invoice.user.get_full_name()} (ID: {invoice.user.id})")
            self.stdout.write(f"   • Asesor: {invoice.advisor.get_full_name()} (ID: {invoice.advisor.id})")
            self.stdout.write(f"   • Orden de Pago: {invoice.payment_order.order_number}")

            self.stdout.write("")
            self.stdout.write("=" * 70)

        except Exception as e:
            self.stdout.write("")
            self.stdout.write(self.style.ERROR("❌ ERROR AL CREAR LA FACTURA"))
            self.stdout.write(self.style.ERROR(f"   {type(e).__name__}: {e}"))
            self.stdout.write("")
            self.stdout.write("=" * 70)
            raise CommandError(f"No se pudo crear la factura: {e}")
