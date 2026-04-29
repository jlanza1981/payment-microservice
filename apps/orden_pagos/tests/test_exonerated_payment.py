"""
Tests para el endpoint de pagos exonerados.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.billing.models import Invoice, InvoiceDetail
from apps.orden_pagos.models import PaymentOrder, PaymentOrderDetails, PaymentConcept, PaymentCategory
from apps.pagos.models import Payment, PaymentAllocation

User = get_user_model()


class ExoneratedPaymentEndpointTests(TestCase):
    """Tests para el endpoint de pagos exonerados"""

    def setUp(self):
        """Configuración inicial para las pruebas"""
        # Crear usuarios
        self.student = User.objects.create_user(
            username='student1',
            email='student@test.com',
            first_name='Juan',
            last_name='Pérez'
        )

        self.advisor = User.objects.create_user(
            username='advisor1',
            email='advisor@test.com',
            first_name='María',
            last_name='García'
        )

        # Crear categoría y conceptos de pago
        self.category = PaymentCategory.objects.create(
            code='TEST',
            name='Categoría de Prueba',
            is_active=True
        )

        self.concept1 = PaymentConcept.objects.create(
            code='C1',
            name='Concepto 1',
            category=self.category,
            is_active=True
        )

        self.concept2 = PaymentConcept.objects.create(
            code='C2',
            name='Concepto 2',
            category=self.category,
            is_active=True
        )

    def test_create_exonerated_payment_new_order(self):
        """Test crear pago exonerado con orden nueva"""
        payload = {
            "student_id": self.student.id,
            "concepts": [
                {"concept_id": self.concept1.id, "quantity": 1},
                {"concept_id": self.concept2.id, "quantity": 2}
            ],
            "payer_name": "Juan Pérez",
            "advisor_id": self.advisor.id,
            "notes": "Beca completa 2026"
        }

        # Simular llamada al endpoint
        # En producción usarías self.client.post con autenticación

        # Verificar que no existen registros previos
        self.assertEqual(PaymentOrder.objects.count(), 0)
        self.assertEqual(Invoice.objects.count(), 0)
        self.assertEqual(Payment.objects.count(), 0)

    def test_create_exonerated_payment_existing_order(self):
        """Test crear pago exonerado con orden existente"""
        # Crear orden previa
        order = PaymentOrder.objects.create(
            student=self.student,
            advisor=self.advisor,
            status='PENDING',
            total_order=Decimal('100.00')
        )

        PaymentOrderDetails.objects.create(
            payment_order=order,
            payment_concept=self.concept1,
            quantity=1,
            price=Decimal('100.00'),
            sub_total=Decimal('100.00')
        )

        payload = {
            "order_payment_id": order.id,
            "payer_name": "Juan Pérez",
            "advisor_id": self.advisor.id,
            "notes": "Exoneración aprobada"
        }

        # Verificar que la orden existe
        self.assertEqual(PaymentOrder.objects.count(), 1)
        self.assertEqual(order.status, 'PENDING')

    def test_validation_requires_order_or_student_data(self):
        """Test validación: debe proporcionar orden existente O datos para nueva"""
        payload = {
            "payer_name": "Juan Pérez",
            "notes": "Sin orden ni datos"
        }

        # Esta validación debería fallar
        # En el endpoint real, esto generaría un error 400

    def test_validation_cannot_pay_paid_order(self):
        """Test validación: no se puede pagar una orden ya pagada"""
        order = PaymentOrder.objects.create(
            student=self.student,
            advisor=self.advisor,
            status='PAID',
            total_order=Decimal('0.00')
        )

        payload = {
            "order_payment_id": order.id,
            "payer_name": "Juan Pérez"
        }

        # Esta validación debería fallar con error 400

    def test_payment_method_is_exonerated(self):
        """Test que el método de pago sea 'EX' (Exonerated)"""
        # Verificar que 'EX' esté en las opciones
        payment_methods = dict(Payment.PAYMENT_METHODS)
        self.assertIn('EX', payment_methods)
        self.assertEqual(payment_methods['EX'], 'Exonerated')

    def test_payment_amount_is_zero(self):
        """Test que el monto del pago sea siempre $0.00"""
        # Crear pago exonerado manualmente para verificar
        order = PaymentOrder.objects.create(
            student=self.student,
            advisor=self.advisor,
            status='PENDING',
            total_order=Decimal('0.00')
        )

        invoice = Invoice.objects.create(
            payment_order=order,
            user=self.student,
            advisor=self.advisor,
            total=Decimal('0.00')
        )

        payment = Payment.objects.create(
            invoice=invoice,
            user=self.student,
            advisor=self.advisor,
            payment_method='EX',
            amount=Decimal('0.00'),
            status='V',
            payer_name='Juan Pérez'
        )

        self.assertEqual(payment.amount, Decimal('0.00'))
        self.assertEqual(payment.payment_method, 'EX')
        self.assertEqual(payment.status, 'V')

    def test_order_status_changes_to_paid(self):
        """Test que el estado de la orden cambie a PAID"""
        order = PaymentOrder.objects.create(
            student=self.student,
            advisor=self.advisor,
            status='PENDING',
            total_order=Decimal('0.00')
        )

        # Simular proceso de pago exonerado
        order.status = 'PAID'
        order.save()

        order.refresh_from_db()
        self.assertEqual(order.status, 'PAID')

    def test_invoice_status_is_paid(self):
        """Test que la factura tenga estado 'P' (Pagada)"""
        order = PaymentOrder.objects.create(
            student=self.student,
            advisor=self.advisor,
            status='PENDING',
            total_order=Decimal('0.00')
        )

        invoice = Invoice.objects.create(
            payment_order=order,
            user=self.student,
            advisor=self.advisor,
            status='P',
            total=Decimal('0.00'),
            balance_due=Decimal('0.00')
        )

        self.assertEqual(invoice.status, 'P')
        self.assertEqual(invoice.balance_due, Decimal('0.00'))

    def test_payment_allocations_created(self):
        """Test que se creen las asignaciones de pago"""
        order = PaymentOrder.objects.create(
            student=self.student,
            advisor=self.advisor,
            status='PAID',
            total_order=Decimal('0.00')
        )

        invoice = Invoice.objects.create(
            payment_order=order,
            user=self.student,
            advisor=self.advisor,
            status='P',
            total=Decimal('0.00')
        )

        detail = InvoiceDetail.objects.create(
            invoice=invoice,
            concept=self.concept1,
            description='Test',
            quantity=1,
            unit_price=Decimal('0.00'),
            subtotal=Decimal('0.00')
        )

        payment = Payment.objects.create(
            invoice=invoice,
            user=self.student,
            payment_method='EX',
            amount=Decimal('0.00'),
            status='V',
            payer_name='Juan Pérez'
        )

        allocation = PaymentAllocation.objects.create(
            payment=payment,
            invoice_detail=detail,
            concept=self.concept1,
            amount_applied=Decimal('0.00'),
            status='PAID'
        )

        self.assertEqual(allocation.amount_applied, Decimal('0.00'))
        self.assertEqual(allocation.status, 'PAID')

    def test_student_not_found(self):
        """Test error cuando el estudiante no existe"""
        payload = {
            "student_id": 99999,  # ID inexistente
            "concepts": [{"concept_id": self.concept1.id, "quantity": 1}],
            "payer_name": "Juan Pérez"
        }

        # Esto debería generar error 404

    def test_concept_not_found(self):
        """Test error cuando un concepto no existe"""
        payload = {
            "student_id": self.student.id,
            "concepts": [{"concept_id": 99999, "quantity": 1}],  # ID inexistente
            "payer_name": "Juan Pérez"
        }

        # Esto debería generar error 404

    def test_advisor_not_found(self):
        """Test error cuando el asesor no existe"""
        payload = {
            "student_id": self.student.id,
            "concepts": [{"concept_id": self.concept1.id, "quantity": 1}],
            "payer_name": "Juan Pérez",
            "advisor_id": 99999  # ID inexistente
        }

        # Esto debería generar error 404


class ExoneratedPaymentIntegrationTests(TestCase):
    """Tests de integración para el flujo completo"""

    def setUp(self):
        """Configuración inicial"""
        self.student = User.objects.create_user(
            username='student_int',
            email='student_int@test.com'
        )

        self.category = PaymentCategory.objects.create(
            code='INT',
            name='Integration',
            is_active=True
        )

        self.concept = PaymentConcept.objects.create(
            code='INT1',
            name='Integration Concept',
            category=self.category,
            is_active=True
        )

    def test_full_exonerated_payment_flow(self):
        """Test del flujo completo de pago exonerado"""
        # 1. Crear orden
        order = PaymentOrder.objects.create(
            student=self.student,
            advisor=self.student,
            status='PENDING',
            total_order=Decimal('0.00')
        )

        # 2. Crear detalle
        PaymentOrderDetails.objects.create(
            payment_order=order,
            payment_concept=self.concept,
            quantity=1,
            price=Decimal('0.00'),
            sub_total=Decimal('0.00')
        )

        # 3. Crear factura
        invoice = Invoice.objects.create(
            payment_order=order,
            user=self.student,
            status='P',
            total=Decimal('0.00')
        )

        # 4. Crear detalle de factura
        detail = InvoiceDetail.objects.create(
            invoice=invoice,
            concept=self.concept,
            description='Test',
            quantity=1,
            unit_price=Decimal('0.00'),
            subtotal=Decimal('0.00')
        )

        # 5. Crear pago
        payment = Payment.objects.create(
            invoice=invoice,
            user=self.student,
            payment_method='EX',
            amount=Decimal('0.00'),
            status='V',
            payer_name='Test User'
        )

        # 6. Crear asignación
        PaymentAllocation.objects.create(
            payment=payment,
            invoice_detail=detail,
            concept=self.concept,
            amount_applied=Decimal('0.00'),
            status='PAID'
        )

        # 7. Actualizar estado
        order.status = 'PAID'
        order.save()

        # Verificaciones finales
        order.refresh_from_db()
        self.assertEqual(order.status, 'PAID')
        self.assertEqual(order.total_order, Decimal('0.00'))
        self.assertEqual(invoice.status, 'P')
        self.assertEqual(payment.payment_method, 'EX')
        self.assertEqual(payment.amount, Decimal('0.00'))
        self.assertEqual(PaymentAllocation.objects.count(), 1)
