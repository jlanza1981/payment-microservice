"""
Tests Completos: CreatePaymentUseCase

Suite de tests para validar los dos flujos principales de pago:
1. Flujo Exonerado
2. Flujo Pago Anticipado

Author: Sistema LC Mundo
Date: 2026-01-12
"""

from decimal import Decimal

from django.test import TestCase

from apps.administrador.models import Usuarios
from apps.billing.models import Invoice, InvoiceDetail
from apps.orden_pagos.models import PaymentOrder, PaymentConcept
from apps.pagos.application.use_cases.create_payment_exonerated import CreatePaymentUseCase
from apps.pagos.infrastructure.repository.payment_repository import PaymentRepository
from apps.pagos.models import Payment, PaymentAllocation


class CreatePaymentUseCaseTest(TestCase):
    """
    Suite de tests para CreatePaymentUseCase.

    Tests incluidos:
    1. test_create_exonerated_payment_success
    2. test_create_advance_payment_without_invoice
    3. test_associate_invoice_to_advance_payment
    4. test_validation_missing_required_fields
    5. test_validation_invalid_amount
    6. test_validation_invalid_payment_method
    7. test_cannot_associate_invoice_twice
    """

    def setUp(self):
        """
        Configuración inicial para cada test.
        Crea datos de prueba: usuarios, conceptos, etc.
        """
        # Crear usuarios de prueba
        self.student = Usuarios.objects.create(
            nombre='Juan',
            apellido='Pérez',
            correo='juan.perez@test.com',
            tipo_usuario='student'
        )

        self.advisor = Usuarios.objects.create(
            nombre='María',
            apellido='García',
            correo='maria.garcia@test.com',
            tipo_usuario='advisor'
        )

        # Crear concepto de pago
        self.concept_matricula = PaymentConcept.objects.create(
            name='Matrícula',
            description='Matrícula del curso',
            unit_price=Decimal('1500.00'),
            currency='USD'
        )

        # Inicializar caso de uso
        self.repository = PaymentRepository()
        self.use_case = CreatePaymentUseCase(self.repository)

    def tearDown(self):
        """Limpieza después de cada test."""
        Payment.objects.all().delete()
        PaymentAllocation.objects.all().delete()
        Invoice.objects.all().delete()
        PaymentOrder.objects.all().delete()
        Usuarios.objects.all().delete()
        PaymentConcept.objects.all().delete()

    # ========================================================================
    # TEST 1: PAGO EXONERADO
    # ========================================================================

    def test_create_exonerated_payment_success(self):
        """
        Test: Crear pago exonerado con factura.

        Valida:
        - Pago se crea correctamente
        - payment_method = 'EX'
        - status = 'V' (Verificado automáticamente)
        - verification_date se establece
        - Factura se actualiza (balance_due)
        """
        # Arrange: Crear orden y factura
        order = PaymentOrder.objects.create(
            student=self.student,
            advisor=self.advisor,
            status='EXONERATED',
            total_order=Decimal('1500.00')
        )

        invoice = Invoice.objects.create(
            user=self.student,
            advisor=self.advisor,
            payment_order=order,
            status='E',
            subtotal=Decimal('1500.00'),
            total=Decimal('1500.00'),
            balance_due=Decimal('1500.00'),
            currency='USD'
        )

        # Act: Crear pago exonerado
        payment = self.use_case.create_exonerated_payment(
            invoice=invoice,
            user=self.student,
            advisor=self.advisor,
            amount=Decimal('1500.00'),
            currency='USD'
        )

        # Assert: Validar pago
        self.assertIsNotNone(payment)
        self.assertIsNotNone(payment.payment_number)
        self.assertEqual(payment.payment_method, 'EX')
        self.assertEqual(payment.status, 'V')
        self.assertEqual(payment.amount, Decimal('1500.00'))
        self.assertEqual(payment.user, self.student)
        self.assertEqual(payment.advisor, self.advisor)
        self.assertEqual(payment.invoice, invoice)
        self.assertIsNotNone(payment.verification_date)

        # Assert: Validar actualización de factura
        invoice.refresh_from_db()
        self.assertEqual(invoice.balance_due, Decimal('0.00'))

    # ========================================================================
    # TEST 2: PAGO ANTICIPADO SIN FACTURA
    # ========================================================================

    def test_create_advance_payment_without_invoice(self):
        """
        Test: Crear pago anticipado SIN factura.

        Valida:
        - Pago se crea sin factura (invoice=None)
        - payment_reference_number se guarda
        - status = 'D' (Disponible)
        - Datos de pago correctos
        """
        # Act: Crear pago anticipado sin factura
        payment = self.use_case.create_advance_payment(
            user=self.student,
            advisor=self.advisor,
            amount=Decimal('500.00'),
            payment_method='PP',
            payment_reference_number='PAYPAL-TXN-123456',
            currency='USD',
            status='D'
        )

        # Assert: Validar pago
        self.assertIsNotNone(payment)
        self.assertIsNotNone(payment.payment_number)
        self.assertIsNone(payment.invoice)  # SIN FACTURA
        self.assertEqual(payment.payment_method, 'PP')
        self.assertEqual(payment.status, 'D')
        self.assertEqual(payment.amount, Decimal('500.00'))
        self.assertEqual(payment.payment_reference_number, 'PAYPAL-TXN-123456')
        self.assertEqual(payment.user, self.student)
        self.assertEqual(payment.advisor, self.advisor)

    # ========================================================================
    # TEST 3: ASOCIAR FACTURA A PAGO ANTICIPADO
    # ========================================================================

    def test_associate_invoice_to_advance_payment(self):
        """
        Test: Asociar factura a un pago anticipado existente.

        Valida:
        - Pago se actualiza con factura
        - Allocations se crean correctamente
        - Balance de factura se actualiza
        """
        # Arrange: Crear pago anticipado
        payment = self.use_case.create_advance_payment(
            user=self.student,
            advisor=self.advisor,
            amount=Decimal('500.00'),
            payment_method='PP',
            payment_reference_number='PAYPAL-123',
            currency='USD',
            status='D'
        )

        # Crear orden y factura
        order = PaymentOrder.objects.create(
            student=self.student,
            advisor=self.advisor,
            status='ACTIVE',
            total_order=Decimal('500.00')
        )

        invoice = Invoice.objects.create(
            user=self.student,
            advisor=self.advisor,
            payment_order=order,
            status='I',
            subtotal=Decimal('500.00'),
            total=Decimal('500.00'),
            balance_due=Decimal('500.00'),
            currency='USD'
        )

        invoice_detail = InvoiceDetail.objects.create(
            invoice=invoice,
            payment_concept=self.concept_matricula,
            description='Matrícula',
            quantity=1,
            unit_price=Decimal('500.00')
        )

        # Act: Asociar factura al pago
        allocations = [
            {
                'invoice_detail_id': invoice_detail.id,
                'payment_concept_id': self.concept_matricula.id,
                'amount_applied': Decimal('500.00'),
                'status': 'PAID'
            }
        ]

        updated_payment = self.use_case.associate_invoice_to_payment(
            payment_id=payment.id,
            invoice_id=invoice.id,
            allocations=allocations
        )

        # Assert: Validar pago actualizado
        self.assertIsNotNone(updated_payment.invoice)
        self.assertEqual(updated_payment.invoice.id, invoice.id)

        # Assert: Validar allocations
        allocations_count = updated_payment.allocations.count()
        self.assertEqual(allocations_count, 1)

        allocation = updated_payment.allocations.first()
        self.assertEqual(allocation.amount_applied, Decimal('500.00'))
        self.assertEqual(allocation.invoice_detail, invoice_detail)

        # Assert: Validar balance de factura
        invoice.refresh_from_db()
        self.assertEqual(invoice.balance_due, Decimal('0.00'))

    # ========================================================================
    # TEST 4: VALIDACIÓN - CAMPOS REQUERIDOS
    # ========================================================================

    def test_validation_missing_required_fields(self):
        """
        Test: Validar que se requieren campos obligatorios.

        Valida:
        - ValueError si falta 'user'
        - ValueError si falta 'amount'
        - ValueError si falta 'payment_method'
        - ValueError si falta 'currency'
        """
        # Test: Falta user
        with self.assertRaises(ValueError) as context:
            self.use_case.execute({
                'amount': Decimal('100.00'),
                'payment_method': 'PP',
                'currency': 'USD'
            })
        self.assertIn('user', str(context.exception).lower())

        # Test: Falta amount
        with self.assertRaises(ValueError) as context:
            self.use_case.execute({
                'user': self.student,
                'payment_method': 'PP',
                'currency': 'USD'
            })
        self.assertIn('amount', str(context.exception).lower())

        # Test: Falta payment_method
        with self.assertRaises(ValueError) as context:
            self.use_case.execute({
                'user': self.student,
                'amount': Decimal('100.00'),
                'currency': 'USD'
            })
        self.assertIn('payment_method', str(context.exception).lower())

        # Test: Falta currency
        with self.assertRaises(ValueError) as context:
            self.use_case.execute({
                'user': self.student,
                'amount': Decimal('100.00'),
                'payment_method': 'PP'
            })
        self.assertIn('currency', str(context.exception).lower())

    # ========================================================================
    # TEST 5: VALIDACIÓN - MONTO INVÁLIDO
    # ========================================================================

    def test_validation_invalid_amount(self):
        """
        Test: Validar que el monto debe ser > 0.

        Valida:
        - ValueError si amount <= 0
        - ValueError si amount no es numérico
        """
        # Test: Monto = 0
        with self.assertRaises(ValueError) as context:
            self.use_case.execute({
                'user': self.student,
                'amount': Decimal('0'),
                'payment_method': 'PP',
                'currency': 'USD'
            })
        self.assertIn('mayor a 0', str(context.exception).lower())

        # Test: Monto negativo
        with self.assertRaises(ValueError) as context:
            self.use_case.execute({
                'user': self.student,
                'amount': Decimal('-100'),
                'payment_method': 'PP',
                'currency': 'USD'
            })
        self.assertIn('mayor a 0', str(context.exception).lower())

        # Test: Monto no numérico
        with self.assertRaises(ValueError) as context:
            self.use_case.execute({
                'user': self.student,
                'amount': 'invalid',
                'payment_method': 'PP',
                'currency': 'USD'
            })
        self.assertIn('número válido', str(context.exception).lower())

    # ========================================================================
    # TEST 6: VALIDACIÓN - MÉTODO DE PAGO INVÁLIDO
    # ========================================================================

    def test_validation_invalid_payment_method(self):
        """
        Test: Validar que el método de pago debe ser válido.

        Valida:
        - ValueError si payment_method no está en la lista permitida
        """
        with self.assertRaises(ValueError) as context:
            self.use_case.execute({
                'user': self.student,
                'amount': Decimal('100.00'),
                'payment_method': 'BITCOIN',  # No válido
                'currency': 'USD'
            })
        self.assertIn('método de pago inválido', str(context.exception).lower())

    # ========================================================================
    # TEST 7: NO SE PUEDE ASOCIAR FACTURA DOS VECES
    # ========================================================================

    def test_cannot_associate_invoice_twice(self):
        """
        Test: No se puede asociar factura a un pago que ya tiene factura.

        Valida:
        - ValueError si el pago ya tiene factura asociada
        """
        # Arrange: Crear pago con factura
        order = PaymentOrder.objects.create(
            student=self.student,
            advisor=self.advisor,
            status='ACTIVE',
            total_order=Decimal('500.00')
        )

        invoice1 = Invoice.objects.create(
            user=self.student,
            advisor=self.advisor,
            payment_order=order,
            status='I',
            subtotal=Decimal('500.00'),
            total=Decimal('500.00'),
            balance_due=Decimal('500.00'),
            currency='USD'
        )

        payment = self.use_case.execute({
            'invoice': invoice1,
            'user': self.student,
            'advisor': self.advisor,
            'amount': Decimal('500.00'),
            'payment_method': 'PP',
            'currency': 'USD'
        })

        # Crear segunda factura
        invoice2 = Invoice.objects.create(
            user=self.student,
            advisor=self.advisor,
            payment_order=order,
            status='I',
            subtotal=Decimal('500.00'),
            total=Decimal('500.00'),
            balance_due=Decimal('500.00'),
            currency='USD'
        )

        # Act & Assert: Intentar asociar segunda factura
        with self.assertRaises(ValueError) as context:
            self.use_case.associate_invoice_to_payment(
                payment_id=payment.id,
                invoice_id=invoice2.id
            )
        self.assertIn('ya tiene factura asociada', str(context.exception).lower())


