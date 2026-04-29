"""
Implementación del servicio de generación de PDFs usando Celery tasks.
"""
import logging
from typing import Any, Dict

from apps.billing.tasks import save_pdf_payment_task
from apps.website.tasks import save_legacy_payment_pdf_task
from apps.pagos.domain.interface.services.pdf_generator_service_interface import PDFGeneratorServiceInterface

logger = logging.getLogger(__name__)


class PDFGenerationError(Exception):
    """Excepción lanzada cuando falla la generación de un PDF."""
    pass


class CeleryPDFGeneratorService(PDFGeneratorServiceInterface):
    """
    Implementación del servicio de generación de PDFs.
    
    NOTA: Llama directamente a las funciones internas para evitar problemas
    de deadlock cuando se ejecuta desde contextos de Celery.
    """

    def generate_payment_pdf(
        self,
        invoice: Any,
        invoice_data: Dict[str, Any]
    ) -> str:
        """
        Genera un PDF de comprobante de pago para una factura nueva.
        
        Args:
            invoice: Objeto Invoice completo
            invoice_data: Datos estructurados de la factura
            
        Returns:
            Ruta relativa del PDF generado
        """
        try:
            logger.info(f"Generando PDF para factura {invoice.id}")
            
            # Llamar directamente a la función para evitar problemas de deadlock
            pdf_content, pdf_path = save_pdf_payment_task(invoice_data)
            
            # Guardar el archivo en el modelo
            invoice.invoice_file = pdf_path
            invoice.save()
            
            logger.info(f"PDF generado exitosamente: {pdf_path}")
            return pdf_path
                
        except Exception as e:
            error_msg = f"Error generando PDF para factura {invoice.id}: {str(e)}"
            logger.error(error_msg)
            raise PDFGenerationError(error_msg) from e

    def generate_legacy_payment_pdf(
        self,
        invoice_id: int,
        invoice_data: Any
    ) -> str:
        """
        Genera un PDF de comprobante de pago para una factura legacy.
        
        Args:
            invoice_id: ID de la factura legacy
            invoice_data: Datos de la factura legacy
            
        Returns:
            Ruta relativa del PDF generado
            
        Note:
            El task save_legacy_payment_pdf_task ya tiene url_base configurado
            en website/tasks.py (línea 30)
        """
        try:
            logger.info(f"Generando PDF legacy para factura {invoice_id}")
            
            # Ejecutar tarea de forma síncrona
            # El task espera (invoice_id, data) - NO necesita base_url
            result = save_legacy_payment_pdf_task.apply(
                args=[invoice_id, invoice_data]
            )
            
            if result.successful():
                pdf_path = result.result
                logger.info(f"PDF legacy generado exitosamente: {pdf_path}")
                return pdf_path
            else:
                error_msg = f"Error generando PDF legacy para factura {invoice_id}"
                logger.error(error_msg)
                raise PDFGenerationError(error_msg)
                
        except Exception as e:
            error_msg = f"Error generando PDF legacy para factura {invoice_id}: {str(e)}"
            logger.error(error_msg)
            raise PDFGenerationError(error_msg) from e

