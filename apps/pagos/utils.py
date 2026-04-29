
from decimal import Decimal

from apps.pagos.application.use_cases.get_fee_config import FeeConfigUseCase


def calculate_paypal_order_amount(target_amount, currency, is_international=True):
    target_amount = Decimal(target_amount)
    fee_config = FeeConfigUseCase().get_config(currency)

    fee_percentage = fee_config.base_percentage

    if is_international:
        fee_percentage += fee_config.international_percentage

    fixed_fee = fee_config.fixed_fee

    # Fórmula: (Neto deseado + fijo) / (1 - porcentaje total)
    amount_to_charge = (target_amount + fixed_fee) / (1 - fee_percentage)
    return round(amount_to_charge, 2)

def _calculate_eur_amount_with_conversion(self, target_amount):
    """
    Calcula cuánto debes cobrar en EUR para recibir
    monto_objetivo_usd neto después de fees y conversión.
    """
    # Convert Decimal to float for calculations
    target_amount = float(target_amount)

    tasa_eur_usd = self.exchange_rates_services.get_exchange_rate('EUR')  # Obtener tasa real desde API
    fixed_rate_eur = 0.35
    conversion_margin = 0.03
    fee_percentage_base = 0.0349
    # Convertimos el objetivo USD a EUR al tipo real
    target_amount_eur = target_amount/tasa_eur_usd

    # Fórmula que cubre comisión comercial + conversión
    amount_receive_eur = (
            (target_amount_eur + fixed_rate_eur)
            / ((1 - fee_percentage_base) * (1 - conversion_margin))
    )

    return round(amount_receive_eur, 2)