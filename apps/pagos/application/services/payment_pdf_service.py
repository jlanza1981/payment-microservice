import logging
from typing import List
from dataclasses import replace

from api.DRF.ExtraFunction import DataPlanilla
from apps.pagos.application.dto.student_payment_dto import StudentPaymentDTO
from apps.pagos.domain.interface.services.file_storage_service_interface import FileStorageServiceInterface
from apps.pagos.domain.interface.services.pdf_generator_service_interface import PDFGeneratorServiceInterface

logger = logging.getLogger(__name__)


class PaymentPDFService:

    def __init__(
        self,
        file_storage_service: FileStorageServiceInterface,
        pdf_generator_service: PDFGeneratorServiceInterface
    ):

        self.file_storage_service = file_storage_service
        self.pdf_generator_service = pdf_generator_service

    def ensure_payment_pdfs_exist(
        self,
        payments: List[StudentPaymentDTO],
        domain_name: str
    ) -> List[StudentPaymentDTO]:

        result = []
        
        for payment in payments:
            updated_payment = self._ensure_single_payment_pdf(payment, domain_name)
            result.append(updated_payment)
        
        return result

    def _ensure_single_payment_pdf(
        self,
        payment: StudentPaymentDTO,
        domain_name: str
    ) -> StudentPaymentDTO:
        """
        Verifica y crea el PDF de un solo pago si es necesario.
        Construye la URL completa para acceder al archivo.
        """
        # Caso 1: El pago NO tiene archivo (payment.file es None o vacío) -> CREAR PDF
        if not payment.file:
            logger.warning(
                f"PDF no existe para pago {payment.id} (fuente: {payment.source}). Creando..."
            )
            return self._generated_pdf(payment, domain_name)

        # Caso 2: El pago tiene archivo con URL completa -> Verificar existencia física
        if payment.file and self.file_storage_service.exists(payment.file):
            pdf_full_url = f"{domain_name}/media{payment.file}"
            return replace(payment, file=pdf_full_url)
        else:
            return self._generated_pdf(payment, domain_name)


    def _regenerate_payment_pdf(
            self,
            payment: StudentPaymentDTO
    ) -> str:

        if not payment.invoice or not payment.invoice_id:
            raise ValueError(
                f"Pago {payment.id} no tiene factura asociada para generar PDF"
            )

        # Preparar datos según el tipo de factura
        if payment.source == "legacy":
            invoice_data = self._prepare_legacy_invoice_data(payment.invoice)
            pdf_path = self.pdf_generator_service.generate_legacy_payment_pdf(
                invoice_id=payment.invoice_id,
                invoice_data=invoice_data
            )
        else:
            invoice_data = self._prepare_invoice_data(payment.invoice)
            pdf_path = self.pdf_generator_service.generate_payment_pdf(
                invoice=payment.invoice,
                invoice_data=invoice_data
            )

        logger.info(f"PDF regenerado exitosamente para pago {payment.id}: {pdf_path}")
        return pdf_path

    def _generated_pdf(self, payment, domain_name: str):
        try:
            pdf_relative_path = self._regenerate_payment_pdf(payment)
            pdf_full_url = f"{domain_name}/media/{pdf_relative_path}"
            logger.info(f"✓ PDF creado exitosamente: {pdf_full_url}")

            return replace(payment, file=pdf_full_url)

        except Exception as e:
            logger.error(
                f"✗ Error creando PDF para pago {payment.id}: {str(e)}"
            )
            return payment

    @staticmethod
    def _prepare_legacy_invoice_data(invoice) -> dict:
        """Prepara datos de factura legacy para generación de PDF."""
        return DataPlanilla(invoice, True)

    @staticmethod
    def _prepare_invoice_data(invoice) -> dict:
        """Prepara datos de factura nueva para generación de PDF."""
        return invoice.get_invoice_structure

