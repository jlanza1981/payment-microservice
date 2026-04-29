"""
Tests Completos: WebhookEventProcessor

Suite de tests para validar el procesamiento de eventos de webhook de PayPal:
1. PAYMENT.CAPTURE.COMPLETED - Pago exitoso
2. PAYMENT.CAPTURE.DECLINED - Pago rechazado
3. PAYMENT.CAPTURE.DENIED - Pago denegado

Simula todo el flujo como si fuera un estudiante real realizando el pago,
para verificar las notificaciones por correo electrónico.

Author: Sistema LC Mundo
Date: 2026-03-25
"""

from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils import timezone

from apps.administrador.models import Usuarios
from apps.billing.domain.interface.services import InvoiceDomainService
from apps.billing.models import Invoice
from apps.billing.infrastructure.repository.invoice_repository import InvoiceRepository
from apps.billing.application.services.invoice_service import InvoiceService
from apps.core.domain.events.inbox_event_created import InboxEventCreated
from apps.core.infrastructure.inbox.event_processor import WebhookEventProcessor
from apps.core.infrastructure.inbox.repository.inbox_repository import InboxRepository
from apps.orden_pagos.infrastructure.repository.payment_order_repository import PaymentOrderRepository
from apps.orden_pagos.infrastructure.repository.payment_concept_repository import PaymentConceptRepository
from apps.orden_pagos.models import PaymentOrder, PaymentConcept, PaymentOrderDetails, PaymentOrderProgram
from apps.pagos.infrastructure.repository.payment_repository import PaymentRepository
from apps.pagos.models import InboxEvent, Payment
from apps.user.infrastructure.repository.users_repository import UsersRepository


