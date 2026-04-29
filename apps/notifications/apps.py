from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications_message'
    verbose_name = 'Notificaciones'

    def ready(self):
        """
        Método ejecutado cuando la aplicación está lista.
        Aquí se pueden importar señales u otras configuraciones.
        """
        pass