# ============================================================================
# TESTS DE INTEGRACIÓN
# ============================================================================

class CreatePaymentIntegrationTest(TestCase):
    """
    Tests de integración para flujos completos.
    """

    def setUp(self):
        """Configuración inicial."""
        self.student = Usuarios.objects.create(
            nombre='Test',
            apellido='Student',
            correo='test@test.com',
            tipo_usuario='student'
        )

        self.advisor = Usuarios.objects.create(
            nombre='Test',
            apellido='Advisor',
            correo='advisor@test.com',
            tipo_usuario='advisor'
        )

        self.concept = PaymentConcept.objects.create(
            name='Test Concept',
            unit_price=Decimal('100.00')
        )

        self.use_case = CreatePaymentUseCase(PaymentRepository())

    def test_complete_exonerated_flow(self):
        """
        Test: Flujo completo de pago exonerado.

        Orden → Factura → Pago Exonerado
        """
        # 1. Crear orden
        order = PaymentOrder.objects.create(
            student=self.student,
            advisor=self.advisor,
            status='EXONERATED',
            total_order=Decimal('1000.00')
        )

        # 2. Crear factura
        invoice = Invoice.objects.create(
            user=self.student,
            advisor=self.advisor,
            payment_order=order,
            status='E',
            total=Decimal('1000.00'),
            balance_due=Decimal('1000.00'),
            currency='USD'
        )

        # 3. Crear pago exonerado
        payment = self.use_case.create_exonerated_payment(
            invoice=invoice,
            user=self.student,
            advisor=self.advisor,
            amount=Decimal('1000.00')
        )

        # Validar resultado completo
        self.assertEqual(payment.status, 'V')
        self.assertEqual(payment.payment_method, 'EX')

        invoice.refresh_from_db()
        self.assertEqual(invoice.balance_due, Decimal('0.00'))

    def test_complete_advance_payment_flow(self):
        """
        Test: Flujo completo de pago anticipado.

        Pago → Factura → Asociación
        """
        # 1. Pago anticipado
        payment = self.use_case.create_advance_payment(
            user=self.student,
            advisor=self.advisor,
            amount=Decimal('500.00'),
            payment_method='PP',
            payment_reference_number='TEST-123'
        )

        self.assertIsNone(payment.invoice)

        # 2. Crear orden y factura
        order = PaymentOrder.objects.create(
            student=self.student,
            advisor=self.advisor,
            status='ACTIVE',
            total_order=Decimal('500.00')
        )

        invoice = Invoice.objects.create(
            user=self.student,
            advisor=self.advisor,
            payment_order=order,
            status='I',
            total=Decimal('500.00'),
            balance_due=Decimal('500.00'),
            currency='USD'
        )

        invoice_detail = InvoiceDetail.objects.create(
            invoice=invoice,
            payment_concept=self.concept,
            quantity=1,
            unit_price=Decimal('500.00')
        )

        # 3. Asociar factura
        updated_payment = self.use_case.associate_invoice_to_payment(
            payment_id=payment.id,
            invoice_id=invoice.id,
            allocations=[
                {
                    'invoice_detail_id': invoice_detail.id,
                    'payment_concept_id': self.concept.id,
                    'amount_applied': Decimal('500.00'),
                    'status': 'PAID'
                }
            ]
        )

        # Validar resultado completo
        self.assertIsNotNone(updated_payment.invoice)
        self.assertEqual(updated_payment.invoice.id, invoice.id)

        invoice.refresh_from_db()
        self.assertEqual(invoice.balance_due, Decimal('0.00'))


# ============================================================================
# EJECUTAR TESTS
# ============================================================================

"""
Para ejecutar estos tests:

# Todos los tests
python manage.py test apps.pagos.tests.test_create_payment_flows

# Test específico
python manage.py test apps.pagos.tests.test_create_payment_flows.CreatePaymentUseCaseTest.test_create_exonerated_payment_success

# Con verbose
python manage.py test apps.pagos.tests.test_create_payment_flows -v 2

# Con coverage
coverage run --source='apps.pagos' manage.py test apps.pagos.tests.test_create_payment_flows
coverage report
"""
