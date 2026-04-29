# apps/orden_pagos/application/use_cases/calculate_registration_fee.py
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Any, List, Optional

from apps.orden_pagos.infrastructure.repository.registration_fee_repository import RegistrationFeeRepository


@dataclass
class RegistrationFeeData:
    """Datos del precio de inscripción obtenidos del repositorio."""
    base_amount: Decimal
    discount_percentage: Decimal
    registration_name: str
    currency: str


class CalculateRegistrationFeeUseCase:
    """
    Caso de uso para calcular el precio de inscripción de una sede.
    Aplica descuentos según la configuración de la sede.

    Responsabilidades:
    - Obtener datos de inscripción de la sede
    - Calcular descuentos aplicables
    - Formatear respuesta con totales y descuentos
    """

    DEFAULT_CURRENCY = 'USD'
    DEFAULT_REGISTRATION_NAME = 'Inscripción'
    DISCOUNT_NAME = 'Descuento LC'
    DISCOUNT_TYPE_PERCENTAGE = 'percentage'

    def __init__(self, repository: RegistrationFeeRepository):
        self.repository = repository

    def execute(
            self,
            institution_id: int,
            city_id: int,
            program_type_id: int
    ) -> Dict[str, Any]:
        """
        Calcula el precio de inscripción con descuentos aplicados.
        """
        fee_data = self._get_registration_fee_data(
            institution_id, city_id, program_type_id
        )

        total_amount, discounts = self._calculate_total_with_discounts(
            fee_data.base_amount,
            fee_data.discount_percentage
        )

        return self._build_response(
            base_amount=fee_data.base_amount,
            discount_percentage=fee_data.discount_percentage,
            total_amount=total_amount,
            currency=fee_data.currency,
            discounts=discounts,
            registration_name=fee_data.registration_name
        )

    def _get_registration_fee_data(
            self,
            institution_id: int,
            city_id: int,
            program_type_id: int
    ) -> RegistrationFeeData:
        """
        Obtiene los datos de inscripción desde el repositorio.

        Returns:
            RegistrationFeeData con los datos de inscripción o valores por defecto
        """
        currency = self._get_currency(institution_id, city_id, program_type_id)
        registration_price = self._get_registration_price(
            institution_id, city_id, program_type_id
        )

        if registration_price:
            return RegistrationFeeData(
                base_amount=registration_price['price'],
                discount_percentage=registration_price['discount_percentage'],
                registration_name=registration_price['description'],
                currency=currency
            )

        return self._get_default_fee_data(currency)

    def _get_currency(
            self,
            institution_id: int,
            city_id: int,
            program_type_id: int
    ) -> str:
        """Obtiene la moneda de la sede o retorna la moneda por defecto."""
        currency = self.repository.get_currency_by_institution_and_city(
            institution_id=institution_id,
            city_id=city_id,
            program_type_id=program_type_id
        )
        return currency or self.DEFAULT_CURRENCY

    def _get_registration_price(
            self,
            institution_id: int,
            city_id: int,
            program_type_id: int
    ) -> Optional[Dict[str, Any]]:
        """Obtiene el precio de inscripción desde el repositorio."""
        return self.repository.get_registration_price_by_sede(
            institution_id=institution_id,
            city_id=city_id,
            program_type_id=program_type_id
        )

    def _get_default_fee_data(self, currency: str) -> RegistrationFeeData:
        """Retorna datos por defecto cuando no se encuentra precio de inscripción."""
        return RegistrationFeeData(
            base_amount=Decimal('0.00'),
            discount_percentage=Decimal('0.00'),
            registration_name=self.DEFAULT_REGISTRATION_NAME,
            currency=currency
        )

    def _calculate_total_with_discounts(
            self,
            base_amount: Decimal,
            discount_percentage: Decimal
    ) -> tuple[Decimal, List[Dict[str, Any]]]:
        """
        Calcula el total aplicando descuentos porcentuales.
        """
        if discount_percentage <= 0:
            return base_amount, []

        discount_amount = self._calculate_discount_amount(
            base_amount, discount_percentage
        )
        total_amount = base_amount - discount_amount

        discount_detail = self._build_discount_detail(
            discount_percentage, discount_amount
        )

        return total_amount, [discount_detail]

    @staticmethod
    def _calculate_discount_amount(
            base_amount: Decimal,
            discount_percentage: Decimal
    ) -> Decimal:
        """Calcula el monto del descuento."""
        return base_amount * (discount_percentage / Decimal('100'))

    def _build_discount_detail(
            self,
            discount_percentage: Decimal,
            discount_amount: Decimal
    ) -> Dict[str, Any]:
        """Construye el detalle de un descuento."""
        return {
            'name': self.DISCOUNT_NAME,
            'percentage': int(discount_percentage),
            'discount_amount': self._format_amount(discount_amount),
            'type': self.DISCOUNT_TYPE_PERCENTAGE
        }

    def _build_response(
            self,
            base_amount: Decimal,
            discount_percentage: Decimal,
            total_amount: Decimal,
            currency: str,
            discounts: List[Dict[str, Any]],
            registration_name: str
    ) -> Dict[str, Any]:
        """Construye la respuesta formateada del caso de uso."""
        return {
            'amount': self._format_amount(base_amount),
            'discount_percentage': int(discount_percentage),
            'fixed_discount': self._format_amount(Decimal('0.00')),
            'currency': currency,
            'total_amount': self._format_amount(total_amount),
            'discounts': discounts,
            'registration_name': registration_name
        }

    @staticmethod
    def _format_amount(amount: Decimal) -> str:
        """Formatea un monto decimal a string con separadores de miles y 2 decimales."""
        return f'{amount:,.2f}'
