"""
Implementación del servicio de almacenamiento de archivos usando filesystem local.

Maneja diferentes tipos de entrada:
- str: Ruta como string
- Path: Objeto Path de pathlib
- FieldFile: Campo de archivo de Django
"""
import logging
from pathlib import Path
from typing import Optional

from django.conf import settings

from apps.pagos.domain.interface.services.file_storage_service_interface import FileStorageServiceInterface

logger = logging.getLogger(__name__)


class LocalFileStorageService(FileStorageServiceInterface):
    """
    Implementación del servicio de almacenamiento usando el filesystem local.
    Utiliza MEDIA_ROOT de Django como directorio base.
    """

    def __init__(self, base_path: Optional[str] = None):
        """
        Inicializa el servicio con el path base.
        
        Args:
            base_path: Path base para archivos. Si es None, usa settings.MEDIA_ROOT
        """
        self.base_path = Path(base_path) if base_path else Path(settings.MEDIA_ROOT)

    def exists(self, file_path) -> bool:
        """
        Verifica si un archivo existe en el sistema de archivos.
        """
        try:
            # Convertir a string manejando diferentes tipos
            if file_path is None:
                return False
            
            # Si es un FieldFile de Django, obtener el name
            if hasattr(file_path, 'name'):
                file_path_str = str(file_path.name) if file_path.name else None
            # Si es un Path, convertir a string
            elif isinstance(file_path, Path):
                file_path_str = str(file_path)
            # Si ya es string
            else:
                file_path_str = str(file_path)
            
            # Si después de convertir es None o vacío, no existe
            if not file_path_str:
                return False
            
            # Eliminar barra inicial si existe (importante!)
            file_path_str = file_path_str.lstrip('/')
            
            # Construir path completo y verificar
            full_path = self.base_path / file_path_str
            exists = full_path.exists() and full_path.is_file()
            
            if not exists:
                logger.debug(f"Archivo no encontrado: {file_path_str} (full path: {full_path})")
            else:
                logger.debug(f"Archivo encontrado: {file_path_str}")
            
            return exists
        except Exception as e:
            logger.error(f"Error verificando existencia de archivo {file_path}: {str(e)}")
            return False

    def get_absolute_path(self, file_path) -> Optional[str]:
        """
        Obtiene la ruta absoluta de un archivo si existe.
        
        Args:
            file_path: Ruta del archivo (str, Path, o FieldFile de Django)
            
        Returns:
            Ruta absoluta del archivo si existe, None en caso contrario
        """
        try:
            # Convertir a string manejando diferentes tipos
            if file_path is None:
                return None
            
            # Si es un FieldFile de Django, obtener el name
            if hasattr(file_path, 'name'):
                file_path_str = str(file_path.name) if file_path.name else None
            # Si es un Path, convertir a string
            elif isinstance(file_path, Path):
                file_path_str = str(file_path)
            # Si ya es string
            else:
                file_path_str = str(file_path)
            
            # Si después de convertir es None o vacío
            if not file_path_str:
                return None
            
            # Eliminar barra inicial si existe (importante!)
            # /planilla_online/46.pdf -> planilla_online/46.pdf
            file_path_str = file_path_str.lstrip('/')
            
            # Construir path completo y verificar
            full_path = self.base_path / file_path_str
            
            if full_path.exists() and full_path.is_file():
                return str(full_path)
            
            return None
        except Exception as e:
            logger.error(f"Error obteniendo ruta absoluta de {file_path}: {str(e)}")
            return None

