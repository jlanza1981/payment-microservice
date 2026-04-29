import logging
from pathlib import Path
from uuid import uuid4
from typing import Optional, Tuple, Dict, Any

from django.template.loader import render_to_string

from weasyprint import HTML, CSS

from api import settings
from apps.documents.domain.ports.pdf_generator import PDFGenerator

logger = logging.getLogger(__name__)


class PDFGenerationError(Exception):
    """Excepción lanzada cuando falla la generación del PDF"""
    pass


class PDFStorageError(Exception):
    """Excepción lanzada cuando falla el almacenamiento del PDF"""
    pass


class WeasyPrintPDFGenerator(PDFGenerator):
    """
    Generador de PDFs usando WeasyPrint.

    Esta implementación genera PDFs a partir de templates HTML
    con estilos CSS, usando la librería WeasyPrint.
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
        Genera un PDF usando WeasyPrint.
        """
        # Renderizar template HTML con los datos
        logger.info(f" data={data_structure} template_name={template_name}")
        try:
            html_content = render_to_string(template_name, {'data': data_structure})
        except Exception as e:
            logger.error(f"Error al renderizar template {template_name}: {e}")
            raise PDFGenerationError(f"No se pudo renderizar el template: {e}") from e

        # Configurar base_url para recursos estáticos
        if not base_url:
            base_url = str(settings.BASE_DIR)

        # Buscar archivo CSS
        css_path = Path(settings.BASE_DIR) / 'static' / 'css' / css_filename

        # Generar PDF con WeasyPrint
        try:
            html_obj = HTML(string=html_content, base_url=base_url)

            if css_path.exists():
                pdf_content = html_obj.write_pdf(stylesheets=[CSS(str(css_path))])
            else:
                logger.warning(f"Archivo CSS no encontrado: {css_path}. Generando PDF sin estilos.")
                pdf_content = html_obj.write_pdf()

        except Exception as e:
            logger.error(f"Error al generar PDF con WeasyPrint: {e}")
            raise PDFGenerationError(f"WeasyPrint falló al generar el PDF: {e}") from e

        # Determinar ruta de salida
        media_root = Path(settings.MEDIA_ROOT) if settings.MEDIA_ROOT else Path('media')

        if output_path is None:
            # Generar ruta automáticamente
            # Crear nombre de archivo con tipo de documento dinámico
            filename = f"{document_type}_{uuid4().hex}.pdf"

            # Ruta relativa para guardar en BD
            relative_path = Path(folder) / filename

            # Ruta completa en el sistema de archivos
            full_path = media_root / relative_path

            # Crear directorio si no existe
            full_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            # Usar ruta proporcionada
            full_path = Path(output_path)

            # Calcular ruta relativa a MEDIA_ROOT
            try:
                relative_path = full_path.relative_to(media_root)
            except ValueError:
                # Si la ruta no es relativa a MEDIA_ROOT, usar la ruta completa
                relative_path = full_path
                logger.warning(
                    f"La ruta {output_path} no es relativa a MEDIA_ROOT. "
                    f"Se guardará la ruta completa en BD."
                )

        # Guardar archivo en disco
        try:
            with open(full_path, 'wb') as f:
                f.write(pdf_content)
        except IOError as e:
            logger.error(f"Error al guardar PDF en {full_path}: {e}")
            raise PDFStorageError(f"No se pudo guardar el PDF en disco: {e}") from e

        logger.info(
            f"PDF generado exitosamente | "
            f"tipo={document_type} | "
            f"tamaño={len(pdf_content)} bytes | "
            f"ruta={relative_path}"
        )

        # Retornar contenido y ruta RELATIVA (para guardar en BD)
        return pdf_content, str(relative_path)

