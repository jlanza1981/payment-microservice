import logging

from django.db import transaction
from decimal import Decimal

from apps.billing.application.use_cases.prepare_invoice_data import PrepareInvoiceDataUseCase
from apps.billing.application.use_cases import CreateInvoiceUseCase
from apps.billing.application.use_cases.create_invoice_credit_detail import CreateInvoiceCreditDetail
from apps.billing.application.use_cases.create_payment_receipt import CreatePaymentReceiptUseCase
from apps.billing.application.use_cases.find_invoice_by_payment_order import FindInvoiceByPaymentOrder
from apps.core.application.use_cases.get_payer_name_order_approved import GetPayerNameOrderApproved
from apps.core.domain.events.event_dispatcher import EventDispatcher
from apps.core.infrastructure.inbox.repository.inbox_repository import InboxRepository
from apps.pagos.application.commands import ProcessPaymentCommand, CreatePaymentTransactionCommand
from apps.pagos.application.services.payment_processing_service import PaymentProcessingService
from apps.pagos.application.use_cases.create_payment import CreatePaymentUseCase
from apps.pagos.application.use_cases.prepare_payment_allocations import PreparePaymentAllocationsUseCase
from apps.pagos.application.use_cases.prepare_payment_data import PreparePaymentDataUseCase
from apps.pagos.application.use_cases.process_payment import ProcessPaymentUseCase
from apps.pagos.application.use_cases.record_payment_transaction import RecordPaymentTransaction
from apps.orden_pagos.application.use_cases.get_payment_order_by_id import GetPaymentOrderByIdUseCase
from apps.core.domain.events.payment_captured_event import PaymentCapturedEvent

from apps.core.domain.events.paypal_payment_captured_event import PaypalPaymentCapturedEvent

logger = logging.getLogger(__name__)

