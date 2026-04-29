"""
Schemas de filtros para la API de órdenes de pago.
"""
from datetime import date
from typing import Optional, Literal

from ninja import Schema


class PaymentOrderFilterSchema(Schema):
    """
    Schema para filtros de búsqueda de órdenes de pago.
    """
    # Filtros generales
    search: Optional[str] = None  # Búsqueda por número de orden, estudiante, etc.
    status: Optional[Literal['PENDING', 'PAID', 'VERIFIED', 'CANCELLED']] = None
    order_number: Optional[str] = None

    # Filtros por IDs
    student: Optional[int] = None
    advisor: Optional[int] = None
    opportunity: Optional[int] = None
    quotation: Optional[int] = None

    # Filtros por fechas
    created_from: Optional[date] = None
    created_to: Optional[date] = None

    # Filtros por montos
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None

    # Ordenamiento
    order_by: Optional[str] = '-created_at'  # Por defecto ordenar por más reciente

    # Paginación (opcional, puede manejarse en el endpoint)
    page: int = 1
    per_page: int = 10
