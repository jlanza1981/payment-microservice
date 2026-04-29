from apps.pagos.application.services.payment_history_service import PaymentHistoryService
from apps.pagos.application.services.payment_pdf_service import PaymentPDFService
from apps.pagos.domain.interface.repository.payment_repository_interface import PaymentRepositoryInterface
from typing import Dict, Any

from apps.pagos.infrastructure.services.celery_pdf_generator_service import CeleryPDFGeneratorService
from apps.pagos.infrastructure.services.local_file_storage_service import LocalFileStorageService


class StudentPaymentHistoryUseCase:
    def __init__(self, payment_repository: PaymentRepositoryInterface, legacy_payment_repository: PaymentRepositoryInterface):
        self.service = PaymentHistoryService(
            payment_repository,
            legacy_payment_repository,
            PaymentPDFService(LocalFileStorageService(), CeleryPDFGeneratorService())
        )
    def execute(self, student_id, filter_dict:Dict[str, Any] = None, domain_name = None):
        return self.service.get_student_payments(
            student_id=student_id,
            filters=filter_dict,
            domain_name=domain_name,
            ensure_pdfs=True)