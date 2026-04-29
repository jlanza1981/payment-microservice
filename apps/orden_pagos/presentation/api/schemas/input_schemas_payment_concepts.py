from ninja import Schema
from pydantic import Field
from typing import Optional, List


class AdditionalDataForConceptInputSchema(Schema):

    payment_concept_ids: List[int] = Field(..., description="Lista de IDs de conceptos de pago (ej: [1, 2, 3])")
    country_origin_id: str = Field(..., description="ID del país")
    institution_id: Optional[int] = Field(None, description="ID de la institución")
    city_id: Optional[int] = Field(None, description="ID de la ciudad")
    program_type_id: Optional[int] = Field(None, description="ID del tipo de programa (categoría)")

    # Campos para matrícula / material
    program_id: Optional[int] = Field(None, description="ID del programa (si aplica)")
    program_code: Optional[str] = Field(None, description="Código especial del programa: 'O' para otros")
    weeks: Optional[int] = Field(None, description="Número de semanas")
    intensity_id: Optional[int] = Field(None, description="ID de la intensidad (requerida para idioma)")
    is_college: bool = Field(False, description="True si es programa universitario (College), False si es idioma")
    is_extension: bool = Field(False, description="True si matricula es para extensión de programa")

    # Campos para matrícula/extensión
    duration_type: Optional[str] = Field(None, description="Tipo de duración (S=Semanal, M=Mensual, etc.)")
    extension_weeks: Optional[int] = Field(None, description="Semanas de extensión, si aplica")