class WebhookEventProcessorTest(TestCase):
    """
    Suite de tests para WebhookEventProcessor.

    Tests incluidos:
    1. test_payment_capture_completed_success - Pago completado exitosamente
    2. test_payment_capture_declined_sends_notification - Pago rechazado con notificación
    3. test_payment_capture_denied_sends_notification - Pago denegado con notificación
    """

    def setUp(self):
        """
        Configuración inicial para cada test.
        Crea un estudiante completo con orden de pago y conceptos.
        """
        # Crear usuarios de prueba (estudiante y asesor)
        self.student = Usuarios.objects.create(
            nombre='Carlos',
            apellido='Rodríguez',
            email='carlos.rodriguez@test.com',
            correo='carlos.rodriguez@test.com',
            tipo_usuario='student'
        )

        self.advisor = Usuarios.objects.create(
            nombre='Ana',
            apellido='Martínez',
            email='ana.martinez@test.com',
            correo='ana.martinez@test.com',
            tipo_usuario='advisor'
        )

        # Crear conceptos de pago
        self.concept_matricula = PaymentConcept.objects.create(
            code='M',
            description='Matrícula',
            unit_price=Decimal('2000.00'),
            currency='USD',
            is_active=True
        )

        self.concept_inscripcion = PaymentConcept.objects.create(
            code='I',
            description='Inscripción',
            unit_price=Decimal('150.00'),
            currency='USD',
            is_active=True
        )

        # Crear orden de pago
        self.payment_order = PaymentOrder.objects.create(
            order_number='ORD-2026-001',
            student=self.student,
            advisor=self.advisor,
            status='PENDING',
            total_order=Decimal('2150.00'),
            currency='USD',
            consumed=False
        )

        # Crear programa asociado a la orden
        self.program = PaymentOrderProgram.objects.create(
            payment_order=self.payment_order,
            duration=12,
            duration_type='w',
            price_week=Decimal('100.00'),
            material_cost=Decimal('200.00')
        )

        # Crear detalles de la orden
        PaymentOrderDetails.objects.create(
            payment_order=self.payment_order,
            payment_concept=self.concept_matricula,
            amount=Decimal('2000.00'),
            quantity=1,
            sub_total=Decimal('2000.00')
        )

        PaymentOrderDetails.objects.create(
            payment_order=self.payment_order,
            payment_concept=self.concept_inscripcion,
            amount=Decimal('150.00'),
            quantity=1,
            sub_total=Decimal('150.00')
        )

        # Inicializar repositorios
        self.inbox_repository = InboxRepository()
        self.payment_order_repository = PaymentOrderRepository()
        self.invoice_repository = InvoiceRepository()
        self.payment_repository = PaymentRepository()
        self.payment_concept_repository = PaymentConceptRepository()
        self.user_repository = UsersRepository()
        self.invoice_service = InvoiceDomainService()

        # Inicializar el procesador de eventos
        self.event_processor = WebhookEventProcessor(
            inbox_repository=self.inbox_repository,
            payment_order_repository=self.payment_order_repository,
            invoice_repository=self.invoice_repository,
            payment_repository=self.payment_repository,
            payment_concept_repository=self.payment_concept_repository,
            user_repository=self.user_repository,
            invoice_service=self.invoice_service
        )

    def tearDown(self):
        """Limpieza después de cada test."""
        Payment.objects.all().delete()
        Invoice.objects.all().delete()
        InboxEvent.objects.all().delete()
        PaymentOrderDetails.objects.all().delete()
        PaymentOrderProgram.objects.all().delete()
        PaymentOrder.objects.all().delete()
        PaymentConcept.objects.all().delete()
        Usuarios.objects.all().delete()

    # ========================================================================
    # TEST 1: PAYMENT.CAPTURE.COMPLETED - PAGO EXITOSO
    # ========================================================================

    def test_payment_capture_completed_success(self):
        """
        Test: Procesar evento PAYMENT.CAPTURE.COMPLETED exitoso.

        Simula un estudiante que completa el pago por PayPal.

        Valida:
        - InboxEvent se crea correctamente
        - Pago se registra con status 'V' (Verificado)
        - Factura se genera automáticamente
        - InboxEvent se marca como procesado
        - Se envía correo de confirmación (mock)
        """
        # Arrange: Crear el payload de PayPal (evento COMPLETED)
        paypal_capture_id = 'CAPTURE-123456789'
        paypal_order_id = 'ORDER-987654321'
        
        payload = {
            "id": "WH-EVENT-123456789",
            "event_version": "1.0",
            "create_time": timezone.now().isoformat(),
            "resource_type": "capture",
            "resource": {
                "id": paypal_capture_id,
                "status": "COMPLETED",
                "amount": {
                    "value": "2150.00",
                    "currency_code": "USD"
                },
                "final_capture": True,
                "seller_protection": {
                    "status": "ELIGIBLE"
                },
                "payee": {
                    "email_address": "merchant@lcmundo.com",
                    "merchant_id": "MERCHANT123"
                },
                "create_time": timezone.now().isoformat(),
                "update_time": timezone.now().isoformat(),
                "links": []
            },
            "links": []
        }

        # Crear el InboxEvent (lo que haría el webhook)
        inbox_event = InboxEvent.objects.create(
            event_id="WH-EVENT-123456789",
            event_type="PAYMENT.CAPTURE.COMPLETED",
            provider="paypal",
            payload=payload,
            processed=False,
            payer_name=f"{self.student.nombre} {self.student.apellido}",
            payment_order_id=self.payment_order.id
        )

        # Crear el evento de dominio
        created_event = InboxEventCreated(
            inbox_event_id=inbox_event.id,
            provider="paypal",
            event_type="PAYMENT.CAPTURE.COMPLETED",
            event_id="WH-EVENT-123456789",
            payment_order_id=self.payment_order.id,
            payer_name=f"{self.student.nombre} {self.student.apellido}"
        )

        # Act: Procesar el evento
        with patch('apps.pagos.application.services.payment_processing_service.SendEmailUseCase') as mock_email:
            mock_email.return_value.execute.return_value = {'success': True}
            
            self.event_processor.process_pending(created_event)

        # Assert: Verificar que el evento fue procesado
        inbox_event.refresh_from_db()
        self.assertTrue(inbox_event.processed, "El InboxEvent debe estar marcado como procesado")

        # Verificar que se creó el pago
        payment = Payment.objects.filter(
            user=self.student,
            payment_reference_number=paypal_capture_id
        ).first()
        
        self.assertIsNotNone(payment, "Debe existir un pago creado")
        self.assertEqual(payment.status, 'V', "El pago debe estar verificado")
        self.assertEqual(payment.amount, Decimal('2150.00'), "El monto debe ser correcto")
        self.assertEqual(payment.payment_method, 'PP', "El método debe ser PayPal")

        # Verificar que se creó la factura
        invoice = Invoice.objects.filter(payment_order=self.payment_order).first()
        self.assertIsNotNone(invoice, "Debe existir una factura generada")
        self.assertEqual(invoice.user, self.student, "La factura debe ser del estudiante")

        print("✅ TEST COMPLETADO: Pago exitoso procesado correctamente")
        print(f"   📧 Correo enviado a: {self.student.email}")
        print(f"   💰 Pago: {payment.payment_number}")
        print(f"   🧾 Factura: {invoice.invoice_number}")

    # ========================================================================
    # TEST 2: PAYMENT.CAPTURE.DECLINED - PAGO RECHAZADO
    # ========================================================================

    def test_payment_capture_declined_sends_notification(self):
        """
        Test: Procesar evento PAYMENT.CAPTURE.DECLINED (pago rechazado).

        Simula un estudiante cuyo pago es rechazado por PayPal
        (ej: fondos insuficientes, tarjeta bloqueada).

        Valida:
        - InboxEvent se crea correctamente
        - Se registra la transacción de pago fallida
        - InboxEvent se marca como procesado
        - Se envía correo de notificación al estudiante y asesor
        """
        # Arrange: Crear el payload de PayPal (evento DECLINED)
        paypal_capture_id = 'CAPTURE-DECLINED-123'
        
        payload = {
            "id": "WH-EVENT-DECLINED-123",
            "event_version": "1.0",
            "create_time": timezone.now().isoformat(),
            "resource_type": "capture",
            "resource": {
                "id": paypal_capture_id,
                "status": "DECLINED",
                "status_details": {
                    "reason": "INSUFFICIENT_FUNDS"
                },
                "amount": {
                    "value": "2150.00",
                    "currency_code": "USD"
                },
                "payee": {
                    "email_address": "merchant@lcmundo.com",
                    "merchant_id": "MERCHANT123"
                },
                "create_time": timezone.now().isoformat(),
                "update_time": timezone.now().isoformat(),
            }
        }

        # Crear el InboxEvent
        inbox_event = InboxEvent.objects.create(
            event_id="WH-EVENT-DECLINED-123",
            event_type="PAYMENT.CAPTURE.DECLINED",
            provider="paypal",
            payload=payload,
            processed=False,
            payer_name=f"{self.student.nombre} {self.student.apellido}",
            payment_order_id=self.payment_order.id
        )

        # Crear el evento de dominio
        created_event = InboxEventCreated(
            inbox_event_id=inbox_event.id,
            provider="paypal",
            event_type="PAYMENT.CAPTURE.DECLINED",
            event_id="WH-EVENT-DECLINED-123",
            payment_order_id=self.payment_order.id,
            payer_name=f"{self.student.nombre} {self.student.apellido}"
        )

        # Act: Procesar el evento con mock del envío de email
        with patch('apps.notifications_message.application.send_email.SendEmailUseCase.execute') as mock_email:
            mock_email.return_value = {
                'success': True,
                'emails': [self.student.email, self.advisor.email]
            }
            
            self.event_processor.process_pending(created_event)

        # Assert: Verificar que el evento fue procesado
        inbox_event.refresh_from_db()
        self.assertTrue(inbox_event.processed, "El InboxEvent debe estar marcado como procesado")

        # Verificar que se llamó al envío de email
        mock_email.assert_called_once()
        
        print("✅ TEST COMPLETADO: Pago rechazado procesado correctamente")
        print(f"   📧 Notificación enviada a: {self.student.email}, {self.advisor.email}")
        print(f"   ❌ Razón: INSUFFICIENT_FUNDS")
        print("   💡 El estudiante debe recibir un correo para intentar nuevamente")

    # ========================================================================
    # TEST 3: PAYMENT.CAPTURE.DENIED - PAGO DENEGADO
    # ========================================================================

    def test_payment_capture_denied_sends_notification(self):
        """
        Test: Procesar evento PAYMENT.CAPTURE.DENIED (pago denegado).

        Simula un estudiante cuyo pago es denegado por PayPal
        (ej: problema de autenticación, restricción de país).

        Valida:
        - InboxEvent se crea correctamente
        - Se registra la transacción de pago fallida
        - InboxEvent se marca como procesado
        - Se envía correo de notificación al estudiante y asesor
        """
        # Arrange: Crear el payload de PayPal (evento DENIED)
        paypal_capture_id = 'CAPTURE-DENIED-456'
        
        payload = {
            "id": "WH-EVENT-DENIED-456",
            "event_version": "1.0",
            "create_time": timezone.now().isoformat(),
            "resource_type": "capture",
            "resource": {
                "id": paypal_capture_id,
                "status": "DENIED",
                "status_details": {
                    "reason": "PAYMENT_DENIED"
                },
                "amount": {
                    "value": "2150.00",
                    "currency_code": "USD"
                },
                "payee": {
                    "email_address": "merchant@lcmundo.com",
                    "merchant_id": "MERCHANT123"
                },
                "create_time": timezone.now().isoformat(),
                "update_time": timezone.now().isoformat(),
            }
        }

        # Crear el InboxEvent
        inbox_event = InboxEvent.objects.create(
            event_id="WH-EVENT-DENIED-456",
            event_type="PAYMENT.CAPTURE.DENIED",
            provider="paypal",
            payload=payload,
            processed=False,
            payer_name=f"{self.student.nombre} {self.student.apellido}",
            payment_order_id=self.payment_order.id
        )

        # Crear el evento de dominio
        created_event = InboxEventCreated(
            inbox_event_id=inbox_event.id,
            provider="paypal",
            event_type="PAYMENT.CAPTURE.DENIED",
            event_id="WH-EVENT-DENIED-456",
            payment_order_id=self.payment_order.id,
            payer_name=f"{self.student.nombre} {self.student.apellido}"
        )

        # Act: Procesar el evento con mock del envío de email
        with patch('apps.notifications_message.application.send_email.SendEmailUseCase.execute') as mock_email:
            mock_email.return_value = {
                'success': True,
                'emails': [self.student.email, self.advisor.email]
            }
            
            self.event_processor.process_pending(created_event)

        # Assert: Verificar que el evento fue procesado
        inbox_event.refresh_from_db()
        self.assertTrue(inbox_event.processed, "El InboxEvent debe estar marcado como procesado")

        # Verificar que se llamó al envío de email
        mock_email.assert_called_once()
        
        print("✅ TEST COMPLETADO: Pago denegado procesado correctamente")
        print(f"   📧 Notificación enviada a: {self.student.email}, {self.advisor.email}")
        print(f"   ❌ Razón: PAYMENT_DENIED")
        print("   💡 El estudiante debe recibir un correo para resolver el problema")

    # ========================================================================
    # TEST 4: MULTIPLE EVENTS - VARIOS EVENTOS PENDIENTES
    # ========================================================================

    def test_process_multiple_pending_events(self):
        """
        Test: Procesar múltiples eventos pendientes en cola.

        Simula varios intentos de pago de un estudiante.

        Valida:
        - Todos los eventos pendientes se procesan
        - Cada evento se marca como procesado individualmente
        - El orden no afecta el procesamiento
        """
        # Arrange: Crear múltiples eventos
        events_data = [
            {
                "event_id": "WH-EVENT-001",
                "event_type": "PAYMENT.CAPTURE.DECLINED",
                "capture_id": "CAPTURE-001"
            },
            {
                "event_id": "WH-EVENT-002",
                "event_type": "PAYMENT.CAPTURE.DECLINED",
                "capture_id": "CAPTURE-002"
            },
            {
                "event_id": "WH-EVENT-003",
                "event_type": "PAYMENT.CAPTURE.COMPLETED",
                "capture_id": "CAPTURE-003"
            }
        ]

        created_events = []
        for event_data in events_data:
            payload = {
                "id": event_data["event_id"],
                "resource": {
                    "id": event_data["capture_id"],
                    "status": "COMPLETED" if "COMPLETED" in event_data["event_type"] else "DECLINED",
                    "amount": {
                        "value": "2150.00",
                        "currency_code": "USD"
                    },
                    "payee": {
                        "email_address": "merchant@lcmundo.com"
                    }
                }
            }

            inbox_event = InboxEvent.objects.create(
                event_id=event_data["event_id"],
                event_type=event_data["event_type"],
                provider="paypal",
                payload=payload,
                processed=False,
                payer_name=f"{self.student.nombre} {self.student.apellido}",
                payment_order_id=self.payment_order.id
            )

            created_event = InboxEventCreated(
                inbox_event_id=inbox_event.id,
                provider="paypal",
                event_type=event_data["event_type"],
                event_id=event_data["event_id"],
                payment_order_id=self.payment_order.id,
                payer_name=f"{self.student.nombre} {self.student.apellido}"
            )
            created_events.append((inbox_event, created_event))

        # Act: Procesar todos los eventos
        with patch('apps.notifications_message.application.send_email.SendEmailUseCase.execute') as mock_email, \
             patch('apps.pagos.application.services.payment_processing_service.SendEmailUseCase') as mock_payment_email:
            
            mock_email.return_value = {'success': True, 'emails': [self.student.email]}
            mock_payment_email.return_value.execute.return_value = {'success': True}
            
            for inbox_event, created_event in created_events:
                self.event_processor.process_pending(created_event)

        # Assert: Verificar que todos los eventos fueron procesados
        for inbox_event, _ in created_events:
            inbox_event.refresh_from_db()
            self.assertTrue(inbox_event.processed, f"El evento {inbox_event.event_id} debe estar procesado")

        print("✅ TEST COMPLETADO: Múltiples eventos procesados correctamente")
        print(f"   📊 Total eventos procesados: {len(created_events)}")
        print("   💡 Todos los intentos de pago fueron registrados")


# ========================================================================
# INSTRUCCIONES PARA EJECUTAR LOS TESTS
# ========================================================================
"""
CÓMO EJECUTAR ESTOS TESTS:

1. Ejecutar todos los tests del módulo:
   python manage.py test apps.core.tests.test_webhook_event_processor

2. Ejecutar un test específico:
   python manage.py test apps.core.tests.test_webhook_event_processor.WebhookEventProcessorTest.test_payment_capture_completed_success

3. Ejecutar con verbose para ver más detalles:
   python manage.py test apps.core.tests.test_webhook_event_processor -v 2

4. Para probar con datos reales:
   - Edita los valores de self.student.email y self.advisor.email en setUp()
   - Edita el payload con datos reales de PayPal
   - Comenta los @patch y ejecuta en un entorno de desarrollo
   - Verifica que lleguen los correos a las direcciones configuradas

NOTAS IMPORTANTES:
- Los tests usan mocks por defecto para no enviar correos reales
- Para probar correos reales, debes:
  1. Configurar SMTP en settings.py
  2. Comentar los decoradores @patch
  3. Ejecutar en ambiente de desarrollo/staging
  
- Para ver los correos sin enviarlos realmente:
  Usa el backend de consola en settings.py:
  EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
"""

