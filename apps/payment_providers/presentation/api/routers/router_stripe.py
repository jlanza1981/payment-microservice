from ninja import Router

from apps.payment_providers.application.services.handle_payment_provider_event import HandlePaymentProviderEventService

router_stripe = Router(tags=["Stripe"], auth=None)

@router_stripe.post("/webhooks/")
def paypal_webhook(request):

    event = request.json()

    HandlePaymentProviderEventService().handle(
        provider="paypal",
        payload=event
    )

    return {"ok": True}
