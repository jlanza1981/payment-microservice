"""
DTOs compartidos para la capa de aplicación.
Estos DTOs pueden ser usados por use cases, repositorios y servicios.
"""
from .registration_data_request import RegistrationDataRequest
from .output_registration_data_request import RegistrationDataRequestOutput

__all__ = [
    'RegistrationDataRequest',
    'RegistrationDataRequestOutput',
]
