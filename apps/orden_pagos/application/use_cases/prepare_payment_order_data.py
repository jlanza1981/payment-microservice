from typing import Dict, Any

class PreparePaymentOrderDataUseCase:

    def __init__(
        self,
        repository_user,
        repository_opportunity,
    ):
        self.repositories = {
            'student': repository_user,
            'advisor': repository_user,
            'opportunity': repository_opportunity,
        }

    def execute(self, data_payment_order: Any) -> Dict[str, Any]:
        """
        Convierte los IDs de student, advisor y opportunity a instancias.
        Acepta diccionarios, dataclasses u otros objetos.
        """
        # Convertir a diccionario si es necesario
        if isinstance(data_payment_order, dict):
            payment_order = data_payment_order.copy()
        elif hasattr(data_payment_order, '__dict__'):
            payment_order = vars(data_payment_order).copy()
        else:
            payment_order = data_payment_order

        for field, repository in self.repositories.items():

            value = payment_order.get(field)

            if not value:
                continue

            # Si ya es una instancia (no es id)
            if not isinstance(value, (int, str)):
                continue

            instance = repository.get_by_id(value)

            if instance:
                payment_order[field] = instance

        return payment_order