class ProcessPaypalPaymentCaptureService:
    """
    Servicio de aplicación que procesa un evento de pago capturado por PayPal.
    Orquesta los dominios: orden_pagos, pagos y billing.
    """

    def __init__(self,
                 payment_order_repository,
                 invoice_repository,
                 payment_repository,
                 payment_concept_repository,
                 user_repository,
                 invoice_service
    ):
        self.payment_order_repository = payment_order_repository
        self.invoice_repository = invoice_repository
        self.payment_repository = payment_repository

        self.invoice_service = invoice_service

        self.prepare_invoice_data_uc = PrepareInvoiceDataUseCase(self.payment_order_repository, user_repository)
        self.prepare_payment_allocations_uc = PreparePaymentAllocationsUseCase(self.invoice_repository, payment_concept_repository)
        self.prepare_payment_data_uc = PreparePaymentDataUseCase(user_repository, self.invoice_repository)

        invoice_uc = CreateInvoiceUseCase(self.invoice_service, self.invoice_repository, self.payment_order_repository, user_repository, payment_concept_repository)
        payment_uc = CreatePaymentUseCase(self.payment_repository, payment_concept_repository, self.invoice_repository, PaymentProcessingService(), self.prepare_payment_data_uc)

        self.credit_uc = CreateInvoiceCreditDetail(self.invoice_repository, self.payment_repository)
        self.create_payment_receipt_uc = CreatePaymentReceiptUseCase(self.invoice_repository, self.payment_repository)
        self.inbox_repository = InboxRepository()
        inbox_payer_name_uc = GetPayerNameOrderApproved(self.inbox_repository)

        self.process_payment_uc = ProcessPaymentUseCase(
            invoice_uc=invoice_uc,
            payment_uc=payment_uc,
            credit_uc= self.credit_uc,
            prepare_payment_allocations_uc=self.prepare_payment_allocations_uc,
            payment_order_repository=self.payment_order_repository,
            invoice_repository=self.invoice_repository,
            payment_repository=self.payment_repository,
            inbox_payer_name_uc=inbox_payer_name_uc

        )

    @transaction.atomic
    def execute(self, event: PaypalPaymentCapturedEvent):
        paypal_data = event
        print(f"Procesando evento paypal_data: {paypal_data}")
        payment_transaction = self.create_payment_transaction(paypal_data)

        if not payment_transaction:
            logger.info(f"Transacción de pago ya existe para PayPal Order ID: {paypal_data.capture_id}")
            return
        print('order_id', paypal_data.order_id)
        # 2. Obtener orden de pago
        payment_order = GetPaymentOrderByIdUseCase(self.payment_order_repository).execute(
            order_id=int(paypal_data.order_id)
        )

        # 3. Verificar si ya existe factura para esta orden
        existing_invoice = FindInvoiceByPaymentOrder(self.invoice_repository).execute(payment_order.id)

        if existing_invoice and existing_invoice.status == 'PP':
            # Es un abono subsecuente
            logger.info(f"Factura existente encontrada: {existing_invoice.invoice_number}")
            payment = self._process_additional_payment(existing_invoice, paypal_data)
        else:
            # Es el primer pago (crear nueva factura)
            logger.info("Creando nueva factura para primer pago")
            payment_result = self._process_first_payment(payment_order, paypal_data)
            
            if payment_result is None:
                logger.error(
                    f"❌ No se pudo procesar el primer pago para la orden {payment_order.order_number}. "
                    f"El proceso se detiene aquí. Revisa los logs anteriores para más detalles."
                )
                return
            
            payment = payment_result.payment

        # 4. Actualizar transacción con el pago creado
        payment_transaction.update_payment(payment)

        logger.info(
            f"Procesamiento completado - "
            f"Pago: {payment.payment_number}, "
            f"Factura: {payment.invoice.invoice_number}"
        )
    def create_payment_transaction(self, paypal_data):
        resource = paypal_data.resource

        command = CreatePaymentTransactionCommand(
            paypal_order_id=resource['id'],
            payment_order=resource['custom_id'],
            currency=resource['amount']['currency_code'],
            amount=resource['amount']['value'],
            status=resource['status'],
            gross_amount=resource['seller_receivable_breakdown']['gross_amount']['value'],
            paypal_fee=resource['seller_receivable_breakdown']['paypal_fee']['value'],
            net_amount=resource['seller_receivable_breakdown']['net_amount']['value'],
            payee_email=resource['payee']['email_address'],
            payee_merchant_id=resource['payee']['merchant_id'],
            resource_json=resource
        )
        return RecordPaymentTransaction(self.payment_repository, self.payment_order_repository).execute(command)

    def _process_first_payment(self, payment_order, paypal_data):
        resource = paypal_data.resource
        seller_receivable_breakdown = resource['seller_receivable_breakdown']
        
        command = ProcessPaymentCommand(
            payment_order_id=payment_order.id,
            payment_provider='paypal',
            provider_transaction_id=paypal_data.capture_id,
            amount=Decimal(seller_receivable_breakdown['net_amount']['value']),  #monto real del pago
            currency=paypal_data.currency,
            payer_name=paypal_data.payer_name
        )
        is_full_payment = command.amount >= payment_order.total_order

        payment_processed = self.process_payment_uc.execute(command)
        
        if payment_processed is None:
            logger.error(
                f"❌ No se pudo procesar el pago de PayPal para la orden {payment_order.order_number}. "
                f"Capture ID: {paypal_data.capture_id}"
            )
            return None

        self._emit_payment_captured_event(payment_processed.invoice, payment_processed.payment, is_full_payment, payment_processed.payment_receipt)

        return payment_processed

    def _process_additional_payment(self, invoice, paypal_data):
        resource = paypal_data.resource
        seller_receivable_breakdown = resource['seller_receivable_breakdown']
        logger.info(
            f"Procesando abono adicional a factura {invoice.invoice_number} - "
            f"Balance anterior: ${invoice.balance_due}, "
            f"Abono: ${paypal_data.amount}"
        )

        # Determinar si es pago completo antes de crear el pago
        is_full_payment = Decimal(paypal_data.amount) >= Decimal(invoice.balance_due)
        command = ProcessPaymentCommand(
            payment_order_id=invoice.payment_order.id,
            payment_provider='paypal',
            provider_transaction_id=paypal_data.capture_id,
            amount=Decimal(seller_receivable_breakdown['net_amount']['value']),  # monto real del pago
            currency=paypal_data.currency,
            payer_name=paypal_data.payer_name
        )
        payment = self.process_payment_uc.create_payment(invoice, command, is_full_payment)

        # Actualizar balance después de crear el pago
        invoice.update_balance()
        invoice.refresh_from_db()
        
        payment_receipt = None
        payment_order = invoice.payment_order

        logger.info(
            f"Abono completó el pago de factura {invoice.invoice_number}. "
            f"Balance restante: ${invoice.balance_due}"
        )
        if is_full_payment:
            invoice.update_status('P')
            payment_order.mark_as_paid()
            payment_order.mark_consumed()
            payment_order.initialize_suggested_payment_amount()
        else:
            payment_receipt = self.create_payment_receipt_uc.execute(payment.id, invoice.id)
            self.credit_uc.execute(invoice.id, payment.id, payment_receipt)
            payment_order.initialize_suggested_payment_amount()



        self._emit_payment_captured_event(invoice, payment, is_full_payment, payment_receipt)

        return payment

    @staticmethod
    def _emit_payment_captured_event(invoice, payment, is_full_payment, payment_receipt=None):
        event = PaymentCapturedEvent(
            invoice_id=invoice.id,
            payment_id=payment.id,
            payment_receipt_id=payment_receipt.id if payment_receipt else None,
            amount=payment.amount,
            currency=invoice.currency,
            is_full_payment=is_full_payment,
            invoice_number=invoice.invoice_number,
            payment_provider='paypal'
        )

        EventDispatcher.dispatch(event)