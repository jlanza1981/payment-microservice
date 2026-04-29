import logging

from django.db import transaction

from apps.billing.application.commands import CreateInvoiceCommand
from apps.billing.application.mappers.invoice_mapper import InvoiceMapper
from apps.billing.application.use_cases.create_payment_receipt import CreatePaymentReceiptUseCase
from apps.billing.domain.interface.repository import InvoiceRepositoryInterface
from apps.billing.presentation.api.schemas.output_schemas import InvoiceSchema
from apps.orden_pagos.domain.interface.repository.repository_interface import PaymentOrderRepositoryInterface
from apps.orden_pagos.presentation.api.schemas import PaymentOrderSchema
from apps.pagos.application.commands import CreatePaymentCommand, ProcessPaymentResult
from apps.pagos.domain.interface.repository.payment_repository_interface import PaymentRepositoryInterface

logger = logging.getLogger(__name__)

class ProcessPaymentUseCase:
    def __init__(
        self,
        invoice_uc,
        payment_uc,
        credit_uc,
        prepare_payment_allocations_uc,
        payment_order_repository: PaymentOrderRepositoryInterface,
        invoice_repository: InvoiceRepositoryInterface,
        payment_repository:PaymentRepositoryInterface,
        inbox_payer_name_uc

    ):

        self.invoice_uc = invoice_uc
        self.create_payment_uc = payment_uc
        self.credit_uc = credit_uc
        self.inbox_payer_name_uc = inbox_payer_name_uc


        self.payment_order_repository = payment_order_repository
        self.invoice_repository = invoice_repository
        self.payment_repository = payment_repository

        self.create_payment_receipt_uc = CreatePaymentReceiptUseCase(self.invoice_repository, self.payment_repository)
        self.prepare_payment_allocations_uc = prepare_payment_allocations_uc

    @transaction.atomic
    def execute(self, command):
        payment_receipt = None
        # 1️⃣ Obtener orden de pago
        payment_order = self.payment_order_repository.get_by_id(command.payment_order_id)

        # 2️⃣ Determinar si es pago total o parcial
        is_full_payment = command.amount >= payment_order.total_order
        invoice_status = 'P' if is_full_payment else 'PP'
        status_payment_order = 'PAID' if is_full_payment else 'ACTIVE'

        # 3️⃣ Crear factura
        invoice = self._create_invoice(payment_order, invoice_status)

        # Si no se pudo crear la factura, detener el proceso
        if invoice is None:
            logger.error(
                f"❌ El proceso de pago se detiene porque no se pudo crear la factura "
                f"para la orden {payment_order.order_number}"
            )
            return None

        # 4️⃣ Crear pago asociado
        payment = self.create_payment(invoice, command, is_full_payment)

        # 5️⃣ Actualizar balance de la factura basado en el pago recibido
        invoice.update_balance()

        # Recargar la factura para obtener los valores actualizados
        invoice.refresh_from_db()

        logger.info(
            f"Balance actualizado - Factura: {invoice.invoice_number} - "
            f"Balance pendiente: ${invoice.balance_due} - "
            f"Estado: {invoice.get_status_display()}"
        )

        if not is_full_payment:
            payment_receipt = self.process_partial_payment(invoice.id, payment.id)
            payment_order.update_status(status_payment_order)
            payment_order.initialize_suggested_payment_amount()
        else:
            payment_order.mark_as_paid()
            payment_order.mark_consumed()

        return ProcessPaymentResult(
            invoice=invoice,
            payment=payment,
            payment_receipt=payment_receipt
        )

    def _create_invoice(self, payment_order, initial_status: str):
        payment_order_schema = PaymentOrderSchema.from_orm(payment_order)

        #payload_invoice = self.invoice_uc.prepare_invoice_data(payment_order_schema.model_dump())
        payload_invoice = InvoiceMapper.prepare_invoice_data(
            payment_order_schema.model_dump()
        )
        payload_invoice['status'] = initial_status
        data_invoice = CreateInvoiceCommand(**payload_invoice)

        invoice = self.invoice_uc.execute(data_invoice)
        
        if invoice is None:
            logger.error(
                f"❌ No se pudo crear la factura para la orden {payment_order.order_number}. "
                f"El proceso se detiene aquí."
            )
            return None

        logger.info(
            f"Factura creada: {invoice.invoice_number} - "
            f"Estado: {initial_status} - "
            f"Total: ${invoice.total}"
        )

        return invoice

    def create_payment(self, invoice, data, is_full_payment):
        invoice_schema = InvoiceSchema.from_orm(invoice).dict()
        amount_to_pay = data.amount if hasattr(data, 'amount') else 0
        # Determinar el monto del pago
        amount = invoice.payment_order.suggested_payment_amount if invoice.payment_order.suggested_payment_amount else invoice.total
        
        # Preparar allocations con distribución correcta del monto
        payment_allocation = self.prepare_payment_allocations_uc.execute(
            invoice_schema.get('invoice_details'),
            payment_amount=amount,  # Pasar el monto para distribución correcta
            is_full_payment=is_full_payment
        )
        
        payer_name_inbox = self.inbox_payer_name_uc.execute(invoice.payment_order.id)
        payer_name = payer_name_inbox if payer_name_inbox else invoice_schema.get('user_name')

        payment_data = CreatePaymentCommand(
            invoice=invoice.id,
            user=invoice_schema.get('user'),
            advisor=invoice_schema.get('advisor'),
            payment_reference_number=data.provider_transaction_id,
            payment_method='PP',  # PayPal
            status='D',  # Disponible (ya verificado por PayPal)
            amount=amount,
            amount_paid=data.amount,
            currency=data.currency,
            payer_name=payer_name,
            payment_terms_conditions=True,
            payment_allocation=payment_allocation
        )

        payment = self.create_payment_uc.execute(payment_data)

        logger.info(
            f"Pago creado: {payment.payment_number} - "
            f"Monto: ${payment.amount} - "
            f"Factura: {invoice.invoice_number} - "
            f"Pagador: {payer_name}"
        )

        return payment

    def process_partial_payment(self, invoice, payment):
        payment_receipt = self.create_payment_receipt_uc.execute(payment, invoice)

        self.credit_uc.execute(invoice, payment, payment_receipt)

        return payment_receipt