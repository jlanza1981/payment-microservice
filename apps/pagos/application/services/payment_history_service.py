"""
Servicio de aplicación para gestionar el historial de pagos de estudiantes.

Este servicio se enfoca exclusivamente en:
- Obtener pagos de múltiples fuentes (nueva y legacy)
- Combinar y ordenar los pagos
- Delegar la gestión de PDFs a un servicio especializado
"""
import logging
from typing import List, Dict, Any, Optional

from apps.pagos.application.dto.student_payment_dto import StudentPaymentDTO
from apps.pagos.application.services.payment_pdf_service import PaymentPDFService
from apps.pagos.domain.interface.repository.payment_repository_interface import PaymentRepositoryInterface

logger = logging.getLogger(__name__)


class PaymentHistoryService:
    """
    Servicio de aplicación para consultar el historial de pagos de un estudiante.
    
    Responsabilidades:
    - Obtener pagos de repositorios (nuevo y legacy)
    - Combinar pagos de diferentes fuentes
    - Ordenar cronológicamente
    - Coordinar con el servicio de PDFs para asegurar disponibilidad de archivos
    """

    def __init__(
        self,
        payment_repository: PaymentRepositoryInterface,
        legacy_payment_repository: PaymentRepositoryInterface,
        payment_pdf_service: Optional[PaymentPDFService] = None
    ):
        self.payment_repository = payment_repository
        self.legacy_payment_repository = legacy_payment_repository
        self.payment_pdf_service = payment_pdf_service

    def get_student_payments(
        self,
        student_id: int,
        filters: Optional[Dict[str, Any]] = None,
        domain_name = None,
        ensure_pdfs: bool = True
    ) -> List[StudentPaymentDTO]:
        """
        Obtiene el historial completo de pagos de un estudiante.
        Combina pagos de la plataforma nueva y legacy, los ordena cronológicamente
        y opcionalmente asegura que los PDFs estén disponibles con URLs completas.
        """
        logger.info(f"Obteniendo historial de pagos para estudiante {student_id}")

        # Obtener pagos de ambas fuentes
        new_payments = self._get_new_payments(student_id, filters)
        legacy_payments = self._get_legacy_payments(student_id, filters)

        # Combinar y ordenar
        all_payments = self._combine_and_sort_payments(new_payments, legacy_payments)

        # Asegurar disponibilidad de PDFs y construir URLs completas si se requiere
        if ensure_pdfs and self.payment_pdf_service and domain_name:
            all_payments = self.payment_pdf_service.ensure_payment_pdfs_exist(
                payments=all_payments,
                domain_name=domain_name
            )

        logger.info(
            f"Historial obtenido: {len(new_payments)} pagos nuevos, "
            f"{len(legacy_payments)} pagos legacy"
        )

        return all_payments

    def _get_new_payments(
        self,
        student_id: int,
        filters: Optional[Dict[str, Any]]
    ) -> List[StudentPaymentDTO]:
        return self.payment_repository.get_by_student(student_id, filters)

    def _get_legacy_payments(
        self,
        student_id: int,
        filters: Optional[Dict[str, Any]]
    ) -> List[StudentPaymentDTO]:
        return self.legacy_payment_repository.get_by_student(student_id, filters)

    @staticmethod
    def _combine_and_sort_payments(
        new_payments: List[StudentPaymentDTO],
        legacy_payments: List[StudentPaymentDTO]
    ) -> List[StudentPaymentDTO]:
        all_payments = [*new_payments, *legacy_payments]
        all_payments.sort(key=lambda payment: payment.date)
        return all_payments
