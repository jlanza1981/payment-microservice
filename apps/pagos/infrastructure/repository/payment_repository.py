import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List

from django.db import transaction
from django.db.models import QuerySet, F, Value, CharField, Case, When, Sum, Q
from django.db.models.functions import Concat
from django.utils import timezone

from api import settings
from apps.pagos.application.commands import CreatePaymentTransactionCommand
from apps.pagos.application.dto.student_payment_dto import StudentPaymentDTO
from apps.pagos.domain.interface.repository.payment_repository_interface import PaymentRepositoryInterface

from apps.pagos.models import Payment, PaymentAllocation, PaymentTransaction

logger = logging.getLogger(__name__)

class PaymentRepository(PaymentRepositoryInterface):



    def __init__(self):
        super().__init__()

    def get_by_student(self, student_id: int, filters: Dict[str, Any] = None) -> List[StudentPaymentDTO]:
        try:
            payments = Payment.objects.filter(user_id=student_id).select_related("invoice","user").order_by('-created_at')

            if filters:
                payments = self._apply_filters(payments, filters)

            result = []

            for p in payments:
                result.append(
                    StudentPaymentDTO(
                        id=p.id,
                        student_id=p.user.id,
                        amount=p.amount,
                        currency=p.currency,
                        status=p.invoice.get_status_display(),
                        date=p.created_at.strftime('%d/%m/%Y') if p.created_at else '',
                        method=p.get_payment_method_display() if p.payment_method else None,
                        source="new",
                        reference=p.payment_reference_number,
                        invoice_id=p.invoice.id,
                        invoice=p.invoice,
                        invoice_number=p.invoice.invoice_number,
                        file=f'{settings.DOMAIN_NAME}/media{p.invoice.invoice_file}' if p.invoice.invoice_file else None,
                        payer_name=p.payer_name,
                        total=p.invoice.total,
                        amount_paid=p.invoice.get_total_paid(),
                        balance_due=p.invoice.balance_due,
                    )
                )

            return result
        except Exception as e:
            logger.error(
                f"Error obteniendo pagos nuevos por estudiante {student_id}: {str(e)}"
            )
            # En caso de error, retornar lista vacía para no bloquear la operación
            return []

    def list_all(self, filters: Dict[str, Any] = None) -> QuerySet:
        """Lista todos los pagos con filtros opcionales."""
        queryset = Payment.objects.select_related(
            'invoice',
            'invoice__user',
            'user',
            'advisor'
        ).prefetch_related(
            'allocations',
            'allocations__invoice_detail',
            'allocations__payment_concept'
        ).annotate(
            user_name=Concat(
                F('user__nombre'),
                Value(' '),
                F('user__apellido'),
                output_field=CharField()
            ),
            advisor_name=Concat(
                F('advisor__nombre'),
                Value(' '),
                F('advisor__apellido'),
                output_field=CharField()
            ),
            status_display=Case(
                When(status='P', then=Value('Pendiente por verificar')),
                When(status='D', then=Value('Disponible')),
                When(status='V', then=Value('Verificado')),
                When(status='R', then=Value('Rechazado')),
                When(status='X', then=Value('Anulado')),
                default=Value(''),
                output_field=CharField()
            )
        )

        if filters:
            queryset = self._apply_filters(queryset, filters)

        return queryset.order_by('-payment_date')

    def create(
          self,
          payment_data: Dict[str, Any],
          allocations: List[Dict[str, Any]] = None
    ) -> Payment:

        try:
            with transaction.atomic():
                payment = Payment.objects.create(**payment_data)

                if allocations:
                    self._create_payment_allocations(payment, allocations)

                reloaded_payment = self._reload_payment(payment.pk)

                return reloaded_payment

        except Exception as e:
            logger.error(f"Error al crear factura: {str(e)}")
            raise

    def update(self, payment_id: int, payment_data: Dict[str, Any]) -> Payment:
        try:
            with transaction.atomic():
                payment = self.get_by_id(payment_id)

                # Validar que el pago no esté anulado
                if payment.status == 'X':
                    raise ValueError(
                        f"El pago {payment.payment_number} no se puede actualizar "
                        f"(estado: Anulado)"
                    )

                # Separar allocations antes de convertir
                allocations = payment_data.pop('allocations', None)

                # Actualizar campos básicos
                for key, value in payment_data.items():
                    if hasattr(payment, key):
                        setattr(payment, key, value)

                payment.save()

                # Actualizar asignaciones si vienen en los datos
                if allocations is not None:
                    payment.allocations.all().delete()
                    self._create_payment_allocations(payment, allocations)

                return self._reload_payment(payment.pk)

        except Exception as e:
            logger.error(f"Error al actualizar la factura: {str(e)}")
            raise

    def cancel(self, payment_id: int) -> bool:
        """ Anula un pago  """
        try:
            with transaction.atomic():
                payment = self.get_by_id(payment_id)

                # Validar que el pago no esté ya anulado
                if payment.status == 'X':
                    raise ValueError(f"El pago {payment.payment_number} ya está anulado")

                # Cambiar estado a Anulado
                payment.status = 'X'
                payment.save(update_fields=['status', 'updated_at'])
                return True

        except Payment.DoesNotExist:
            return False

    def verify(self, payment_id: int, verification_date: Any = None) -> Payment:
        """
        Verifica un pago por tesorería.
        """
        with transaction.atomic():
            payment = Payment.objects.get(pk=payment_id)
            payment.verify()
            return self._reload_payment(payment.pk)

    def reject(self, payment_id: int) -> Payment:
        """
        Rechaza un pago.

        Args:
            payment_id: ID del pago a rechazar

        Returns:
            Payment: Pago rechazado
        """
        with transaction.atomic():
            payment = Payment.objects.get(pk=payment_id)

            # Validar que el pago esté pendiente
            if payment.status not in ['P', 'D']:
                raise ValueError(
                    f"El pago {payment.payment_number} no se puede rechazar "
                    f"(estado actual: {payment.get_status_display()})"
                )

            payment.status = 'R'
            payment.save(update_fields=['status', 'updated_at'])

            return self._reload_payment(payment.pk)

    def get_by_id(self, payment_id: int) -> Optional[Payment]:
        """Obtiene un pago por ID con relaciones básicas."""
        return Payment.objects.select_related(
            'invoice',
            'invoice__user',
            'user',
            'advisor'
        ).prefetch_related(
            'allocations',
            'allocations__invoice_detail',
            'allocations__payment_concept'
        ).filter(pk=payment_id).first()

    def get_by_payment_number(self, payment_number: str) -> Optional[Payment]:
        """Obtiene un pago por su número de pago."""
        return Payment.objects.select_related(
            'invoice',
            'user',
            'advisor'
        ).prefetch_related(
            'allocations'
        ).filter(payment_number=payment_number).first()

    def get_by_id_with_relations(self, payment_id: int) -> Optional[Payment]:
        """Obtiene un pago con todas sus relaciones cargadas."""
        return Payment.objects.select_related(
            'invoice',
            'invoice__user',
            'invoice__advisor',
            'invoice__payment_order',
            'user',
            'advisor'
        ).prefetch_related(
            'allocations',
            'allocations__invoice_detail',
            'allocations__invoice_detail__payment_concept',
            'allocations__payment_concept'
        ).filter(pk=payment_id).first()

    def save_payment(self, payment: Payment, update_fields: List[str] = None) -> Payment:

        if update_fields:
            payment.save(update_fields=update_fields)
        else:
            payment.save()
        return payment

    def get_payments_by_invoice(self, invoice_id: int) -> List[Payment]:
        """Obtiene todos los pagos de una factura."""
        return list(
            Payment.objects.select_related(
                'user',
                'advisor'
            ).prefetch_related(
                'allocations'
            ).filter(invoice_id=invoice_id).order_by('-payment_date')
        )

    def get_payments_by_user(self, user_id: int) -> List[Payment]:
        """Obtiene todos los pagos de un usuario."""
        return list(
            Payment.objects.select_related(
                'invoice',
                'advisor'
            ).prefetch_related(
                'allocations'
            ).filter(user_id=user_id).order_by('-payment_date')
        )

    def get_pending_payments_by_user(self, user_id: int) -> List[Payment]:
        """Obtiene pagos pendientes de verificación de un usuario."""
        return list(
            Payment.objects.select_related(
                'invoice',
                'advisor'
            ).prefetch_related(
                'allocations'
            ).filter(
                user_id=user_id,
                status='P'
            ).order_by('-payment_date')
        )

    def get_verified_payments_by_invoice(self, invoice_id: int) -> List[Payment]:
        """Obtiene pagos verificados de una factura."""
        return list(
            Payment.objects.select_related(
                'user',
                'advisor'
            ).prefetch_related(
                'allocations'
            ).filter(
                invoice_id=invoice_id,
                status='V'
            ).order_by('-payment_date')
        )

    def calculate_total_payments_by_invoice(self, invoice_id: int) -> Decimal:
        """Calcula el total de pagos verificados de una factura."""
        result = Payment.objects.filter(
            invoice_id=invoice_id,
            status='V'
        ).aggregate(
            total=Sum('amount')
        )
        return result['total'] or Decimal('0.00')

    def get_payments_by_date_range(
          self,
          start_date: Any,
          end_date: Any,
          status: str = None
    ) -> List[Payment]:
        """Obtiene pagos en un rango de fechas con estado opcional."""
        queryset = Payment.objects.select_related(
            'invoice',
            'user',
            'advisor'
        ).prefetch_related(
            'allocations'
        ).filter(
            payment_date__gte=start_date,
            payment_date__lte=end_date
        )

        if status:
            queryset = queryset.filter(status=status)

        return list(queryset.order_by('-payment_date'))

    def get_payments_by_advisor(self, advisor_id: int) -> List[Payment]:
        """Obtiene todos los pagos gestionados por un asesor."""
        return list(
            Payment.objects.select_related(
                'invoice',
                'user'
            ).prefetch_related(
                'allocations'
            ).filter(advisor_id=advisor_id).order_by('-payment_date')
        )

    def get_payment_allocations_by_payment(self, payment_id: int) -> List[PaymentAllocation]:
        """Obtiene todas las asignaciones de un pago."""
        return list(
            PaymentAllocation.objects.select_related(
                'payment',
                'invoice_detail',
                'invoice_detail__payment_concept',
                'concept'
            ).filter(payment_id=payment_id).order_by('created_at')
        )

    def get_payment_transaction(self, paypal_order_id: str, payment_order_id: int) -> PaymentTransaction:
        response = PaymentTransaction.objects.filter(paypal_order_id=paypal_order_id, payment_order_id=payment_order_id).first()
        return response

    def save_payment_transaction(self, payload:CreatePaymentTransactionCommand) -> PaymentTransaction:

        response = PaymentTransaction.objects.create(
            payment_order=payload.payment_order,
            payment_id=payload.payment if payload.payment else None,
            paypal_order_id=payload.paypal_order_id,
            amount=payload.amount,
            currency=payload.currency,
            status=payload.status,
            gross_amount=payload.gross_amount,
            paypal_fee=payload.paypal_fee,
            net_amount=payload.net_amount,
            payee_email=payload.payee_email,
            payee_merchant_id=payload.payee_merchant_id,
            resource_json=payload.resource_json,
        )
        return response

    def update_payment_transaction(self, payment_transaction: PaymentTransaction, update_fields: List[str] = None) -> PaymentTransaction:
        payment_transaction.save(update_fields=update_fields)
        return payment_transaction



    # MÉTODOS PRIVADOS DE UTILIDAD
    # ==========================================
    @staticmethod
    def _create_payment_allocations(payment: Payment, allocations: List[Dict[str, Any]]) -> None:
        allocation_objects = []
        for allocation_data in allocations:
            allocation_kwargs = allocation_data.copy()
            allocation_kwargs['payment'] = payment
            allocation_objects.append(PaymentAllocation(**allocation_kwargs))

        if allocation_objects:
            PaymentAllocation.objects.bulk_create(allocation_objects)

    def _reload_payment(self, payment_id: int) -> Payment:
        """Recarga un pago con todas sus relaciones."""
        return self.get_by_id_with_relations(payment_id)

    @staticmethod
    def _apply_filters(queryset: QuerySet, filters: Dict[str, Any]) -> QuerySet:

        if 'invoice_number' in filters:
            queryset = queryset.filter(invoice__invoice_number=filters['invoice_number'])

        if 'user' in filters:
            queryset = queryset.filter(user_id=filters['user'])

        if 'advisor' in filters:
            queryset = queryset.filter(advisor_id=filters['advisor'])

        if 'payment_method' in filters:
            queryset = queryset.filter(payment_method=filters['payment_method'])

        if 'created_from' in filters:
            queryset = queryset.filter(created_at__gte=filters['created_from'])

        if 'created_to' in filters:
            queryset = queryset.filter(created_at__lte=filters['created_to'])

        if 'min_amount' in filters:
            queryset = queryset.filter(amount__gte=filters['min_amount'])

        if 'max_amount' in filters:
            queryset = queryset.filter(amount__lte=filters['max_amount'])

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
