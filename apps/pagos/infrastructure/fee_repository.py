from typing import Optional

from apps.pagos.models import FeeConfig


class FeeRepository:
    def __init__(self):
        pass

    @staticmethod
    def get_fee_config(currency:str) -> Optional[FeeConfig]:
        try:
            fee_config = FeeConfig.objects.get(currency=currency, is_active=True)
        except FeeConfig.DoesNotExist:
            raise ValueError(f"No hay configuración de fees para la moneda {currency}")

        return fee_config