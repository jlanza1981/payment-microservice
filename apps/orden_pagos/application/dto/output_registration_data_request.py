from decimal import Decimal

from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator

class RegistrationDataRequestOutput(BaseModel):
    duration_type: str = Field(..., description="Tipo de duración: 'A' para años, 'S' para semestres, 'W' para semanas")
    duration: Optional[int] = Field(None, gt=0, description="Número de semanas del programa (para cursos de idiomas)")
    weeks: Optional[int] = Field(None, gt=0, description="Número de semanas/años/semestres (para college)")
    lc_discount_percentage: Optional[Decimal] = Field(None, description="Descuento porcentual aplicado")
    lc_discount_fixed: Optional[Decimal] = Field(None, description="Descuento fijo aplicado")
    lc_price: Optional[Decimal] = Field(None, description="Precio LC con descuento (para college)")
    price_week: Optional[Decimal] = Field(None, description="Precio semanal del curso de idiomas")
    institution_price: Optional[Decimal] = Field(None, description="Precio de la institución")
    total_tuition: Optional[Decimal] = Field(None, description="Precio total de la matrícula")
    currency: Optional[str] = Field(None, description="Moneda del precio")
    is_college: bool = False
    is_extension: Optional[bool] = False
    price_range: Optional[str] = Field(None, description="Rango de precio aplicado (solo para cursos de idiomas)")
    semesters: Optional[int] = Field(None, description="Número de semestres (solo para programas universitarios)")
    semester_price: Optional[Decimal] = Field(None, description="Precio por semestre (solo para programas universitarios)")
    semester_lc_price: Optional[Decimal] = Field(None, description="Precio por semestre con descuento (solo para programas universitarios)")

