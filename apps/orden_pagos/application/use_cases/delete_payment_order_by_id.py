from django.db import transaction

from apps.orden_pagos.domain.interface.repository.repository_interface import PaymentOrderRepositoryInterface


class DeletePaymentOrderByIdUseCase:
    """
    Caso de uso: Anular (soft delete) una orden de pago.

    Las órdenes NO se eliminan físicamente, solo se anulan (status = CANCELLED).
    Solo se pueden anular órdenes en estado PENDING.
    """

    def __init__(self, repository: PaymentOrderRepositoryInterface):
        self.repository = repository

    @transaction.atomic
    def execute(self, command) -> bool:
        """
        Anula una orden de pago usando el método cancel() del modelo.

        Args:
            command: DeletePaymentOrderCommand con el order_id

        Returns:
            bool: True si se anuló correctamente, False si no se puede anular

        Nota:
            - Retorna True si la orden se anuló exitosamente (PENDING → CANCELLED)
            - Retorna False si la orden no existe o no está en estado PENDING
        """
        # Delegar al repositorio que usa el método cancel() del modelo
        return self.repository.delete(command.order_id)
