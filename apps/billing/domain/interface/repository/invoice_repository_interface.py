from abc import ABC, abstractmethod
from decimal import Decimal
from typing import List, Optional, Dict, Any

from apps.billing.application.commands import CreatePaymentReceiptCommand
from apps.billing.models import InvoiceCreditDetail
from apps.pagos.models import Payment

class InvoiceRepositoryInterface(ABC):
    """
    Repositorio abstracto para Invoice.
    Define el contrato de operaciones sin implementar cómo se hacen.
    """

    @abstractmethod
    def list_all(self, filters: Dict[str, Any] = None) -> List['Invoice']:
        """Listar facturas con filtros opcionales"""
        pass

    @abstractmethod
    def create(
          self,
          invoice_data: Dict[str, Any],
          invoice_details: List[Dict[str, Any]]
    ) -> 'Invoice':
        """
        Crear una nueva factura con sus detalles.

        Args:
            invoice_data: Datos de la factura (student, advisor, payment_order, etc.)
            invoice_details: Lista de detalles de la factura (conceptos de pago)

        Returns:
            Invoice: Factura creada
        """
        pass

    @abstractmethod
    def update(self, invoice_id: int, invoice_data: Dict[str, Any]) -> 'Invoice':
        """Actualizar una factura existente"""
        pass

    @abstractmethod
    def cancel(self, invoice_id: int) -> bool:
        """Anular una factura"""
        pass

    @abstractmethod
    def get_by_id(self, invoice_id: int) -> Optional['Invoice']:
        """Obtener factura por ID"""
        pass

    @abstractmethod
    def get_by_invoice_number(self, invoice_number: str) -> Optional['Invoice']:
        """Obtener factura por número de factura"""
        pass

    @abstractmethod
    def get_by_id_with_relations(self, invoice_id: int) -> Optional['Invoice']:
        """Obtener factura por ID con todas sus relaciones cargadas"""
        pass

    @abstractmethod
    def save_invoice(self, invoice: 'Invoice', update_fields: List[str] = None) -> 'Invoice':
        """
        Guardar una instancia de Invoice con campos específicos.

        Args:
            invoice: Instancia de Invoice a guardar
            update_fields: Lista de campos a actualizar (opcional)

        Returns:
            Invoice: Instancia actualizada
        """
        pass

    @abstractmethod
    def get_invoices_by_student(self, student_id: int) -> List['Invoice']:
        """Obtener todas las facturas de un estudiante"""
        pass

    @abstractmethod
    def get_invoices_by_payment_order(self, payment_order_id: int) -> Optional['Invoice']:
        """Obtener  factura de una orden de pago"""
        pass

    @abstractmethod
    def get_pending_invoices_by_student(self, student_id: int) -> List['Invoice']:
        """Obtener facturas pendientes de un estudiante"""
        pass

    @abstractmethod
    def calculate_student_total_debt(self, student_id: int) -> Decimal:
        """Calcular deuda total de un estudiante"""
        pass

    @abstractmethod
    def link_receipt_to_credit_detail(self, invoice, payment, payment_receipt):
        """
        Vincula un PaymentReceipt con el InvoiceCreditDetail correspondiente.

        Este método busca el InvoiceCreditDetail que se creó previamente
        (con payment_receipt=None) y lo vincula con el recibo recién creado.

        Args:
            invoice: Factura asociada
            payment: Pago asociado
            payment_receipt: Recibo de pago a vincular

        Returns:
            InvoiceCreditDetail: Registro actualizado o None si no se encontró
        """
        pass

    @abstractmethod
    def calculate_receipt_balances(self, invoice, payment_amount):
        """
        Calcula los balances para un recibo de pago.

        Args:
            invoice: Factura (ya actualizada con el nuevo balance)
            payment_amount: Monto del pago realizado

        Returns:
            tuple: (previous_balance, new_balance)
        """
        pass

    @abstractmethod
    def create_payment_receipt(self, receipt_data:CreatePaymentReceiptCommand):
        """
        Crea un PaymentReceipt para un abono.
        """
        pass

    @abstractmethod
    def get_payment_receipt_by_id(self, payment_receipt_id:int)-> 'PaymentReceipt':
        """
        obtiene un PaymentReceipt por id.
        """
        pass

    def create_invoice_credit_detail(self, payment: Payment, invoice, payment_receipt)->'InvoiceCreditDetail':
        """
        Crea un InvoiceCreditDetail para un abono.
        """
        pass
    def update_credit_invoice_payment_receipt(self, invoice_credit_detail: 'InvoiceCreditDetail', payment_receipt, update_fields: List[str])-> 'InvoiceCreditDetail':
        """
        Guarda un InvoiceCreditDetail con campos específicos.
        """
        pass

    @abstractmethod
    def get_already_applied_allocations(self, invoice_detail_id: int):
        """
        Obtiene todos los PaymentAllocation aplicados a un invoice_detail.
        
        Args:
            invoice_detail_id: ID del detalle de factura
            
        Returns:
            QuerySet de PaymentAllocation con relación a payment cargada
            
        Note:
            - Retorna las instancias completas para evaluar status individualmente
            - Solo considera pagos con status 'D' (Disponible) o 'V' (Verificado)
            - Permite al caso de uso verificar duplicados por status y payment_id
            - Incluye select_related('payment') para acceder a payment.status sin queries extra
        """
        pass

