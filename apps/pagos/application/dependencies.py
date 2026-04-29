"""
Configuración de inyección de dependencias para servicios de pagos.

Este módulo centraliza la creación e inyección de dependencias siguiendo
los principios de arquitectura hexagonal y DDD.
"""
from apps.pagos.application.services.payment_history_service import PaymentHistoryService
from apps.pagos.application.services.payment_pdf_service import PaymentPDFService
from apps.pagos.infrastructure.repository.payment_repository import PaymentRepository
from apps.pagos.infrastructure.repository.legacy_payment_repository import LegacyPaymentRepository
from apps.pagos.infrastructure.services.local_file_storage_service import LocalFileStorageService
from apps.pagos.infrastructure.services.celery_pdf_generator_service import CeleryPDFGeneratorService


def get_payment_repository() -> PaymentRepository:
    """
    Obtiene una instancia del repositorio de pagos.
    
    Returns:
        Instancia configurada de PaymentRepository
    """
    return PaymentRepository()


def get_legacy_payment_repository() -> LegacyPaymentRepository:
    """
    Obtiene una instancia del repositorio de pagos legacy.
    
    Returns:
        Instancia configurada de LegacyPaymentRepository
    """
    return LegacyPaymentRepository()


def get_file_storage_service() -> LocalFileStorageService:
    """
    Obtiene una instancia del servicio de almacenamiento de archivos.
    
    Returns:
        Instancia configurada de LocalFileStorageService
    """
    return LocalFileStorageService()


def get_pdf_generator_service() -> CeleryPDFGeneratorService:
    """
    Obtiene una instancia del servicio de generación de PDFs.
    
    Returns:
        Instancia configurada de CeleryPDFGeneratorService
    """
    return CeleryPDFGeneratorService()


def get_payment_pdf_service() -> PaymentPDFService:
    """
    Obtiene una instancia del servicio de gestión de PDFs de pagos.
    
    Returns:
        Instancia configurada de PaymentPDFService con todas sus dependencias
    """
    file_storage_service = get_file_storage_service()
    pdf_generator_service = get_pdf_generator_service()
    
    return PaymentPDFService(
        file_storage_service=file_storage_service,
        pdf_generator_service=pdf_generator_service
    )


def get_payment_history_service() -> PaymentHistoryService:
    """
    Obtiene una instancia del servicio de historial de pagos.
    
    Esta es la función principal para obtener el servicio completo
    con todas sus dependencias correctamente configuradas.
    
    Returns:
        Instancia configurada de PaymentHistoryService
    """
    payment_repository = get_payment_repository()
    legacy_payment_repository = get_legacy_payment_repository()
    payment_pdf_service = get_payment_pdf_service()
    
    return PaymentHistoryService(
        payment_repository=payment_repository,
        legacy_payment_repository=legacy_payment_repository,
        payment_pdf_service=payment_pdf_service
    )

