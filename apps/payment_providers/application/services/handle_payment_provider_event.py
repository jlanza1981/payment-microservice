import logging

from apps.payment_providers.application.process_paypal import ProcessPayPal

logger = logging.getLogger(__name__)


class HandlePaymentProviderEventService:
    """
    Servicio para manejar eventos de webhooks de proveedores de pago.
    """

    def handle(self, provider: str, payload: dict):
        if provider == "paypal":
            self._handle_paypal(payload)
        elif provider == "stripe":
            self._handle_stripe(payload)
        else:
            logger.warning(f"Proveedor de pago no soportado: {provider}")

    @staticmethod
    def _handle_paypal(payload):
        ProcessPayPal().process(payload)


    def _handle_stripe(self, payload):
        logger.info(f"Procesando evento Stripe: {payload.get('type')}")
        # TODO: Implementar manejo de eventos de Stripe
        # extraer datos, validar firma, llamar caso de uso correspondiente
