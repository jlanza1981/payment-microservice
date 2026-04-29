from dataclasses import dataclass
from typing import Optional


@dataclass
class GetPaymentOrderQuery:
    """
    Query para obtener una orden de pago por ID.
    """
    order_id: int


@dataclass
class GetPaymentOrderByNumberQuery:
    """
    Query para obtener una orden de pago por número de orden.
    """
    order_number: str


@dataclass
class ListPaymentOrdersQuery:
    """
    Query para listar órdenes de pago con filtros.
    """
    status: Optional[str] = None
    student_id: Optional[int] = None
    advisor_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    quotation_id: Optional[int] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None

