from typing import Protocol, Tuple, Optional, Dict, Any


class PDFGenerator(Protocol):
    """
    Puerto de salida: define cómo generar PDFs.
    """
    def generate_pdf(
        self,
        data_structure: Dict[str, Any],
        template_name: str,
        css_filename: str,
        folder: str,
        document_type: str = "document",
        output_path: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> Tuple[bytes, str]:
        """
        Args:
            data_structure: Datos para renderizar en la plantilla
            template_name: Ruta de la plantilla HTML (ej: 'payments/payment_order.html')
            css_filename: Nombre del archivo CSS (ej: 'payment_order.css')
            folder: Carpeta donde guardar el PDF (ej: 'payment_orders')
            document_type: Tipo de documento para el nombre del archivo (ej: 'invoice', 'receipt')
            output_path: Ruta de salida opcional (si no se provee, se genera automáticamente)
            base_url: URL base para resolver recursos estáticos

        Returns:
            Tuple[bytes, str]: Contenido del PDF en bytes y ruta relativa del archivo
        """
        ...