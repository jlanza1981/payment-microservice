from abc import ABC, abstractmethod
from decimal import Decimal
from typing import List, Optional, Dict, Any

from apps.pagos.application.commands import CreatePaymentTransactionCommand
from apps.pagos.application.dto.student_payment_dto import StudentPaymentDTO
from apps.pagos.models import Payment, PaymentAllocation, PaymentTransaction


class PaymentRepositoryInterface(ABC):
    """
    Repositorio abstracto para Payment.
    Define el contrato de operaciones sin implementar cómo se hacen.
    """

    @abstractmethod
    def list_all(self, filters: Dict[str, Any] = None) -> List['Payment']:
        """Listar pagos con filtros opcionales"""
        pass

    @abstractmethod
    def create(
          self,
          payment_data: Dict[str, Any],
          allocations: List[Dict[str, Any]] = None
    ) -> 'Payment':
        """
        Crear un nuevo pago con sus asignaciones opcionales.
        """
        pass

    @abstractmethod
    def update(self, payment_id: int, payment_data: Dict[str, Any]) -> 'Payment':
        """Actualizar un pago existente"""
        pass

    @abstractmethod
    def cancel(self, payment_id: int) -> bool:
        """Anular un pago"""
        pass

    @abstractmethod
    def verify(self, payment_id: int, verification_date: Any = None) -> 'Payment':
        """Verificar un pago por tesorería"""
        pass

    @abstractmethod
    def reject(self, payment_id: int) -> 'Payment':
        """Rechazar un pago"""
        pass

    @abstractmethod
    def get_by_id(self, payment_id: int) -> Optional['Payment']:
        """Obtener pago por ID"""
        pass

    @abstractmethod
    def get_by_payment_number(self, payment_number: str) -> Optional['Payment']:
        """Obtener pago por número de pago"""
        pass

    @abstractmethod
    def get_by_id_with_relations(self, payment_id: int) -> Optional['Payment']:
        """Obtener pago por ID con todas sus relaciones cargadas"""
        pass

    @abstractmethod
    def save_payment(self, payment: 'Payment', update_fields: List[str] = None) -> 'Payment':
        """
        Guardar una instancia de Payment con campos específicos.
        """
        pass

    @abstractmethod
    def get_payments_by_invoice(self, invoice_id: int) -> List['Payment']:
        """Obtener todos los pagos de una factura"""
        pass

    @abstractmethod
    def get_payments_by_user(self, user_id: int) -> List['Payment']:
        """Obtener todos los pagos de un usuario"""
        pass

    @abstractmethod
    def get_pending_payments_by_user(self, user_id: int) -> List['Payment']:
        """Obtener pagos pendientes de verificación de un usuario"""
        pass

    @abstractmethod
    def get_verified_payments_by_invoice(self, invoice_id: int) -> List['Payment']:
        """Obtener pagos verificados de una factura"""
        pass

    @abstractmethod
    def calculate_total_payments_by_invoice(self, invoice_id: int) -> Decimal:
        """Calcular total de pagos verificados de una factura"""
        pass

    @abstractmethod
    def get_payments_by_date_range(
          self,
          start_date: Any,
          end_date: Any,
          status: str = None
    ) -> List['Payment']:
        """Obtener pagos en un rango de fechas con estado opcional"""
        pass

    @abstractmethod
    def get_payments_by_advisor(self, advisor_id: int) -> List['Payment']:
        """Obtener todos los pagos gestionados por un asesor"""
        pass

    @abstractmethod
    def get_payment_allocations_by_payment(self, payment_id: int) -> List['PaymentAllocation']:
        """Obtener todas las asignaciones de un pago"""
        pass

    def save_payment_transaction(self, payload: CreatePaymentTransactionCommand, ) -> PaymentTransaction:
        """Guardar la transacción de pago con el ID de orden de PayPal"""
        pass

    def update_payment_transaction(self, payment_transaction: PaymentTransaction, update_fields: List[str] = None) -> 'PaymentTransaction':
        pass

    def get_payment_transaction(self, paypal_order_id:str, payment_order_id: int) -> PaymentTransaction:
        """Obtener pago por ID con todas sus relaciones cargadas"""
        pass

    @abstractmethod
    def get_by_student(self, student_id: int, filters: Dict[str, Any] = None) -> List[StudentPaymentDTO]:
        pass
