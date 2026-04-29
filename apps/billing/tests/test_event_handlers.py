"""
Tests para los Event Handlers de Billing.
"""
from unittest.mock import patch
from decimal import Decimal

from apps.billing.events.event_handlers import handle_payment_captured
from apps.core.domain.events.payment_captured_event import PaymentCapturedEvent


class TestBillingEventHandlers:
    """Tests para handlers de eventos en billing"""

    @patch('apps.billing.event_handlers.send_invoice_email_task')
    def test_handle_payment_captured_full_payment_sends_email(self, mock_task):
        """
        Test: Cuando se captura un pago completo, se debe encolar la tarea de email
        """
        # Arrange
        event = PaymentCapturedEvent(
            invoice_id=123,
            payment_id=456,
            payment_receipt_id=1,
            amount=Decimal('100.00'),
            currency='USD',
            is_full_payment=True,
            invoice_number='INV-001',
            payment_provider='paypal'
        )

        # Act
        handle_payment_captured(event)

        # Assert
        mock_task.delay.assert_called_once_with(123)

    @patch('apps.billing.event_handlers.send_invoice_email_task')
    def test_handle_payment_captured_partial_payment_does_not_send_email(self, mock_task):
        """
        Test: Cuando se captura un pago parcial, NO se debe enviar email de factura completa
        """
        # Arrange
        event = PaymentCapturedEvent(
            invoice_id=123,
            payment_id=456,
            payment_receipt_id=1,
            amount=Decimal('50.00'),
            currency='USD',
            is_full_payment=False,  # Pago parcial
            invoice_number='INV-001',
            payment_provider='paypal'
        )

        # Act
        handle_payment_captured(event)

        # Assert
        mock_task.delay.assert_not_called()

    @patch('apps.billing.event_handlers.send_invoice_email_task')
    def test_handle_payment_captured_logs_error_on_task_failure(self, mock_task):
        """
        Test: Si la tarea de Celery falla, se debe loggear el error
        """
        # Arrange
        mock_task.delay.side_effect = Exception("Celery connection error")

        event = PaymentCapturedEvent(
            invoice_id=123,
            payment_id=456,
            payment_receipt_id=None,
            amount=Decimal('100.00'),
            currency='USD',
            is_full_payment=True,
            invoice_number='INV-001',
            payment_provider='paypal'
        )

        # Act & Assert
        # No debería lanzar excepción (debe capturarla y loggear)
        with patch('apps.billing.event_handlers.logger') as mock_logger:
            handle_payment_captured(event)
            mock_logger.error.assert_called()

