from apps.pagos.domain.interface.repository.payment_repository_interface import PaymentRepositoryInterface
from apps.pagos.models import Payment


class GetPaymentById:
    def __init__(self, payment_repository: PaymentRepositoryInterface):
        self.payment_repository = payment_repository

    def execute(self, payment_id:int) -> Payment:
        return self.payment_repository.get_by_id(payment_id)