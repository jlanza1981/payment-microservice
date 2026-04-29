from decimal import Decimal
from typing import Dict, Any, Callable, Optional

from apps.instituciones.models import TiposCostoMaterial
from apps.orden_pagos.infrastructure.repository.headquarters_pricing_repository import HeadquartersPriceRepository
from apps.orden_pagos.application.dto import RegistrationDataRequest

class CalculateMaterialCostUseCase:
    """
    Caso de uso para calcular costo de material.
    """

    COST_TYPE_CONFIG: Dict[str, tuple[str, Callable[[Decimal, int, int, int], Decimal]]] = {
        'S': ('Semanal', lambda base, weeks, months, duration: base * (weeks or 0)),
        'M': ('Mensual', lambda base, weeks, months, duration: base * (months or 0)),
        'A': ('Anual', lambda base, weeks, months, duration: base),
        'T': ('Semestral', lambda base, weeks, months, duration: base * 2),
        'C': ('Programa Completo', lambda base, weeks, months, duration: base),
    }

    def __init__(self, repository: HeadquartersPriceRepository):
        self.repository = repository

    def execute(self, req: "RegistrationDataRequest") -> Dict[str, Any]:

        currency = self.repository.get_currency_by_headquarters(
            institution_id=req.institution_id,
            city_id=req.city_id,
            category_id=req.program_type_id
        ) or ''
        # Si es un programa "otros", no hay pricing específico
        if getattr(req, 'is_other_program', lambda: False)():
            return self._get_default_material_response(currency)

        if req.is_college:
            return self._get_college_material_cost(req, currency)
        else:
            return self._get_language_course_material_cost(req, currency)

    def _get_college_material_cost(
            self,
            args: "RegistrationDataRequest",
            currency: str
    ) -> Dict[str, Any]:

        program_pricing = self.repository.get_college_program_pricing(args)

        if not program_pricing or not getattr(program_pricing, "tipo_costo_material_internacional", None):
            return self._get_default_material_response(currency)

        international_material_cost = program_pricing.costo_material_internacional
        material_cost_type = program_pricing.tipo_costo_material_internacional
        duration = program_pricing.duracion or 1

        cost_type_obj = material_cost_type
        base_cost = international_material_cost
        months = round(args.weeks / 4)

        total_cost, type_description = self._calculate_material_total(
            base_cost=base_cost,
            cost_type=cost_type_obj.tipo,
            weeks=args.weeks,
            months=months,
            duration=duration
        )

        return {
            'material_cost': self._format_amount(base_cost),
            'material_cost_type_name': type_description,
            'material_cost_type': cost_type_obj.id,
            'total_material_cost': self._format_amount(total_cost),
            'duration': months,
            'currency': currency,
            'select_material_cost_type': TiposCostoMaterial.TIPOS_PRECIOS if not cost_type_obj
            else [],
        }

    def _get_language_course_material_cost(
            self,
            params: RegistrationDataRequest,
            currency: str
    ) -> Dict[str, Any]:

        prices_qs = self.repository.get_language_course_intensity(params)

        if not prices_qs or not prices_qs.tipo_costo_material:
            return self._get_default_material_response(currency)
        cost_type_obj = prices_qs.tipo_costo_material
        base_cost = prices_qs.costo_material

        # Calcular months basado en weeks (aproximadamente 4 semanas por mes)
        months = round(params.weeks / 4) if params.weeks else 0

        total_cost, type_description = self._calculate_material_total(
            base_cost=base_cost,
            cost_type=cost_type_obj.tipo,
            weeks=params.weeks,
            months=months,
            duration=params.weeks or 1
        )
        return {
            'material_cost': self._format_amount(base_cost),
            'material_cost_type_name': type_description,
            'material_cost_type': cost_type_obj.id,
            'total_material_cost': self._format_amount(total_cost),
            'duration': params.weeks,
            'currency': currency,

        }

    def _calculate_material_total(
            self,
            base_cost: Decimal,
            cost_type: str,
            weeks: int,
            months: Optional[int],
            duration: int
    ) -> tuple[Decimal, str]:
        """
        Calcula el total del costo de material según el tipo.
        """
        description, calculate_fn = self.COST_TYPE_CONFIG.get(
            cost_type,
            ('Único', lambda base, weeks, months, duration: base)
        )
        total_cost = calculate_fn(base_cost, weeks, months, duration)

        return total_cost, description


    def _get_default_material_response(self, currency:str) -> Dict[str, Any]:
        """Retorna respuesta por defecto para costo de material."""
        material_cost_type = self.repository.get_types_cost_material()
        return {
            'material_cost': '0.00',
            'material_cost_type_name': None,
            'material_cost_type': None,
            'total_material_cost': '0.00',
            'duration': 1,
            'currency': currency,
            'select_material_cost_type': [{'id': i.id, 'nombre': f"{i.nombre}"} for i in material_cost_type]
        }

    @staticmethod
    def _format_amount(amount: Decimal) -> str:
        """Formatea un monto decimal a string."""
        return f'{amount:,.2f}'
