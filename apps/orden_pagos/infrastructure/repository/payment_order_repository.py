import logging
from decimal import Decimal
from typing import Optional, Dict, Any

from django.db import transaction
from django.db.models import QuerySet, F, Value, CharField, Case, When, Count
from django.db.models.functions import Concat
from apps.orden_pagos.domain.interface.repository.repository_interface import PaymentOrderRepositoryInterface
from apps.orden_pagos.infrastructure.services.payment_token_service import PaymentTokenService
from apps.orden_pagos.models import (
    PaymentOrder,
    PaymentOrderDetails,
    PaymentOrderProgram,
)

logger = logging.getLogger(__name__)

class PaymentOrderRepository(PaymentOrderRepositoryInterface):
    def __init__(self):
        super().__init__()
    def get_by_student(self, student_id: int, filters: Dict[str, Any] = None) -> QuerySet:
        queryset = (PaymentOrder.objects.select_related(
            'student',
            'advisor',
            'opportunity',
            'quotation'
        ).prefetch_related(
            'payment_order_details',
            'payment_order_program'
        ).filter(student_id=student_id))

        queryset = (queryset.annotate(
            credit_amount=F('suggested_payment_amount'),
            archivo=F('payment_order_file'),
            student_name=Concat(F('student__nombre'), Value(' '), F('student__apellido'), output_field=CharField()),
            advisor_name=Concat(F('advisor__nombre'), Value(' '), F('advisor__apellido'), output_field=CharField()),
            status_display=Case(
                When(status='PENDING', then=Value('Pendiente de pago')),
                When(status='PAID', then=Value('Pagado')),
                When(status='VERIFIED', then=Value('Verificado por Tesorería')),
                When(status='CANCELLED', then=Value('Cancelado')),
                When(status='ACTIVE', then=Value('Activa - En proceso de pago')),
                default=Value(''),
                output_field=CharField()
            ),
            details_count=Count('payment_order_details')
        ))
        queryset.values(
            'id', 'order_number',
            'student', 'advisor',
            'status', 'status_display',
            'student_name', 'advisor_name',
            'total_order', 'details_count', 'credit_amount', 'archivo'
        )
        if not filters:
            return queryset.order_by('-created_at')

        queryset = self._apply_filters(queryset, filters)

        return queryset.order_by('-created_at')

    def list_all(self, filters: Dict[str, Any] = None) -> QuerySet:
        queryset = PaymentOrder.objects.select_related(
            'student',
            'advisor',
            'opportunity',
            'quotation'
        ).prefetch_related(
            'payment_order_details',
            'payment_order_program'
        ).annotate(
            credit_amount=F('suggested_payment_amount'),
            archivo=F('payment_order_file'),
            student_name=Concat(F('student__nombre'), Value(' '), F('student__apellido'), output_field=CharField()),
            advisor_name=Concat(F('advisor__nombre'), Value(' '), F('advisor__apellido'), output_field=CharField()),
            status_display=Case(
                When(status='PENDING', then=Value('Pendiente de pago')),
                When(status='PAID', then=Value('Pagado')),
                When(status='VERIFIED', then=Value('Verificado por Tesorería')),
                When(status='CANCELLED', then=Value('Cancelado')),
                When(status='ACTIVE', then=Value('Activa - En proceso de pago')),
                default=Value(''),
                output_field=CharField()
            ),
            details_count=Count('payment_order_details')
        )
        queryset.values(
            'id', 'order_number',
            'student', 'advisor',
            'status', 'status_display',
            'student_name', 'advisor_name',
            'total_order', 'details_count', 'credit_amount', 'archivo'
        )
        if not filters:
            return queryset.order_by('-created_at')

        queryset = self._apply_filters(queryset, filters)

        return queryset.order_by('-created_at')

    def create(
          self,
          order_data: Dict[str, Any],
          payment_details: list,
          program_data: Dict[str, Any] = None
    ) -> PaymentOrder:
        try:
            with transaction.atomic():
                if not payment_details:
                    logger.error("payment_details es obligatorio y debe tener al menos un elemento")
                    raise

                order = PaymentOrder.objects.create(**order_data)

                if program_data:
                    self._create_payment_order_program(order, program_data)

                self._create_payment_order_details(order, payment_details)

                reloaded_order = self._reload_payment_order(order.pk)

                return reloaded_order
        except Exception as e:
            logger.error(f"Error al crear la orden de pago: {str(e)}", exc_info=True)
            raise

    def update(self, order_id: int, payment_order_data: Dict[str, Any]) -> PaymentOrder:
        with transaction.atomic():
            order = PaymentOrder.objects.get(pk=order_id)

            if payment_order_data.get('suggested_payment_amount'):
                order.suggested_payment_amount = payment_order_data.get('suggested_payment_amount')
                order.save(update_fields=['suggested_payment_amount', 'updated_at'])

            if not order.can_be_updated():
                raise ValueError(f"La orden {order.order_number} no se puede actualizar (estado: {order.status})")

            program_data = payment_order_data.get('program_data')

            if program_data:
                prog = getattr(order, 'payment_order_program', None)
                if prog is None:
                    self._create_payment_order_program(order, program_data)
                else:
                    for k, v in program_data.items():
                        setattr(prog, k, v)
                    prog.save()

            details = payment_order_data.get('payment_details')

            if details is not None:
                order.payment_order_details.all().delete()
                self._create_payment_order_details(order, details)

            return self._reload_payment_order(order.pk)

    def cancel(self, order_id: int) -> bool:
        try:
            order = PaymentOrder.objects.get(pk=order_id)
            # Usar el método del modelo para anular
            return order.cancel()
        except PaymentOrder.DoesNotExist:
            return False

    def get_by_id(self, order_id: int) -> Optional[PaymentOrder]:
        return PaymentOrder.objects.select_related(
            'student',
            'advisor',
            'opportunity',
            'quotation',
            'payment_order_program',
            'payment_order_program__program_type',
            'payment_order_program__institution',
            'payment_order_program__country',
            'payment_order_program__city',
            'payment_order_program__program',
            'payment_order_program__intensity',
            'payment_order_program__material_cost_type',
        ).prefetch_related(
            'payment_order_details',
            'payment_order_details__payment_concept',
            'payment_order_details__type_administrative_cost'
        ).filter(pk=order_id).first()

    def get_by_order_number(self, order_number: str) -> Optional[PaymentOrder]:
        return PaymentOrder.objects.select_related(
            'student',
            'advisor',
            'opportunity',
            'quotation',
            'payment_order_program',
            'payment_order_program__program_type',
            'payment_order_program__institution',
            'payment_order_program__country',
            'payment_order_program__city',
            'payment_order_program__program',
            'payment_order_program__intensity',
            'payment_order_program__material_cost_type',
        ).prefetch_related(
            'payment_order_details',
            'payment_order_details__payment_concept',
            'payment_order_details__type_administrative_cost'
        ).filter(order_number=order_number).first()

    def get_by_id_with_relations(self, order_id: int) -> Optional[PaymentOrder]:
        return self.get_by_id(order_id)

    def save_order(self, payment_order: PaymentOrder, update_fields: list = None) -> PaymentOrder:
        """
        Guarda una instancia de PaymentOrder.
        """
        if update_fields:
            payment_order.save(update_fields=update_fields)
        else:
            payment_order.save()
        return payment_order

    def generate_token(self, payment_order: 'PaymentOrder') -> str:
        link_expires_at = payment_order.generate_expiration_date()
        token_service = PaymentTokenService()
        token_data = token_service.generate_token(order_id=payment_order.id, link_expires_at=link_expires_at)
        return token_data['token']

    def get_payment_order_by_token(self, token_str) -> Optional[PaymentOrder]:
        return PaymentOrder.objects.select_related(
            'student',
            'advisor',
            'opportunity',
            'quotation',
            'payment_order_program',
            'payment_order_program__program_type',
            'payment_order_program__institution',
            'payment_order_program__country',
            'payment_order_program__city',
            'payment_order_program__program',
            'payment_order_program__intensity',
            'payment_order_program__material_cost_type',
        ).prefetch_related(
            'payment_order_details',
            'payment_order_details__payment_concept',
            'payment_order_details__type_administrative_cost'
        ).filter(token=token_str).first()

    # Métodos privados auxiliares
    @staticmethod
    def _apply_filters(queryset: QuerySet, filters: Dict[str, Any]) -> QuerySet:
        """Aplica los filtros al queryset de órdenes de pago."""
        if filters.get('order_number'):
            queryset = queryset.filter(order_number=filters['order_number'])
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
        if filters.get('student'):
            queryset = queryset.filter(student=filters['student'])
        if filters.get('advisor'):
            queryset = queryset.filter(advisor=filters['advisor'])
        if filters.get('opportunity'):
            queryset = queryset.filter(opportunity=filters['opportunity'])
        if filters.get('quotation'):
            queryset = queryset.filter(quotation=filters['quotation'])
        if filters.get('date_from'):
            queryset = queryset.filter(created_at__gte=filters['date_from'])
        if filters.get('date_to'):
            queryset = queryset.filter(created_at__lte=filters['date_to'])

        return queryset

    @staticmethod
    def _create_payment_order_program(order: PaymentOrder, program_data: Dict[str, Any]) -> PaymentOrderProgram:
        program_kwargs = dict(program_data)
        program_kwargs['payment_order_id'] = order.id
        return PaymentOrderProgram.objects.create(**program_kwargs)

    @staticmethod
    def _create_payment_order_details(order: PaymentOrder, payment_details: list) -> None:
        payment_details_objects = []

        for detail in payment_details:
            payment_details_kwargs = detail.copy()
            payment_details_kwargs['payment_order'] = order

            obj = PaymentOrderDetails(**payment_details_kwargs)

            obj.amount = obj.calculate_amount()
            obj.sub_total = obj.calculate_subtotal

            payment_details_objects.append(obj)

        if payment_details_objects:
            PaymentOrderDetails.objects.bulk_create(payment_details_objects)
            order.calculate_total_order()


    @staticmethod
    def _reload_payment_order(order_id: int) -> PaymentOrder:
        return PaymentOrder.objects.select_related(
            'student', 'advisor', 'opportunity', 'quotation'
        ).prefetch_related(
            'payment_order_details', 'payment_order_program'
        ).get(pk=order_id)
