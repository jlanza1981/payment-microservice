# apps/orden_pagos/infrastructure/repository/registration_fee_repository.py
from decimal import Decimal
from typing import Optional, Dict, Any
from apps.instituciones.models import Sedes, PreciosFijosSedes


class RegistrationFeeRepository:
    """Repositorio para gestión de precios de inscripción por sede."""

    def get_currency_by_institution_and_city(
            self,
            institution_id: int,
            city_id: int,
            program_type_id: int
    ) -> Optional[str]:

        sede = Sedes.objects.filter(
            institucion_id=institution_id,
            ciudad_id=city_id,
            categoria__id__in=(program_type_id,)
        ).select_related('pais').first()

        if sede and sede.pais:
            return sede.pais.currency_symbol
        return None

    def get_registration_price_by_sede(
            self,
            institution_id: int,
            city_id: int,
            program_type_id: int
    ) -> Optional[Dict[str, Any]]:

        fixed_price = PreciosFijosSedes.objects.filter(
            sede__institucion_id=institution_id,
            sede__ciudad_id=city_id,
            tipo__tipo='I',  # Tipo 'I' = Inscripción
            sede__categoria__id__in=(program_type_id,)
        ).select_related('sede', 'tipo').first()

        if fixed_price:
            return {
                'price': Decimal(fixed_price.precio),
                'discount_percentage': Decimal(fixed_price.descuento),
                'description': fixed_price.descripcion_precio
            }
        return None
