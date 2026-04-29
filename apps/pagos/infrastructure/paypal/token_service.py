import base64
import requests
from django.conf import settings


class PayPalTokenService:

    @staticmethod
    def get_access_token():
        url = f"{settings.PAYPAL_BASE_URL}/v1/oauth2/token"

        auth = base64.b64encode(
            f"{settings.PAYPAL_CLIENT_ID}:{settings.PAYPAL_SECRET}".encode()
        ).decode()

        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "grant_type": "client_credentials"
        }

        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()

        return response.json()["access_token"]