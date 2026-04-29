from apps.pagos.application.helpers.domain_helper import DomainHelper

def get_domain_name_from_request(request) -> str:
    return DomainHelper.from_request(request)

def get_domain_name() -> str:
    return DomainHelper.from_settings()

