from decimal import Decimal


class PreparePaymentAllocationsUseCase:

    def __init__(
        self,
        invoice_repository,
        payment_concept_repository
    ):
        self.invoice_repository = invoice_repository
        self.payment_concept_repository = payment_concept_repository

    def execute(self, invoice_details: list, payment_amount: Decimal = None, is_full_payment: bool = False, status: str = None) -> list:
        """
        Distribuye el monto del pago entre los detalles de la factura.
        
        IMPORTANTE: En pagos parciales subsecuentes, considera los allocations existentes
        para evitar duplicación y distribuir el nuevo pago solo sobre montos pendientes.
        
        Args:
            invoice_details: Lista de detalles de la factura
            payment_amount: Monto del pago a distribuir. Si es None, se asume pago completo.
            is_full_payment: Si True, marca todos los conceptos como PAID
            status: Status específico a aplicar. Si se proporciona, sobrescribe el status calculado automáticamente.
                    Si es None, se calcula automáticamente ('PAID' o 'PENDING') según la cobertura del pago.
        
        Returns:
            Lista de allocations con amount_applied y status correctos
        """
        allocations = []
        if not invoice_details:
            return allocations

        # Calcular total de la factura
        total_invoice = sum(
            Decimal(str(detail.get("sub_total") or detail.get("amount") or 0))
            for detail in invoice_details
        )

        # Monto restante a distribuir - asegurar que sea Decimal
        # Validar y convertir payment_amount
        if payment_amount is not None and str(payment_amount).strip():
            try:
                remaining_amount = Decimal(str(payment_amount))
            except (ValueError, TypeError, Exception):
                remaining_amount = total_invoice
        else:
            remaining_amount = total_invoice

        for detail in invoice_details:
            invoice_detail_id = detail.get("id")
            concept_id = detail.get("payment_concept")

            if not invoice_detail_id or not concept_id:
                continue

            payment_concept = self.payment_concept_repository.get_concept_by_id(concept_id)
            invoice_detail = self.invoice_repository.get_invoice_detail_by_id(invoice_detail_id)
            
            subtotal = Decimal(detail.get("sub_total") or detail.get("amount") or 0)
            
            # 🔍 VERIFICAR ALLOCATIONS EXISTENTES - Obtener instancias completas
            existing_allocations = self.invoice_repository.get_already_applied_allocations(invoice_detail_id)
            
            # Garantizar que siempre sea una lista (manejar None, QuerySet, etc.)
            try:
                if existing_allocations is None:
                    existing_allocations = []
                else:
                    existing_allocations = list(existing_allocations)
            except (TypeError, ValueError):
                existing_allocations = []
            
            # Separar allocations por status (solo si hay elementos)
            paid_allocations = []
            pending_allocations = []
            
            if existing_allocations:
                paid_allocations = [a for a in existing_allocations if hasattr(a, 'status') and a.status == 'PAID']
                pending_allocations = [a for a in existing_allocations if hasattr(a, 'status') and a.status == 'PENDING']
            
            # Calcular el monto ya pagado (solo PAID)
            already_paid = sum(a.amount_applied for a in paid_allocations)
            
            # Calcular el monto pendiente en allocations PENDING
            pending_in_allocations = sum(a.amount_applied for a in pending_allocations)
            
            # Calcular el monto TOTAL ya aplicado/asignado (PAID + PENDING)
            total_already_applied = already_paid + pending_in_allocations
            
            # Calcular cuánto FALTA por asignar en este concepto
            pending_amount = subtotal - total_already_applied

            # Si ya está completamente cubierto (PAID + PENDING), saltar este concepto
            # No crear allocations duplicados
            if pending_amount <= 0:
                continue

            # Determinar cuánto se aplica a este detalle del NUEVO pago
            if is_full_payment:
                # Pago completo: aplicar todo lo que falta
                amount_applied = pending_amount
                allocation_status = 'PAID'
            else:
                # Pago parcial: distribuir lo que quede disponible
                if remaining_amount >= pending_amount:
                    # Cubre completamente lo que falta de este concepto
                    amount_applied = pending_amount
                    allocation_status = 'PAID'
                    remaining_amount -= pending_amount
                elif remaining_amount > 0:
                    # Cubre parcialmente lo que falta
                    amount_applied = remaining_amount
                    allocation_status = 'PENDING'
                    remaining_amount = Decimal('0.00')
                else:
                    # No hay dinero disponible para este concepto
                    continue

            # Si se pasó un status específico, usarlo; sino usar el calculado
            final_status = status if status is not None else allocation_status

            # Solo crear allocation si hay monto aplicado en ESTE pago
            if amount_applied > 0:
                allocations.append({
                    "invoice_detail": invoice_detail,
                    "payment_concept": payment_concept,
                    "amount_applied": amount_applied,
                    "status": final_status
                })

        return allocations