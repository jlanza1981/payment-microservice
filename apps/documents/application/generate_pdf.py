from typing import Tuple, Optional, Dict, Any

from apps.documents.domain.ports.pdf_generator import PDFGenerator

class GeneratePDFUseCase:
    """
    Caso de uso para generar documentos PDF.
    Este caso de uso orquesta la generación de PDFs usando
    el generador de PDF inyectado.
    """

    def __init__(self, pdf_generator: PDFGenerator):
        self.pdf_generator = pdf_generator

    def execute(
        self,
        data_structure: Dict[str, Any],
        template_name: str,
        css_filename: str,
        folder: str,
        document_type: str = "document",
        output_path: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> Tuple[bytes, str]:

        return self.pdf_generator.generate_pdf(
            data_structure=data_structure,
            template_name=template_name,
            css_filename=css_filename,
            folder=folder,
            document_type=document_type,
            output_path=output_path,
            base_url=base_url
        )