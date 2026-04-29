import logging


from apps.billing.domain.interface.repository import InvoiceRepositoryInterface
from apps.pagos.domain.interface.repository.payment_repository_interface import PaymentRepositoryInterface
from apps.pagos.models import Payment
from apps.pagos.application.commands import CreatePaymentCommand

logger = logging.getLogger(__name__)

class CreatePaymentUseCase:

    def __init__(
            self,
            payment_repository: PaymentRepositoryInterface,
            payment_concept_repository,
            invoice_repository: InvoiceRepositoryInterface,
            payment_processing_service,
            prepare_payment_data_uc
    ):
        self.payment_repository = payment_repository
        self.payment_concept_repository = payment_concept_repository
        self.invoice_repository = invoice_repository
        self.payment_processing_service = payment_processing_service
        self.prepare_payment_data_uc = prepare_payment_data_uc

    def execute(
          self,
          payment_data: CreatePaymentCommand
    ) -> Payment:

        raw_data = self.payment_processing_service.validate_payment_data(payment_data)
        print('raw_data  pago:', raw_data)

        payment_allocation = raw_data.pop('payment_allocation', None)

        print('payment_data:', raw_data)
        print('payment_allocation:', payment_allocation)
        payment_kwargs = self.prepare_payment_data_uc.execute(raw_data)

        payment = self.payment_repository.create(
            payment_data=payment_kwargs,
            allocations=payment_allocation
        )
        payment.invoice.update_balance()

        logger.info(
            f"Pago anticipado creado: {payment.payment_number} "
            f"(Sin factura - Monto: ${payment.amount})"
        )

        return payment