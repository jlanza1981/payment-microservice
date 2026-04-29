import json

from django.http import HttpResponse
from ninja import Router

from apps.payment_providers.application.services.handle_payment_provider_event import HandlePaymentProviderEventService

router_paypal = Router(tags=["Paypal"], auth=None)

@router_paypal.post("/webhooks/")
def paypal_webhook(request):
    try:
        # request.body es bytes, json.loads convierte a dict
        event = json.loads(request.body)
        HandlePaymentProviderEventService().handle(provider="paypal", payload=event)
        return HttpResponse(status=200)
    except json.JSONDecodeError:
        return HttpResponse("Invalid JSON", status=400)

