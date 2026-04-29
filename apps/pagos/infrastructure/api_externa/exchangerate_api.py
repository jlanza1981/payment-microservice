import requests

from api import settings


class ExchangeRatesRepository:
    def __init__(self):
        self.exchange_rates_provider = settings.EXCHANGE_RATE

    def get_exchange_rate(self, currency:str):
        response = requests.get(self.exchange_rates_provider + currency)
        return response.json()