import logging
from decimal import Decimal
from typing import Optional, Dict, Any, List

from django.db import transaction
from django.db.models import QuerySet, F, Value, CharField, Case, When, Sum, Q
from django.db.models.functions import Concat

from apps.billing.application.commands import CreatePaymentReceiptCommand
from apps.billing.domain.interface.repository.invoice_repository_interface import InvoiceRepositoryInterface
from apps.billing.models import Invoice, InvoiceDetail, InvoiceCreditDetail, PaymentReceipt

logger = logging.getLogger(__name__)

class InvoiceRepository(InvoiceRepositoryInterface):

    def __init__(self):
        super().__init__()

    def list_all(self, filters: Dict[str, Any] = None) -> QuerySet:
        """Lista todas las facturas con filtros opcionales."""
        queryset = Invoice.objects.select_related(
            'user',
            'advisor',
            'payment_order',
            'payment_order__opportunity'
        ).prefetch_related(
            'details',
            'details__payment_concept',
            'receipts',
            'credits'
        ).annotate(
            student_name=Concat(
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
                When(status='B', then=Value('Borrador')),
                When(status='I', then=Value('Emitida')),
                When(status='PP', then=Value('Parcialmente pagada')),
                When(status='P', then=Value('Pagada')),
                When(status='A', then=Value('Anulada')),
                When(status='PV', then=Value('Pendiente por Verificar')),
                When(status='V', then=Value('Verificada')),
                When(status='R', then=Value('Reembolsada')),
                When(status='E', then=Value('Exonerada')),
                default=Value(''),
                output_field=CharField()
            )
        )

        if filters:
            queryset = self._apply_filters(queryset, filters)

        return queryset.order_by('-created_at')

    def create(
          self,
          invoice_data: Dict[str, Any],
          invoice_details: List[Dict[str, Any]]
    ) -> Invoice:
        try:
            with transaction.atomic():
                if not invoice_details:
                    raise ValueError("invoice_details es obligatorio y debe tener al menos un elemento")

                # Inicializar totales en 0
                invoice_data['subtotal'] = Decimal('0.00')
                invoice_data['total'] = Decimal('0.00')
                invoice_data['balance_due'] = Decimal('0.00')

                # Crear la factura principal
                invoice = Invoice.objects.create(**invoice_data)
                # Crear detalles (obligatorio)
                self._create_invoice_details(invoice, invoice_details)

                # Recargar para obtener el total actualizado por las señales
                reloaded_invoice = self._reload_invoice(invoice.pk)

                return reloaded_invoice
        except Exception as e:
            logger.error(f"Error al crear factura: {str(e)}")
            raise

    def update(self, invoice_id: int, invoice_data: Dict[str, Any]) -> Invoice:

        with transaction.atomic():
            invoice = Invoice.objects.get(pk=invoice_id)

            # Validar que la factura no esté pagada o anulada
            if invoice.status in ['P', 'A']:
                raise ValueError(
                    f"La factura {invoice.invoice_number} no se puede actualizar "
                    f"(estado: {invoice.get_status_display()})"
                )

            # Actualizar campos básicos
            for key, value in invoice_data.items():
                if key not in ['invoice_details'] and hasattr(invoice, key):
                    setattr(invoice, key, value)

            invoice.save()

            # Actualizar detalles si vienen en los datos
            details = invoice_data.get('invoice_details')
            if details is not None:
                invoice.details.all().delete()
                self._create_invoice_details(invoice, details)

            return self._reload_invoice(invoice.pk)

    def cancel(self, invoice_id: int) -> bool:
        """
        Anula una factura.

        """
        try:
            with transaction.atomic():
                invoice = Invoice.objects.get(pk=invoice_id)

                # TODO Usar el servicio de dominio para validar pasar a dode se este llamando
                #self.domain_service.validate_invoice_cancellation(invoice)

                # Cambiar estado a Anulada
                invoice.status = 'A'
                invoice.save(update_fields=['status', 'updated_at'])

                return True
        except Invoice.DoesNotExist:
            return False

    def get_by_id(self, invoice_id: int) -> Optional[Invoice]:
        """Obtiene una factura por ID con relaciones básicas."""
        return Invoice.objects.select_related(
            'user',
            'advisor',
            'payment_order',
            'payment_order__opportunity'
        ).prefetch_related(
            'details',
            'details__payment_concept',
            'details__payment_concept__category'
        ).filter(pk=invoice_id).first()

    def get_by_invoice_number(self, invoice_number: str) -> Optional[Invoice]:
        """Obtiene una factura por su número de factura."""
        return Invoice.objects.select_related(
            'user',
            'advisor',
            'payment_order',
            'payment_order__opportunity'
        ).prefetch_related(
            'details',
            'details__payment_concept'
        ).filter(invoice_number=invoice_number).first()

    def get_by_id_with_relations(self, invoice_id: int) -> Optional[Invoice]:
        """Obtiene una factura con todas sus relaciones cargadas."""
        return Invoice.objects.select_related(
            'user',
            'advisor',
            'payment_order',
            'payment_order__opportunity',
            'payment_order__quotation'
        ).prefetch_related(
            'details',
            'details__payment_concept',
            'details__payment_concept__category',
            'receipts',
            'receipts__payment',
            'credits',
            'invoice_credit_detail_invoice'
        ).filter(pk=invoice_id).first()

    def save_invoice(self, invoice: Invoice, update_fields: List[str] = None) -> Invoice:
        """
        Guarda una instancia de Invoice.
        update_fields: Lista de campos a actualizar (opcional)
        """
        if update_fields:
            invoice.save(update_fields=update_fields)
        else:
            invoice.save()
        return invoice

    def get_invoices_by_student(self, student_id: int) -> List[Invoice]:
        """Obtiene todas las facturas de un estudiante."""
        return list(
            Invoice.objects.select_related(
                'user',
                'payment_order'
            ).prefetch_related(
                'details'
            ).filter(user_id=student_id).order_by('-created_at')
        )

    def get_invoices_by_payment_order(self, payment_order_id: int) -> Optional[Invoice]:
        """Obtiene todas las facturas de una orden de pago."""
        return Invoice.objects.select_related(
            'user',
            'advisor',
            'payment_order'
        ).prefetch_related(
            'details',
            'details__payment_concept'
        ).filter(payment_order_id=payment_order_id).first()


    def get_pending_invoices_by_student(self, student_id: int) -> List[Invoice]:
        """Obtiene facturas pendientes (no pagadas completamente) de un estudiante."""
        return list(
            Invoice.objects.select_related(
                'user',
                'payment_order'
            ).prefetch_related(
                'details'
            ).filter(
                user_id=student_id,
                status__in=['I', 'PP', 'PV', 'V']  # Emitida, Parcialmente Pagada, Pendiente Verificar, Verificada
            ).exclude(
                status='A'  # Excluir anuladas
            ).order_by('-created_at')
        )

    def calculate_student_total_debt(self, student_id: int) -> Decimal:
        """Calcula la deuda total de un estudiante."""
        result = Invoice.objects.filter(
            user_id=student_id,
            status__in=['I', 'PP', 'PV', 'V']
        ).exclude(
            status__in=['P', 'A']  # Excluir pagadas y anuladas
        ).aggregate(
            total_debt=Sum('balance_due')
        )

        return result['total_debt'] or Decimal('0.00')

    @staticmethod
    def get_invoice_detail_by_id(invoice_detail_id: int) -> Optional[InvoiceDetail]:
        """Obtiene un detalle de factura por su ID."""
        return InvoiceDetail.objects.select_related(
            'invoice',
            'payment_concept',
            'payment_concept__category'
        ).filter(pk=invoice_detail_id).first()

    @staticmethod
    def _create_invoice_details(invoice: Invoice, details: List[Dict[str, Any]]) -> None:
        """Crea los detalles de una factura."""
        for detail_data in details:
            detail_kwargs = detail_data.copy()
            detail_kwargs['invoice'] = invoice

            InvoiceDetail.objects.create(**detail_kwargs)

    def _reload_invoice(self, invoice_id: int) -> Invoice:
        """Recarga una factura desde la base de datos con todas sus relaciones."""
        return self.get_by_id_with_relations(invoice_id)

    @staticmethod
    def _apply_filters(queryset: QuerySet, filters: Dict[str, Any]) -> QuerySet:
        """Aplica filtros al queryset de facturas."""
        # Filtro por estudiante
        if 'student_id' in filters:
            queryset = queryset.filter(user_id=filters['student_id'])

        # Filtro por asesor
        if 'advisor_id' in filters:
            queryset = queryset.filter(advisor_id=filters['advisor_id'])

        # Filtro por estado
        if 'status' in filters:
            queryset = queryset.filter(status=filters['status'])

        # Filtro por orden de pago
        if 'payment_order_id' in filters:
            queryset = queryset.filter(payment_order_id=filters['payment_order_id'])

        # Filtro por rango de fechas
        if 'date_from' in filters:
            queryset = queryset.filter(created_at__gte=filters['date_from'])

        if 'date_to' in filters:
            queryset = queryset.filter(created_at__lte=filters['date_to'])

        # Búsqueda por número de factura
        if 'invoice_number' in filters:
            queryset = queryset.filter(invoice_number__icontains=filters['invoice_number'])

        # Búsqueda por nombre de estudiante
        if 'student_name' in filters:
            queryset = queryset.filter(
                Q(user__nombre__icontains=filters['student_name']) |
                Q(user__apellido__icontains=filters['student_name'])
            )

        return queryset

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
        try:
            # Buscar el InvoiceCreditDetail que corresponde a este pago
            # (el que no tiene payment_receipt aún)
            credit_detail = InvoiceCreditDetail.objects.filter(
                invoice=invoice,
                amount=payment.amount,
                payment_receipt__isnull=True
            ).order_by('-created_at').first()

            if credit_detail:
                credit_detail.payment_receipt = payment_receipt
                credit_detail.save(update_fields=['payment_receipt'])
                logger.info(
                    f"InvoiceCreditDetail vinculado con recibo {payment_receipt.receipt_number}"
                )
                return credit_detail

            logger.warning(
                f"No se encontró InvoiceCreditDetail para vincular. "
                f"Factura: {invoice.invoice_number}, Monto: ${payment.amount}"
            )
            return None

        except Exception as e:
            logger.warning(
                f"Error al vincular PaymentReceipt {payment_receipt.receipt_number}: {str(e)}"
            )
            return None

    def calculate_receipt_balances(self, invoice, payment_amount):
        """
        Calcula los balances para un recibo de pago.

        IMPORTANTE: Este método se llama DESPUÉS de que Payment.save() ya actualizó
        el invoice.balance_due, por lo tanto:
        - invoice.balance_due = saldo DESPUÉS del pago (nuevo saldo)
        - previous_balance = saldo ANTES del pago = nuevo_saldo + monto_pagado

        Args:
            invoice: Factura con balance_due YA ACTUALIZADO
            payment_amount: Monto del pago que se acaba de realizar

        Returns:
            tuple: (previous_balance, new_balance)

        Ejemplo:
            - Total factura: $1000
            - Pago realizado: $300
            - invoice.balance_due (ya actualizado): $700
            - previous_balance = $700 + $300 = $1000
            - new_balance = $700
        """
        # El nuevo saldo es el balance actual (ya actualizado por Payment.save())
        new_balance = invoice.balance_due

        # El saldo anterior es: saldo_actual + monto_que_acabamos_de_pagar
        previous_balance = new_balance + payment_amount

        return previous_balance, new_balance

    def create_payment_receipt(self, receipt_data: CreatePaymentReceiptCommand):
        """
        Crea un recibo de pago.
        
        Args:
            receipt_data: Comando con los datos del recibo
            
        Returns:
            PaymentReceipt creado
            
        Note:
            - Extrae IDs de los objetos ForeignKey (payment, invoice, student)
            - invoice puede venir como objeto (para log) pero se pasa correctamente a Django
        """
        receipt_kwargs = {
            'payment_id': receipt_data.payment,  # ID del pago
            'invoice_id': receipt_data.invoice,  # Django acepta el objeto o el ID
            'student_id': receipt_data.student,  # ID del estudiante
            'amount_paid': receipt_data.amount_paid,
            'previous_balance': receipt_data.previous_balance,
            'new_balance': receipt_data.new_balance,
            'payment_method': receipt_data.payment_method,
            'payment_date': receipt_data.payment_date,
            'currency': receipt_data.currency,
            'notes': receipt_data.notes
        }

        receipt = PaymentReceipt.objects.create(**receipt_kwargs)

        logger.info(
            f"PaymentReceipt {receipt.receipt_number} creado exitosamente. "
            f"Invoice: {receipt.invoice.invoice_number}, "
            f"Amount: ${receipt.amount_paid}"
        )

        return receipt

    def get_payment_receipt_by_id(self, payment_receipt_id:int)-> PaymentReceipt:

        receipt = PaymentReceipt.objects.select_related(
            'payment', 'invoice', 'student'
        ).filter(id=payment_receipt_id).first()

        return receipt

    def create_invoice_credit_detail(self, payment, invoice: Invoice, payment_receipt=None) -> InvoiceCreditDetail:
        """
        Crea un registro de crédito/abono aplicado a una factura.
        
        Args:
            payment: Pago realizado (el dinero YA entró)
            invoice: Factura a la que se aplica el abono
            payment_receipt: Recibo de pago asociado (opcional)
        
        Returns:
            InvoiceCreditDetail creado con status='P' (Pagado)
            
        Note:
            - credit_status='P' significa que este abono YA se pagó (dinero en banco)
            - credit_status='E' se usaría para créditos a favor pendientes de aplicar
            - Este registro NO afecta el cálculo de balance (se usa PaymentAllocation)
        """
        credit_detail = InvoiceCreditDetail.objects.create(
                        invoice=invoice,
                        payment_receipt=payment_receipt,
                        amount=payment.amount,
                        credit_status='P'  # P = Pagado (este abono YA se realizó)
                    )
        return credit_detail

    def update_credit_invoice_payment_receipt(self, invoice_credit_detail: InvoiceCreditDetail, payment_receipt, update_fields: List[str])-> InvoiceCreditDetail:
        invoice_credit_detail.save(update_fields=update_fields)
        return invoice_credit_detail

    def get_already_applied_allocations(self, invoice_detail_id: int) -> QuerySet:
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
        from apps.pagos.models import PaymentAllocation
        
        allocations = PaymentAllocation.objects.filter(
            invoice_detail_id=invoice_detail_id,
            payment__status__in=['D', 'V']  # Disponible o Verificado
        ).select_related('payment', 'invoice_detail').order_by('-created_at')
        
        return allocations

