"""
Tests unitarios para PaymentHistoryService siguiendo DDD y Clean Code.

Estos tests demuestran cómo la nueva arquitectura facilita el testing
sin necesidad de dependencias externas (Django, Celery, filesystem).
"""
import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch
from dataclasses import replace

from apps.pagos.application.dto.student_payment_dto import StudentPaymentDTO
from apps.pagos.application.services.payment_history_service import PaymentHistoryService
from apps.pagos.application.services.payment_pdf_service import PaymentPDFService
from apps.pagos.domain.interface.repository.payment_repository_interface import PaymentRepositoryInterface


class TestPaymentHistoryService(unittest.TestCase):
    """
    Tests unitarios para PaymentHistoryService.
    """

    def setUp(self):
        """Configuración antes de cada test."""
        # Crear mocks de las dependencias
        self.mock_payment_repo = MagicMock(spec=PaymentRepositoryInterface)
        self.mock_legacy_repo = MagicMock(spec=PaymentRepositoryInterface)
        self.mock_pdf_service = MagicMock(spec=PaymentPDFService)
        
        # Crear instancia del servicio con mocks
        self.service = PaymentHistoryService(
            payment_repository=self.mock_payment_repo,
            legacy_payment_repository=self.mock_legacy_repo,
            payment_pdf_service=self.mock_pdf_service
        )

    def test_get_student_payments_combines_both_sources(self):
        """
        Test: El servicio combina pagos de ambas fuentes (new y legacy).
        """
        # Arrange
        student_id = 123
        base_url = "https://test.com"
        
        new_payment = StudentPaymentDTO(
            id=1,
            student_id=student_id,
            amount=Decimal('100.00'),
            currency='USD',
            date='2024-01-15',
            source='new',
            method='credit_card',
            invoice_id=1,
            invoice_number='INV-001',
            invoice=None,
            payer_name='John Doe',
            file='payments/payment_1.pdf'
        )
        
        legacy_payment = StudentPaymentDTO(
            id=2,
            student_id=student_id,
            amount=Decimal('50.00'),
            currency='USD',
            date='2024-01-10',
            source='legacy',
            method='bank_transfer',
            invoice_id=2,
            invoice_number='INV-002',
            invoice=None,
            payer_name='Jane Doe',
            file='legacy/payment_2.pdf'
        )
        
        # Configurar mocks
        self.mock_payment_repo.get_by_student.return_value = [new_payment]
        self.mock_legacy_repo.get_by_student.return_value = [legacy_payment]
        self.mock_pdf_service.ensure_payment_pdfs_exist.return_value = [legacy_payment, new_payment]
        
        # Act
        result = self.service.get_student_payments(
            student_id=student_id,
            base_url=base_url
        )
        
        # Assert
        self.assertEqual(len(result), 2)
        self.mock_payment_repo.get_by_student.assert_called_once_with(student_id, None)
        self.mock_legacy_repo.get_by_student.assert_called_once_with(student_id, None)

    def test_get_student_payments_sorts_by_date(self):
        """
        Test: Los pagos se ordenan cronológicamente.
        """
        # Arrange
        student_id = 123
        base_url = "https://test.com"
        
        payment1 = self._create_payment(id=1, date='2024-01-20', source='new')
        payment2 = self._create_payment(id=2, date='2024-01-10', source='legacy')
        payment3 = self._create_payment(id=3, date='2024-01-15', source='new')
        
        self.mock_payment_repo.get_by_student.return_value = [payment1, payment3]
        self.mock_legacy_repo.get_by_student.return_value = [payment2]
        self.mock_pdf_service.ensure_payment_pdfs_exist.return_value = [payment2, payment3, payment1]
        
        # Act
        result = self.service.get_student_payments(
            student_id=student_id,
            base_url=base_url
        )
        
        # Assert - deben estar ordenados por fecha
        self.assertEqual(result[0].date, '2024-01-10')
        self.assertEqual(result[1].date, '2024-01-15')
        self.assertEqual(result[2].date, '2024-01-20')

    def test_get_student_payments_with_filters(self):
        """
        Test: Los filtros se pasan correctamente a los repositorios.
        """
        # Arrange
        student_id = 123
        base_url = "https://test.com"
        filters = {'date_from': '2024-01-01', 'status': 'verified'}
        
        self.mock_payment_repo.get_by_student.return_value = []
        self.mock_legacy_repo.get_by_student.return_value = []
        self.mock_pdf_service.ensure_payment_pdfs_exist.return_value = []
        
        # Act
        self.service.get_student_payments(
            student_id=student_id,
            filters=filters,
            base_url=base_url
        )
        
        # Assert
        self.mock_payment_repo.get_by_student.assert_called_once_with(student_id, filters)
        self.mock_legacy_repo.get_by_student.assert_called_once_with(student_id, filters)

    def test_get_student_payments_without_pdf_verification(self):
        """
        Test: Cuando ensure_pdfs=False, no se llama al servicio de PDFs.
        """
        # Arrange
        student_id = 123
        
        payment = self._create_payment(id=1, date='2024-01-15', source='new')
        self.mock_payment_repo.get_by_student.return_value = [payment]
        self.mock_legacy_repo.get_by_student.return_value = []
        
        # Act
        result = self.service.get_student_payments(
            student_id=student_id,
            ensure_pdfs=False  # No verificar PDFs
        )
        
        # Assert
        self.assertEqual(len(result), 1)
        self.mock_pdf_service.ensure_payment_pdfs_exist.assert_not_called()

    def test_get_student_payments_raises_error_without_base_url(self):
        """
        Test: Lanza error si ensure_pdfs=True pero no se proporciona base_url.
        """
        # Arrange
        student_id = 123
        
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            self.service.get_student_payments(
                student_id=student_id,
                ensure_pdfs=True,
                base_url=None  # No proporcionada
            )
        
        self.assertIn('base_url es requerido', str(context.exception))

    def test_get_student_payments_handles_repository_errors_gracefully(self):
        """
        Test: Si un repositorio falla, el servicio continúa con el otro.
        """
        # Arrange
        student_id = 123
        base_url = "https://test.com"
        
        payment = self._create_payment(id=1, date='2024-01-15', source='new')
        
        # Simular error en repositorio legacy
        self.mock_payment_repo.get_by_student.return_value = [payment]
        self.mock_legacy_repo.get_by_student.side_effect = Exception("DB error")
        self.mock_pdf_service.ensure_payment_pdfs_exist.return_value = [payment]
        
        # Act
        result = self.service.get_student_payments(
            student_id=student_id,
            base_url=base_url
        )
        
        # Assert - debe retornar solo los pagos del repositorio que funcionó
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].source, 'new')

    def test_get_student_payments_calls_pdf_service_with_correct_params(self):
        """
        Test: El servicio de PDFs se llama con los parámetros correctos.
        """
        # Arrange
        student_id = 123
        base_url = "https://test.com"
        
        payment = self._create_payment(id=1, date='2024-01-15', source='new')
        self.mock_payment_repo.get_by_student.return_value = [payment]
        self.mock_legacy_repo.get_by_student.return_value = []
        self.mock_pdf_service.ensure_payment_pdfs_exist.return_value = [payment]
        
        # Act
        self.service.get_student_payments(
            student_id=student_id,
            base_url=base_url,
            ensure_pdfs=True
        )
        
        # Assert
        self.mock_pdf_service.ensure_payment_pdfs_exist.assert_called_once()
        call_args = self.mock_pdf_service.ensure_payment_pdfs_exist.call_args
        self.assertEqual(call_args.kwargs['base_url'], base_url)
        self.assertIsInstance(call_args.kwargs['payments'], list)

    # Helper methods
    def _create_payment(self, id: int, date: str, source: str) -> StudentPaymentDTO:
        """Helper para crear un DTO de pago de prueba."""
        return StudentPaymentDTO(
            id=id,
            student_id=123,
            amount=Decimal('100.00'),
            currency='USD',
            date=date,
            source=source,
            method='credit_card',
            invoice_id=id,
            invoice_number=f'INV-{id:03d}',
            invoice=None,
            payer_name='Test User',
            file=f'payments/payment_{id}.pdf'
        )


class TestPaymentHistoryServiceIntegration(unittest.TestCase):
    """
    Tests de integración (requieren dependencias reales, pero aún mockeadas).
    """

    @patch('apps.pagos.infrastructure.repository.payment_repository.PaymentRepository')
    @patch('apps.pagos.infrastructure.repository.legacy_payment_repository.LegacyPaymentRepository')
    def test_service_with_real_dependencies_structure(self, mock_legacy_repo_class, mock_repo_class):
        """
        Test: Verificar que el servicio se puede instanciar con dependencias reales.
        """
        # Arrange
        from apps.pagos.application.dependencies import get_payment_history_service
        
        mock_repo_class.return_value = MagicMock()
        mock_legacy_repo_class.return_value = MagicMock()
        
        # Act
        service = get_payment_history_service()
        
        # Assert
        self.assertIsInstance(service, PaymentHistoryService)
        self.assertIsNotNone(service.payment_repository)
        self.assertIsNotNone(service.legacy_payment_repository)
        self.assertIsNotNone(service.payment_pdf_service)


if __name__ == '__main__':
    unittest.main()

