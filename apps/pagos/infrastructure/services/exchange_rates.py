from apps.pagos.infrastructure.api_externa.exchangerate_api import ExchangeRatesRepository


class ExchangeRatesServices:
    def __init__(self):
        self.exchange_rates_repository = ExchangeRatesRepository()

    def get_exchange_rate(self, currency:str):
        return self.exchange_rates_repository.get_exchange_rate(currency)
