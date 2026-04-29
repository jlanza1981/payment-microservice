"""
Interfaz para el servicio de almacenamiento de archivos.
Abstrae las operaciones de verificación y obtención de archivos.
"""
from abc import ABC, abstractmethod
from typing import Optional


class FileStorageServiceInterface(ABC):
    """
    Define el contrato para operaciones de almacenamiento de archivos.
    Implementaciones concretas pueden usar filesystem local, S3, etc.
    """

    @abstractmethod
    def exists(self, file_path: str) -> bool:
        """
        Verifica si un archivo existe.
        
        Args:
            file_path: Ruta relativa del archivo
            
        Returns:
            True si el archivo existe, False en caso contrario
        """
        pass

    @abstractmethod
    def get_absolute_path(self, file_path: str) -> Optional[str]:
        """
        Obtiene la ruta absoluta de un archivo.
        
        Args:
            file_path: Ruta relativa del archivo
            
        Returns:
            Ruta absoluta del archivo si existe, None en caso contrario
        """
        pass

