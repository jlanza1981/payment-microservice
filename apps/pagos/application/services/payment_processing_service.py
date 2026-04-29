from decimal import Decimal
from typing import Dict, Any

from apps.pagos.application.commands import CreatePaymentCommand
from apps.pagos.models import Payment

class PaymentProcessingService:

    @staticmethod
    def validate_payment_data(payment_data: CreatePaymentCommand) -> Dict[str, Any]:
        """  Valida que los datos del pago sean correctos.   """
        from dataclasses import is_dataclass, asdict
        if is_dataclass(payment_data):
            raw_data = asdict(payment_data)
        elif isinstance(payment_data, dict):
            raw_data = payment_data
        else:
            raw_data = getattr(payment_data, '__dict__', {})

        required_fields = ['user', 'amount', 'payment_method', 'currency']

        for field in required_fields:
            if field not in raw_data or raw_data[field] is None:
                raise ValueError(f"Campo requerido faltante: {field}")

        # Validar monto positivo
        amount = raw_data.get('amount_paid')
        try:
            # Convertir a Decimal independientemente del tipo (int, float, str, Decimal)
            amount_decimal = Decimal(amount)
            print('amount_decimal', amount_decimal)
            if amount_decimal <= 0:
                raise ValueError("El monto debe ser mayor a 0")
        except (ValueError, TypeError, ArithmeticError) as e:
            raise ValueError(f"El monto debe ser un número válido: {e}")

        # Validar metodo de pago
        payment_method = Payment._meta.get_field('payment_method')
        choices = getattr(payment_method, 'choices', None)
        if not choices:
            raise ValueError("No hay choices definidos para el campo 'payment_method' en el modelo Payment")

        method_valid = [valor for valor, _ in choices]
        if raw_data.get('payment_method') not in method_valid:
            raise ValueError(
                f"Método de pago inválido. Debe ser uno de: {', '.join(method_valid)}"
            )
        return raw_data




