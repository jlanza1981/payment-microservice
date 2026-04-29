from django.apps import AppConfig


class BillingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.billing'

    def ready(self):
        """
        Registrar event handlers cuando la aplicación esté lista.
        Esto permite que billing reaccione a eventos de otros bounded contexts.
        """

        from apps.core.domain.events.payment_captured_event import PaymentCapturedEvent
        from apps.core.domain.events.event_dispatcher import EventDispatcher
        from apps.billing.events.event_handlers import handle_payment_captured

        # Registrar handler para el evento PaymentCaptured
        EventDispatcher.register(PaymentCapturedEvent, handle_payment_captured)  # type: ignore
