from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'

    def ready(self):
        """
        Registrar event handlers cuando la aplicación esté lista.
        """

        from apps.core.domain.events.inbox_event_created import InboxEventCreated
        from apps.core.domain.events.event_dispatcher import EventDispatcher
        from apps.core.infrastructure.inbox.event_handlers import handle_inbox_event_created
        # Registrar handler para InboxEventCreated
        EventDispatcher.register(InboxEventCreated, handle_inbox_event_created)  # type: ignore[arg-type]