from apps.pagos.infrastructure.fee_repository import FeeRepository


class FeeConfigUseCase:
    def __init__(self):
        self.repository = FeeRepository()

    def get_config(self, currency:str):
        return self.repository.get_fee_config(currency)