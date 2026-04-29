"""
Interfaz para el servicio de generación de PDFs de pagos.
Abstrae la generación de comprobantes de pago.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class PDFGeneratorServiceInterface(ABC):
    """
    Define el contrato para la generación de PDFs de comprobantes de pago.
    Implementaciones concretas pueden usar diferentes motores de renderizado.
    """

    @abstractmethod
    def generate_payment_pdf(
        self,
        invoice: Any,
        invoice_data: Dict[str, Any]
    ) -> str:
        """
        Genera un PDF de comprobante de pago para una factura nueva.
        
        Args:
            invoice: Objeto Invoice (necesario para guardar el pdf_path)
            invoice_data: Datos estructurados de la factura
            
        Returns:
            Ruta relativa del archivo PDF generado (ej: invoices/invoice_123.pdf)
            
        Note:
            El task ya tiene base_url configurado internamente en billing/tasks.py
            
        Raises:
            PDFGenerationError: Si falla la generación del PDF
        """
        pass

    @abstractmethod
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
            Ruta relativa del archivo PDF generado (ej: planilla_online/planilla_123.pdf)
            
        Note:
            El task ya tiene url_base configurado en website/tasks.py
            
        Raises:
            PDFGenerationError: Si falla la generación del PDF
        """
        pass

