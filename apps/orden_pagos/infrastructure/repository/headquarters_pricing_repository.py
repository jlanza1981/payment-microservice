# apps/orden_pagos/infrastructure/repository/headquarters_pricing_repository.py
from typing import Optional, Dict, Any, List

from django.db.models import QuerySet

from apps.instituciones.models import (
    Sedes,
    Programas_sedes,
    Cursos_sedes,
    Cursos_sedes_intensidad,
    Curso_precio,
    Curso_precio_paises,
    Cursos,
    PlanPagoSedes, TiposCostoMaterial
)
from apps.orden_pagos.domain.exceptions import GenericDomainException
from apps.orden_pagos.application.dto import RegistrationDataRequest


class HeadquartersPriceRepository:
    """
    Repositorio para gestión de precios de programas y cursos por sede.
    Maneja tanto programas universitarios (College) como cursos de idiomas.
    """
    @staticmethod
    def get_currency_by_headquarters(
            institution_id: int,
            city_id: int,
            category_id: int
    ) -> Optional[str]:
        headquarters = Sedes.objects.filter(
            institucion_id=institution_id,
            ciudad_id=city_id,
            categoria__id__in=(category_id,)
        ).select_related('pais').first()

        return headquarters.pais.currency_symbol if headquarters and headquarters.pais else None

    @staticmethod
    def get_college_program_pricing(
            args: RegistrationDataRequest
    ) -> Optional[Programas_sedes]:

        program_id = args.program_id
        institution_id = args.institution_id
        city_id = args.city_id
        category_id = args.program_type_id

        if not all([program_id, institution_id, city_id, category_id]):
            return None

        headquarters_program = Programas_sedes.objects.filter(
            curso_id=program_id,
            sede__ciudad_id=city_id,
            sede__institucion_id=institution_id,
            sede__categoria__id__in=(category_id,)
        ).select_related('sede', 'sede__pais', 'tipo_costo_material_internacional').first()

        return headquarters_program

    @staticmethod
    def get_headquarters_course(
        args: RegistrationDataRequest,
    ) -> Optional[Cursos_sedes]:

        headquarters_course = (
            Cursos_sedes.objects.filter(
                curso_id=args.program_id,
                sede__ciudad_id=args.city_id,
                sede__institucion_id=args.institution_id,
                sede__categoria__id__in=(args.program_type_id,)
            )
            .select_related("sede", "sede__pais")
            .first()
        )
        return headquarters_course

    @staticmethod
    def get_language_course_intensity(
        args: RegistrationDataRequest,
    ) -> Optional[Cursos_sedes_intensidad]:

        headquarters_course = HeadquartersPriceRepository.get_headquarters_course(args)
        if not headquarters_course:
            raise GenericDomainException('No se encontró el curso por sede con los datos proporcionados')

        course_intensity = (
            Cursos_sedes_intensidad.objects.filter(
                curso_sede=headquarters_course, intensidad_id=args.intensity_id
            )
            .select_related("tipo_costo_material")
            .first()
        )

        return course_intensity

    @staticmethod
    def get_language_course_prices(
        args: RegistrationDataRequest,
    ) -> Optional[QuerySet[Curso_precio]]:

        course_intensity = HeadquartersPriceRepository.get_language_course_intensity(args)
        if not course_intensity:
            raise GenericDomainException('No se encontró la intensidad para el curso seleccionado')

        countries_ids = (
            Curso_precio_paises.objects.filter(
                pais_id=args.country_id, curso_precio__curso_sede_intensidad=course_intensity
            )
            .values_list("curso_precio_id", flat=True)
        )

        prices = (
            Curso_precio.objects.filter(
                curso_sede_intensidad_id=course_intensity.id, id__in=countries_ids
            )
            .order_by("semana1")
        )
        return prices

    @staticmethod
    def get_program_type(program_id: int) -> Optional[str]:
        try:
            curso = Cursos.objects.select_related('categoria').get(id=program_id)
            return curso.categoria.tipo
        except Cursos.DoesNotExist:
            return None

    @staticmethod
    def get_booking_fee_cost(
        institution_id: int,
        city_id: int,
        category_id: int,
        accommodation_plan_id: Optional[int] = None
    ) -> Optional[PlanPagoSedes]:
        """
        Obtiene el costo de reservación de alojamiento para una sede específica.
        """
        # Obtener la sede
        headquarters = Sedes.objects.filter(
            institucion_id=institution_id,
            ciudad_id=city_id,
            categoria__id__in=(category_id,)
        ).first()

        if not headquarters:
            return None

        # Filtrar por plan específico si se proporciona
        query = PlanPagoSedes.objects.filter(sede=headquarters).select_related('sede', 'sede__pais', 'tipo')

        if accommodation_plan_id:
            query = query.filter(id=accommodation_plan_id)

        return query.first()
    @staticmethod
    def get_types_cost_material() -> QuerySet[TiposCostoMaterial, TiposCostoMaterial]:
        return TiposCostoMaterial.objects.filter(activo=True)
