# apps/orden_pagos/api/schemas.py
from ninja import Schema
from decimal import Decimal


class AdministrativeCostSchema(Schema):
    """Schema para tipo de costo administrativo."""
    id: int
    name: str
    amount: Decimal
    currency_country: str
    country_id: str
    country_name: str

    @classmethod
    def from_orm(cls, obj):
        """Convierte un modelo Django o dict a schema"""
        # Si es un diccionario, acceder directamente a las claves

        if isinstance(obj, dict):
            data = {
                'id': obj.get('id', 0),
                'name': obj.get('name', ''),
                'amount': obj.get('amount', Decimal('0.00')),
                'currency_country': obj.get('currency_country', ''),
                'country_id': obj.get('country_id', ''),
                'country_name': obj.get('country_name', ''),
            }
        else:
            # Es un objeto ORM, usar getattr
            data = {
                'id': getattr(obj, 'id', 0),
                'name': getattr(obj, 'name', ''),
                'amount': getattr(obj, 'amount', Decimal('0.00')),
                'currency_country': getattr(obj, 'currency_country', ''),
                'country_id': getattr(obj, 'country_id', ''),
                'country_name': getattr(obj, 'country_name', ''),
            }

        return cls(**data)

    class Config:
        from_attributes = True


class AdministrativeCostFilterSchema(Schema):
    """Schema para filtros de búsqueda."""
    country_id: int
    currency_country: str = "USA"
