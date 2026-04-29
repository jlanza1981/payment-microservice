from django.apps import AppConfig


class PagosConfig(AppConfig):
    name = 'apps.pagos'
    verbose_name = 'Sistema de Pagos y Facturación'

    def ready(self):
        """
        Importa las señales cuando la aplicación está lista.
        Esto activa la creación automática de recibos cuando se registran pagos.
        """
        import apps.pagos.signals  # noqa: F401
