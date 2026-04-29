"""
Tests para el repositorio y caso de uso de facturas.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.billing.application.use_cases import CreateInvoiceUseCase
from apps.billing.domain.interface.services import InvoiceDomainService
from apps.billing.infrastructure.repository import InvoiceRepository
from apps.billing.models import Invoice
from apps.orden_pagos.models import PaymentOrder, PaymentConcept, PaymentCategory

User = get_user_model()


class CreateInvoiceUseCaseTest(TestCase):
    """Tests para el caso de uso CreateInvoice"""

    def setUp(self):
        """Configuración inicial para los tests"""
        # Crear usuarios de prueba
        self.student = User.objects.create_user(
            username='student_test',
            email='student@test.com',
            nombre='Juan',
            apellido='Pérez'
        )

        self.advisor = User.objects.create_user(
            username='advisor_test',
            email='advisor@test.com',
            nombre='María',
            apellido='González'
        )

        # Crear categoría de pago
        self.category = PaymentCategory.objects.create(
            name='Matrícula',
        )

        # Crear concepto de pago
        self.payment_concept = PaymentConcept.objects.create(
            name='Matrícula Curso',
            requires_program=False,
            category=self.category,
            description='Matrícula para cursos',
            base_price=Decimal('500.00')
        )

        # Crear orden de pago
        self.payment_order = PaymentOrder.objects.create(
            student=self.student,
            advisor=self.advisor,
            status='PENDING',
            total_order=Decimal('500.00')
        )

        # Instanciar dependencias
        self.domain_service = InvoiceDomainService()
        self.repository = InvoiceRepository()
        self.use_case = CreateInvoiceUseCase(
            domain_service=self.domain_service,
            repository=self.repository
        )

    def test_create_invoice_successfully(self):
        """Test: Crear factura exitosamente"""
        # Datos de la factura
        invoice_data = {
            'student': self.student.id,
            'advisor': self.advisor.id,
            'payment_order': self.payment_order.id,
            'invoice_details': [
                {
                    'payment_concept': self.payment_concept.id,
                    'description': 'Matrícula curso de inglés',
                    'quantity': 1,
                    'unit_price': Decimal('500.00'),
                    'discount': Decimal('0.00')
                }
            ],
            'currency': 'USD',
            'taxes': Decimal('0.00'),
            'notes': 'Factura de prueba'
        }

        # Ejecutar caso de uso
        invoice = self.use_case.execute(invoice_data)

        # Verificaciones
        self.assertIsNotNone(invoice)
        self.assertIsNotNone(invoice.invoice_number)
        self.assertEqual(invoice.user, self.student)
        self.assertEqual(invoice.advisor, self.advisor)
        self.assertEqual(invoice.payment_order, self.payment_order)
        self.assertEqual(invoice.status, 'I')  # Emitida
        self.assertEqual(invoice.currency, 'USD')
        self.assertEqual(invoice.subtotal, Decimal('500.00'))
        self.assertEqual(invoice.total, Decimal('500.00'))

        # Verificar detalles
        details = invoice.details.all()
        self.assertEqual(details.count(), 1)
        self.assertEqual(details.first().concept, self.payment_concept)

    def test_create_invoice_with_multiple_details(self):
        """Test: Crear factura con múltiples detalles"""
        # Crear segundo concepto
        concept2 = PaymentConcept.objects.create(
            name='Materiales',
            category=self.category,
            description='Materiales de estudio',
            base_price=Decimal('100.00')
        )

        invoice_data = {
            'student': self.student.id,
            'advisor': self.advisor.id,
            'payment_order': self.payment_order.id,
            'invoice_details': [
                {
                    'payment_concept': self.payment_concept.id,
                    'description': 'Matrícula',
                    'quantity': 1,
                    'unit_price': Decimal('500.00'),
                    'discount': Decimal('50.00')
                },
                {
                    'payment_concept': concept2.id,
                    'description': 'Materiales',
                    'quantity': 2,
                    'unit_price': Decimal('100.00'),
                    'discount': Decimal('0.00')
                }
            ]
        }

        invoice = self.use_case.execute(invoice_data)

        self.assertEqual(invoice.details.count(), 2)
        # Subtotal: (500 - 50) + (100 * 2) = 450 + 200 = 650
        self.assertEqual(invoice.subtotal, Decimal('650.00'))

    def test_create_invoice_without_details_fails(self):
        """Test: Crear factura sin detalles debe fallar"""
        invoice_data = {
            'student': self.student.id,
            'advisor': self.advisor.id,
            'payment_order': self.payment_order.id,
            'invoice_details': []
        }

        with self.assertRaises(Exception):
            self.use_case.execute(invoice_data)


class InvoiceRepositoryTest(TestCase):
    """Tests para el repositorio de facturas"""

    def setUp(self):
        """Configuración inicial"""
        self.repository = InvoiceRepository()

        # Crear datos de prueba
        self.student = User.objects.create_user(
            username='student_test',
            email='student@test.com',
            nombre='Test',
            apellido='Student'
        )

        self.advisor = User.objects.create_user(
            username='advisor_test',
            email='advisor@test.com',
            nombre='Test',
            apellido='Advisor'
        )

        self.category = PaymentCategory.objects.create(
            name='Test Category',
        )

        self.payment_concept = PaymentConcept.objects.create(
            name='Test Concept',
            requires_program=False,
            category=self.category,
            base_price=Decimal('100.00')
        )

        self.payment_order = PaymentOrder.objects.create(
            student=self.student,
            advisor=self.advisor,
            status='ACTIVE',
            total_order=Decimal('100.00')
        )

    def test_create_invoice_with_repository(self):
        """Test: Crear factura usando el repositorio"""
        invoice_data = {
            'user': self.student,
            'advisor': self.advisor,
            'payment_order': self.payment_order,
            'currency': 'USD',
            'taxes': Decimal('0.00')
        }

        invoice_details = [
            {
                'concept': self.payment_concept,
                'description': 'Test detail',
                'quantity': 1,
                'unit_price': Decimal('100.00'),
                'discount': Decimal('0.00')
            }
        ]

        invoice = self.repository.create(
            invoice_data=invoice_data,
            invoice_details=invoice_details
        )

        self.assertIsNotNone(invoice.id)
        self.assertIsNotNone(invoice.invoice_number)
        self.assertEqual(invoice.details.count(), 1)

    def test_get_invoices_by_student(self):
        """Test: Obtener facturas por estudiante"""
        # Crear factura
        invoice = Invoice.objects.create(
            user=self.student,
            advisor=self.advisor,
            payment_order=self.payment_order,
            status='I',
            total=Decimal('100.00')
        )

        # Obtener facturas
        invoices = self.repository.get_invoices_by_student(self.student.id)

        self.assertEqual(len(invoices), 1)
        self.assertEqual(invoices[0].id, invoice.id)

    def test_calculate_student_total_debt(self):
        """Test: Calcular deuda total de un estudiante"""
        # Crear facturas con saldo pendiente
        Invoice.objects.create(
            user=self.student,
            advisor=self.advisor,
            payment_order=self.payment_order,
            status='I',
            total=Decimal('100.00'),
            balance_due=Decimal('100.00')
        )

        Invoice.objects.create(
            user=self.student,
            advisor=self.advisor,
            payment_order=self.payment_order,
            status='PP',
            total=Decimal('200.00'),
            balance_due=Decimal('50.00')
        )

        # Calcular deuda
        total_debt = self.repository.calculate_student_total_debt(self.student.id)

        self.assertEqual(total_debt, Decimal('150.00'))
