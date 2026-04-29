import logging
from decimal import Decimal
from typing import Dict, Any, List, Optional

from django.db.models import Q, QuerySet

from api import settings
from apps.pagos.application.dto.student_payment_dto import StudentPaymentDTO
from apps.pagos.domain.interface.repository.payment_repository_interface import PaymentRepositoryInterface
from apps.website.models import PagosEnLinea

logger = logging.getLogger(__name__)

class LegacyPaymentRepository(PaymentRepositoryInterface):
    def get_by_student(self, student_id: int, filters: Dict[str, Any] = None) -> List[StudentPaymentDTO]:
        try:
            payments = (
                PagosEnLinea.objects
                .filter(usuario_id=student_id)
                .select_related("planilla", "usuario")
            )
            if filters:
                payments = self._apply_filters(payments, filters)

            payment_methods_dict = dict(PagosEnLinea.PAYMENT_METHODS)
            result = []
            payment_method = payment_methods_dict.get('PP', 'PayPal')
            for p in payments:
                result.append(
                    StudentPaymentDTO(
                        id=p.id,
                        invoice_id=p.planilla.id,
                        invoice=p.planilla,
                        status=p.get_estatus_display(),
                        invoice_number=str(p.planilla.id),
                        student_id=p.usuario.id,
                        amount=p.monto_pagado,
                        currency=p.moneda,
                        date=p.created_at.strftime('%d/%m/%Y') if p.created_at else '',
                        method=payment_method,
                        source="legacy",
                        reference=p.id_paypal,
                        file=p.planilla.archivo if p.planilla.archivo else None,
                        payer_name=p.nombre_pagador,
                        total=Decimal('0.00'),
                        amount_paid=Decimal('0.00'),
                        balance_due=Decimal('0.00'),
                    )
                )

            return result
        except Exception as e:
            logger.error(
                f"Error obteniendo pagos legacy para estudiante {student_id}: {str(e)}"
            )
            # En caso de error, retornar lista vacía para no bloquear la operación
            return []

    def list_all(self, filters: Dict[str, Any] = None) -> List['PagosEnLinea']:
        pass
    def create(self, payment_data: Dict[str, Any], allocations: List[Dict[str, Any]] = None) -> 'PagosEnLinea':
        pass

    def update(self, payment_id: int, payment_data: Dict[str, Any]) -> 'PagosEnLinea':
        pass

    def cancel(self, payment_id: int) -> bool:
        pass

    def verify(self, payment_id: int, verification_date: Any = None) -> 'PagosEnLinea':
        pass

    def reject(self, payment_id: int) -> 'PagosEnLinea':
        pass

    def get_by_id(self, payment_id: int) -> Optional['PagosEnLinea']:
        pass

    def get_by_payment_number(self, payment_number: str) -> Optional['PagosEnLinea']:
        pass

    def get_by_id_with_relations(self, payment_id: int) -> Optional['PagosEnLinea']:
        pass

    def save_payment(self, payment: 'PagosEnLinea', update_fields: List[str] = None) -> 'PagosEnLinea':
        pass

    def get_payments_by_invoice(self, invoice_id: int) -> List['PagosEnLinea']:
        pass

    def get_payments_by_user(self, user_id: int) -> List['PagosEnLinea']:
        pass

    def get_pending_payments_by_user(self, user_id: int) -> List['PagosEnLinea']:
        pass

    def get_verified_payments_by_invoice(self, invoice_id: int) -> List['PagosEnLinea']:
        pass

    def calculate_total_payments_by_invoice(self, invoice_id: int) -> Decimal:
        pass

    def get_payments_by_date_range(self, start_date: Any, end_date: Any, status: str = None) -> List['PagosEnLinea']:
        pass

    def get_payments_by_advisor(self, advisor_id: int) -> List['PagosEnLinea']:
        pass

    def get_payment_allocations_by_payment(self, payment_id: int) -> List['PagosEnLinea']:
        pass


    @staticmethod
    def _apply_filters(queryset: QuerySet, filters: Dict[str, Any]) -> QuerySet:
        if 'invoice_number' in filters:
            queryset = queryset.filter(id=int(filters['invoice_number']))

        if 'user' in filters:
            queryset = queryset.filter(usuario_id=filters['user'])

        if 'created_from' in filters:
            queryset = queryset.filter(created_at__gte=filters['created_from'])

        if 'created_to' in filters:
            queryset = queryset.filter(created_at__lte=filters['created_to'])

        if 'min_amount' in filters:
            queryset = queryset.filter(monto_pagado__gte=filters['min_amount'])

        if 'max_amount' in filters:
            queryset = queryset.filter(monto_pagado__lte=filters['max_amount'])

        if 'search' in filters:
            search_term = filters['search']
            queryset = queryset.filter(
                Q(payment_number__icontains=search_term) |
                Q(payment_reference_number__icontains=search_term) |
                Q(payer_name__icontains=search_term) |
                Q(user__nombre__icontains=search_term) |
                Q(user__apellido__icontains=search_term)
            )

        return queryset
