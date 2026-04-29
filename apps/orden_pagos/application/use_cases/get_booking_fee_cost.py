from decimal import Decimal
from typing import Dict, Any, Optional

from apps.orden_pagos.infrastructure.repository.headquarters_pricing_repository import HeadquartersPriceRepository


class GetBookingFeeCostUseCase:

    def __init__(self, repository: HeadquartersPriceRepository):
        self.repository = repository

    def execute(
        self,
        institution_id: int,
        city_id: int,
        program_type_id: int,
        accommodation_plan_id: Optional[int] = None
    ) -> Dict[str, Any]:

        booking_fee_cost = self.repository.get_booking_fee_cost(
            institution_id=institution_id,
            city_id=city_id,
            category_id=program_type_id,
            accommodation_plan_id=accommodation_plan_id
        )

        if not booking_fee_cost:
            return self._get_default_response()

        # Obtener moneda desde la sede
        currency = booking_fee_cost.sede.pais.currency_symbol if booking_fee_cost.sede.pais else ''

        return {
            'plan_id': booking_fee_cost.id,
            'plan_name': booking_fee_cost.nombre,
            'description': booking_fee_cost.descripcion,
            'accommodation_type': booking_fee_cost.tipo.descripcion if booking_fee_cost.tipo else None,
            'accommodation_type_id': booking_fee_cost.tipo_id,
            'amount': self._format_amount(booking_fee_cost.costo_reservacion),
            'weekly_cost': self._format_amount(booking_fee_cost.costo_semana),
            'daily_cost': self._format_amount(booking_fee_cost.costo_diario),
            'currency': currency,
            'headquarters_id': booking_fee_cost.sede_id,
            'headquarters_name': booking_fee_cost.sede.nombre if booking_fee_cost.sede else None,
        }

    @staticmethod
    def _get_default_response() -> Dict[str, Any]:
        """
        Retorna respuesta por defecto cuando no se encuentra el plan de alojamiento.
        """
        return {
            'plan_id': None,
            'plan_name': None,
            'description': None,
            'accommodation_type': None,
            'accommodation_type_id': None,
            'reservation_cost': '0.00',
            'weekly_cost': '0.00',
            'daily_cost': '0.00',
            'currency': '',
            'headquarters_id': None,
            'headquarters_name': None,
        }

    @staticmethod
    def _format_amount(amount: Decimal) -> str:
        """Formatea un monto decimal a string con separadores de miles y 2 decimales."""
        return f'{amount:,.2f}'
