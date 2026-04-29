import json

import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from api import settings
from .token_service import PayPalTokenService
from ..services.exchange_rates import ExchangeRatesServices
from ...utils import calculate_paypal_order_amount


class PayPalClient:

    def __init__(self):
        self.paypal_path = f"{settings.PAYPAL_BASE_URL}/v2"
        self.access_token = PayPalTokenService.get_access_token()
        self.exchange_rates_services = ExchangeRatesServices()

    def create_order(self, amount, currency, payment_order:int):
        url = f"{self.paypal_path}/checkout/orders"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }

        order_amount = calculate_paypal_order_amount(amount, currency)
        print('client currency', currency)
        body = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": currency,
                    "value": str(order_amount)
                },
                "custom_id": str(payment_order)
            }]
        }

        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        print('create_order_response', '============', response.json())

        return response.json()

    @csrf_exempt
    def capture_order(self, order_id:str):


        url = self.paypal_path + f"/checkout/orders/{order_id}/capture"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }
        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()

            capture_data = response.json()
            print('response', '============', capture_data)

            return JsonResponse({
                "status": "success"
            })
        except Exception as e:
            print(e)
            return JsonResponse({
                "status": "error"
            }, status=500)