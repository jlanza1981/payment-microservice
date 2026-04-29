from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from apps.orden_pagos.models import PaymentOrder


class PaymentOrderRepositoryInterface(ABC):
    """
    Repositorio abstracto para PaymentOrder.
    Define el contrato de operaciones sin implementar cómo se hacen.
    """

    @abstractmethod
    def get_by_student(self, student_id: int, filters: Dict[str, Any] = None) -> List['PaymentOrder']:
        pass

    @abstractmethod
    def list_all(self, filters: dict = None) -> List['PaymentOrder']:
        """Listar órdenes de pago con filtros opcionales"""
        pass

    @abstractmethod
    def create(
          self,
          order_data: dict,
          payment_details: list,
          program_data: dict
    ) -> 'PaymentOrder':
        pass

    @abstractmethod
    def update(self, order_id: int, payment_order_data: dict) -> 'PaymentOrder':
        """Actualizar una orden de pago existente"""
        pass

    @abstractmethod
    def cancel(self, order_id: int) -> bool:
        pass

    @abstractmethod
    def get_by_id(self, order_id: int) -> Optional['PaymentOrder']:
        """Obtener orden de pago por ID"""
        pass

    @abstractmethod
    def get_by_order_number(self, order_number: str) -> Optional['PaymentOrder']:
        """Obtener orden de pago por número de orden"""
        pass

    @abstractmethod
    def get_by_id_with_relations(self, order_id: int) -> Optional['PaymentOrder']:
        """Obtener orden de pago por ID con todas sus relaciones cargadas"""
        pass

    @abstractmethod
    def save_order(self, payment_order: 'PaymentOrder', update_fields: list = None) -> 'PaymentOrder':
        """Guardar una instancia de PaymentOrder con campos específicos"""
        pass

    @abstractmethod
    def get_payment_order_by_token(self, token: str) -> Optional['PaymentOrder']:
        """Obtener orden de pago por número de orden"""
        pass

    @abstractmethod
    def generate_token(self, payment_order: 'PaymentOrder') -> str:
        """Obtener orden de pago por número de orden"""
        pass
