import logging

from apps.billing.domain.interface.repository import InvoiceRepositoryInterface
from apps.orden_pagos.domain.interface.repository.repository_interface import PaymentOrderRepositoryInterface
from apps.pagos.application.use_cases.send_notification_payment_attempt_not_completed import \
    SendNotificationPaymentAttemptNotCompleted
from apps.pagos.domain.interface.repository.payment_repository_interface import PaymentRepositoryInterface
from apps.core.application.services.process_paypal_payment_capture import (
    ProcessPaypalPaymentCaptureService
)
from apps.core.application.use_cases.get_pending_inbox_events import GetPendingInboxEventsUseCase
from apps.core.domain.events.paypal_payment_captured_event import PaypalPaymentCapturedEvent

logger = logging.getLogger(__name__)


class WebhookEventProcessor:
    """ Procesador de eventos de webhook."""

    def __init__(
            self,
            inbox_repository,
            payment_order_repository: PaymentOrderRepositoryInterface,
            invoice_repository: InvoiceRepositoryInterface,
            payment_repository: PaymentRepositoryInterface,
            payment_concept_repository,
            user_repository,
            invoice_service,
    ):
        self.repository = inbox_repository
        self.payment_order_repository = payment_order_repository
        self.invoice_repository = invoice_repository
        self.payment_repository = payment_repository
        self.payment_concept_repository = payment_concept_repository
        self.user_repository =user_repository
        self.invoice_service = invoice_service
        self.payee_name = None

    def process_pending(self, created_event):

        pending_events = GetPendingInboxEventsUseCase(
            self.repository
        ).execute()
        logger.info(f"pending_events: {pending_events}")
        for event in pending_events:
            print(f"pending_events: {event}")
            if event:
                self._process(event, created_event)



    def _process(self, inbox_event, created_event):
        """Procesa un evento con información del created_event"""
        payload = inbox_event.payload
        print('_process payload', payload)
        resource = payload["resource"]
        print('_process resource', resource)
        event = PaypalPaymentCapturedEvent(
            capture_id=resource["id"],
            order_id=created_event.payment_order_id,
            amount=resource["amount"]["value"],
            currency=resource["amount"]["currency_code"],
            payer_email=resource["payee"]["email_address"],
            payer_name=created_event.payer_name,
            resource=resource
        )
        print('_process PaypalPaymentCapturedEvent', event)
        if created_event.provider == "paypal":
            if created_event.provider_event_type == "PAYMENT.CAPTURE.COMPLETED":
                ProcessPaypalPaymentCaptureService(
                    self.payment_order_repository,
                    self.invoice_repository,
                    self.payment_repository,
                    self.payment_concept_repository,
                    self.user_repository,
                    self.invoice_service
                ).execute(event)

            if created_event.provider_event_type in ["PAYMENT.CAPTURE.DECLINED", "PAYMENT.CAPTURE.DENIED"]:
                ProcessPaypalPaymentCaptureService(
                    self.payment_order_repository,
                    self.invoice_repository,
                    self.payment_repository,
                    self.payment_concept_repository,
                    self.user_repository,
                    self.invoice_service
                ).create_payment_transaction(event)

                SendNotificationPaymentAttemptNotCompleted(self.payment_order_repository).execute(created_event.payment_order_id)

            if created_event.provider_event_type in ["PAYMENT.CAPTURE.REFUNDED", "PAYMENT.CAPTURE.REVERSED"]:
                pass

        inbox_event.processed = True
        inbox_event.save()

