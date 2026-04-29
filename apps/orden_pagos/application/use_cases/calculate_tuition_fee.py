from decimal import Decimal
from typing import Dict, Any, Optional

from apps.orden_pagos.infrastructure.repository.headquarters_pricing_repository import HeadquartersPriceRepository
from apps.orden_pagos.application.dto import RegistrationDataRequestOutput, RegistrationDataRequest


class CalculateTuitionFeeUseCase:

    PROGRAM_TYPE_UNIVERSITY = ('U', 'S')  # Universidad, Superior
    PROGRAM_TYPE_LANGUAGE = ('I', 'C', 'L')    # Idioma, Campamento, online
    PRICE_TYPE_SEMESTER = 'S'
    PRICE_TYPE_ANNUAL = 'A'

    def __init__(self, repository: HeadquartersPriceRepository):
        self.repository = repository

    def execute(self, params: RegistrationDataRequest) -> Dict[str, Any]:

        if not params.program_id or params.program_code == 'O':
            return self._get_default_response(params)

        program_type = self.repository.get_program_type(params.program_id)

        if not program_type:
            return self._get_default_response(params)

        if program_type in self.PROGRAM_TYPE_UNIVERSITY:
            return self._calculate_college_tuition(params)

        elif program_type in self.PROGRAM_TYPE_LANGUAGE:
            return self._calculate_language_course_tuition(params)

        return self._get_default_response(params)

    def _calculate_college_tuition(self, params: RegistrationDataRequest) -> Dict[str, Any]:

        program_pricing = self.repository.get_college_program_pricing(params)
        if not program_pricing:
            return self._get_default_response(params)

        international_price = Decimal(program_pricing.precio_internacional)
        discount_percentage = program_pricing.descuento_inter_porc
        discount_fixed = Decimal(program_pricing.descuento_inter_fijo)
        currency = program_pricing.sede.pais.currency_symbol if program_pricing.sede.pais else ''

        lc_price = self._apply_discount(
            base_price=international_price,
            discount_percentage=Decimal(discount_percentage),
            discount_fixed=discount_fixed
        )

        total_tuition, semesters, semester_price, semester_lc_price = self._calculate_total_by_price_type(
            lc_price=lc_price,
            institution_price=international_price,
            price_type=program_pricing.tipo_precio,
            duration_type=params.duration_type,
            weeks=params.weeks
        )

        output = RegistrationDataRequestOutput(
            duration_type=params.duration_type,
            weeks=params.weeks,
            lc_discount_percentage=Decimal(program_pricing.descuento_inter_porc),
            lc_discount_fixed=Decimal(discount_fixed).quantize(Decimal('0.01')),
            lc_price=Decimal(lc_price).quantize(Decimal('0.01')),
            institution_price=Decimal(international_price).quantize(Decimal('0.01')),
            total_tuition=Decimal(total_tuition).quantize(Decimal('0.01')),
            currency=currency,
            price_range=None,
            duration=None,
            price_week=None,
            semesters=semesters,
            semester_price=Decimal(semester_price).quantize(Decimal('0.01')),
            semester_lc_price=Decimal(semester_lc_price).quantize(Decimal('0.01')),
            is_college=True
        )

        return output.model_dump(exclude_none=True)

    def _calculate_language_course_tuition(self, params: RegistrationDataRequest) -> Dict[str, Any]:
        prices_qs = self.repository.get_language_course_prices(params)

        if not prices_qs or not prices_qs.exists():
            return self._get_default_response(params)

        # Encontrar el precio aplicable según el rango de semanas
        price_info = self.find_prices_by_week_range(pricing=prices_qs, weeks=params.weeks)

        is_weekly_price = self._is_weekly_price(price_info['price_range'])

        if is_weekly_price:
            total_tuition = Decimal(price_info['price_week']) * params.weeks
        else:
            total_tuition = Decimal(price_info['price_week'])

        currency = self.repository.get_currency_by_headquarters(
            institution_id=params.institution_id,
            city_id=params.city_id,
            category_id=params.program_type_id
        ) or ''

        output = RegistrationDataRequestOutput(
                duration_type=params.duration_type,
                duration=params.weeks,
                lc_discount_percentage=Decimal(price_info['lc_discount_percentage']),
                lc_discount_fixed=Decimal(price_info['lc_discount_fixed']).quantize(Decimal('0.01')),
                price_week=Decimal(price_info['price_week']).quantize(Decimal('0.01')),
                institution_price=Decimal(price_info['institution_price']).quantize(Decimal('0.01')),
                total_tuition=Decimal(total_tuition).quantize(Decimal('0.01')),
                currency=currency,
                price_range=price_info['price_range'],
                is_extension=params.is_extension
            )

        return output.model_dump(exclude_none=True)

    @staticmethod
    def _apply_discount(
            base_price: Decimal,
            discount_percentage: Decimal,
            discount_fixed: Decimal
    ) -> Decimal:

        if discount_percentage > 0:
            discount_amount = base_price * (discount_percentage / Decimal('100'))
            return base_price - discount_amount
        elif discount_fixed > 0:
            return base_price - discount_fixed

        return base_price

    def _calculate_total_by_price_type(
            self,
            lc_price: Decimal,
            institution_price: Decimal,
            price_type: str,
            duration_type: str,
            weeks: int
    ) -> tuple[Decimal, int, Decimal, Decimal]:

        semesters = 0
        semester_price = Decimal('0.00')
        semester_lc_price = Decimal('0.00')

        if price_type == self.PRICE_TYPE_SEMESTER:
            semester_price = institution_price
            semester_lc_price = lc_price
            annual_lc_price = lc_price * 2

            if duration_type == 'A':
                semesters = weeks * 2
                total_tuition = annual_lc_price * weeks
            elif duration_type == 'S':
                semesters = weeks
                total_tuition = lc_price * Decimal(weeks / 2)
            else:
                semesters = weeks * 2
                total_tuition = annual_lc_price
        elif price_type == self.PRICE_TYPE_ANNUAL:
            if duration_type == 'S':
                total_tuition = lc_price * Decimal(weeks / 2)
            elif duration_type == 'A':
                total_tuition = lc_price * weeks
            else:
                total_tuition = lc_price
        else:
            total_tuition = lc_price

        return total_tuition, semesters, semester_price, semester_lc_price

    @staticmethod
    def _is_weekly_price(price_range: Optional[str]) -> bool:
        """
        Determina si el precio es semanal o fijo basándose en el rango.
        Si el rango tiene el mismo valor inicial y final, es precio fijo.
        """
        if not price_range:
            return True

        parts = price_range.replace('+', '').split('-')
        if len(parts) == 2:
            return parts[0] != parts[1]
        return True

    def _get_default_response(self, params: RegistrationDataRequest) -> Dict[str, Any]:

        currency = self.repository.get_currency_by_headquarters(
            institution_id=params.institution_id,
            city_id=params.city_id,
            category_id=params.program_type_id
        )

        output = RegistrationDataRequestOutput(
            duration_type=params.duration_type,
            duration=params.weeks,
            currency=currency,
            is_college=params.is_college,
            is_extension=params.is_extension
        )

        return output.model_dump(exclude_none=True)

    @staticmethod
    def find_prices_by_week_range(pricing, weeks: int):
         result = {
             'price_week': Decimal('0.00'),
             'duration': weeks,
             'institution_price': Decimal('0.00'),
             'lc_discount_percentage': Decimal('0.00'),
             'lc_discount_fixed': Decimal('0.00'),
             'price_range': None
         }
         for price in pricing:
             if price.semana2 != '+':
                 # Rango cerrado
                 if price.semana1 <= weeks <= int(price.semana2):
                     result.update({
                         'price_week': price.monto_lc or Decimal('0.00'),
                         'institution_price': price.monto_inst or Decimal('0.00'),
                         'lc_discount_percentage': price.descuento_lc or Decimal('0.00'),
                         'lc_discount_fixed': price.descuento_lc_fijo or Decimal('0.00'),
                         'price_range': f"{price.semana1}-{price.semana2}"
                     })
                     break
             else:
                 # Rango abierto (ej: 12+)
                 if weeks >= price.semana1:
                     result.update({
                         'price_week': price.monto_lc or Decimal('0.00'),
                         'institution_price': price.monto_inst or Decimal('0.00'),
                         'lc_discount_percentage': price.descuento_lc or Decimal('0.00'),
                         'lc_discount_fixed': price.descuento_lc_fijo or Decimal('0.00'),
                         'price_range': f"{price.semana1}+"
                     })
                     break
         return result
