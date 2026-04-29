from api import settings


class DomainHelper:
    """Helper para obtener domain_name en diferentes contextos."""
    
    @staticmethod
    def from_request(request) -> str:
        try:
            return request.build_absolute_uri('/')[:-1]
        except:
            return settings.DOMAIN_NAME
    
    @staticmethod
    def from_settings() -> str:
        return getattr(settings, 'DOMAIN_NAME', settings.DOMAIN_NAME)


# Shortcuts para compatibilidad
get_domain_name_from_request = DomainHelper.from_request
get_domain_name = DomainHelper.from_settings

