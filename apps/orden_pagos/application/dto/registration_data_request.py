from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator

class RegistrationDataRequest(BaseModel):
    """DTO de entrada para cálculo de costo de material.
    Permite especificar un programa por ID o usar el código 'O' para 'otros'.
    """
    # Si hay un programa concreto, ID > 0
    program_id: Optional[int] = Field(None, gt=0)
    # Alternativa: código especial 'O' (otros)
    program_code: Optional[str] = Field(None, description="Código especial del programa: 'O' para otros")
    PaymentDescriptionComponent: Optional[str] = Field(None, description="Descripción adicional para el concepto de pago")
    duration_type: str = Field(..., min_length=1, max_length=1)  # 'A' = Año, 'S' = Semestre, 'w' = Weeks
    institution_id: int = Field(..., gt=0)
    city_id: int = Field(..., gt=0)
    country_id: str = Field(..., min_length=2, max_length=3)
    program_type_id: int = Field(..., gt=0)
    weeks: int = Field(..., gt=0)
    intensity_id: Optional[int] = Field(None, gt=0)
    is_college: bool = False
    is_extension: bool = False


    @field_validator('program_code')
    def normalize_program_code(cls, v):
        if v is None:
            return v
        v = v.strip().upper()
        if v != 'O':
            raise ValueError("program_code debe ser 'O' para indicar 'otros'")
        return v

    @model_validator(mode='after')
    def ensure_program_specified(self):
        # Debe venir program_id (>0) o program_code == 'O'
        if self.program_id is None and (self.program_code or '').upper() != 'O':
            raise ValueError("Debe especificar 'program_id' (>0) o 'program_code'='O' para 'otros'")
        return self

    @model_validator(mode='after')
    def validate_intensity_for_language(self):
        # Si no es college, la intensidad es obligatoria
        if self.intensity_id is None and not self.is_college:
            raise ValueError('intensity_id es requerido para cursos de idiomas')
        return self

    # Helpers
    def is_other_program(self) -> bool:
        return (self.program_code or '').upper() == 'O'

    def get_program_id_or_none(self) -> Optional[int]:
        return self.program_id if not self.is_other_program() else None
