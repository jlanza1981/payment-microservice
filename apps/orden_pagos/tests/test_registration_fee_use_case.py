# apps/orden_pagos/tests/test_registration_fee_use_case.py
"""
Tests para el caso de uso de cálculo de inscripción.
"""
from decimal import Decimal
from unittest.mock import Mock

from apps.orden_pagos.application.use_cases.calculate_registration_fee import CalculateRegistrationFeeUseCase
from apps.orden_pagos.infrastructure.repository.registration_fee_repository import RegistrationFeeRepository


class TestCalculateRegistrationFeeUseCase:
    """Test suite para CalculateRegistrationFeeUseCase."""

    def test_execute_with_valid_data_and_discount(self):
        """
        Dado: Una sede con precio de inscripción y descuento porcentual
        Cuando: Se ejecuta el caso de uso
        Entonces: Retorna el cálculo correcto con descuentos aplicados
        """
        # Arrange
        mock_repository = Mock(spec=RegistrationFeeRepository)
        mock_repository.get_currency_by_institution_and_city.return_value = 'USD'
        mock_repository.get_registration_price_by_sede.return_value = {
            'price': Decimal('1000.00'),
            'discount_percentage': Decimal('10.00'),
            'description': 'Inscripción Estándar'
        }

        use_case = CalculateRegistrationFeeUseCase(mock_repository)

        # Act
        result = use_case.execute(
            institution_id=123,
            city_id=456,
            program_type_id=789
        )

        # Assert
        assert result['amount'] == '1,000.00'
        assert result['discount_percentage'] == 10
        assert result['currency'] == 'USD'
        assert result['total_amount'] == '900.00'
        assert len(result['discounts']) == 1
        assert result['discounts'][0]['name'] == 'Descuento LC'
        assert result['discounts'][0]['discount_amount'] == '100.00'
        assert result['registration_name'] == 'Inscripción Estándar'

    def test_execute_without_discount(self):
        """
        Dado: Una sede sin descuentos
        Cuando: Se ejecuta el caso de uso
        Entonces: El total es igual al precio base
        """
        # Arrange
        mock_repository = Mock(spec=RegistrationFeeRepository)
        mock_repository.get_currency_by_institution_and_city.return_value = 'EUR'
        mock_repository.get_registration_price_by_sede.return_value = {
            'price': Decimal('500.00'),
            'discount_percentage': Decimal('0.00'),
            'description': 'Inscripción Básica'
        }

        use_case = CalculateRegistrationFeeUseCase(mock_repository)

        # Act
        result = use_case.execute(
            institution_id=100,
            city_id=200,
            program_type_id=300
        )

        # Assert
        assert result['amount'] == '500.00'
        assert result['discount_percentage'] == 0
        assert result['currency'] == 'EUR'
        assert result['total_amount'] == '500.00'
        assert len(result['discounts']) == 0

    def test_execute_with_no_registration_price_found(self):
        """
        Dado: Una sede sin precio de inscripción configurado
        Cuando: Se ejecuta el caso de uso
        Entonces: Retorna valores por defecto (ceros)
        """
        # Arrange
        mock_repository = Mock(spec=RegistrationFeeRepository)
        mock_repository.get_currency_by_institution_and_city.return_value = 'USD'
        mock_repository.get_registration_price_by_sede.return_value = None

        use_case = CalculateRegistrationFeeUseCase(mock_repository)

        # Act
        result = use_case.execute(
            institution_id=999,
            city_id=888,
            program_type_id=777
        )

        # Assert
        assert result['amount'] == '0.00'
        assert result['discount_percentage'] == 0
        assert result['currency'] == 'USD'
        assert result['total_amount'] == '0.00'
        assert result['registration_name'] == 'Inscripción'

    def test_execute_with_high_discount_percentage(self):
        """
        Dado: Un descuento porcentual del 25%
        Cuando: Se ejecuta el caso de uso
        Entonces: El descuento se calcula correctamente
        """
        # Arrange
        mock_repository = Mock(spec=RegistrationFeeRepository)
        mock_repository.get_currency_by_institution_and_city.return_value = 'CAD'
        mock_repository.get_registration_price_by_sede.return_value = {
            'price': Decimal('2000.00'),
            'discount_percentage': Decimal('25.00'),
            'description': 'Inscripción Premium'
        }

        use_case = CalculateRegistrationFeeUseCase(mock_repository)

        # Act
        result = use_case.execute(
            institution_id=50,
            city_id=60,
            program_type_id=70
        )

        # Assert
        assert result['amount'] == '2,000.00'
        assert result['discount_percentage'] == 25
        assert result['currency'] == 'CAD'
        assert result['total_amount'] == '1,500.00'
        assert result['discounts'][0]['discount_amount'] == '500.00'
        assert result['discounts'][0]['percentage'] == 25

    def test_execute_with_no_currency_found_uses_default(self):
        """
        Dado: Una sede sin moneda configurada
        Cuando: Se ejecuta el caso de uso
        Entonces: Usa la moneda por defecto USD
        """
        # Arrange
        mock_repository = Mock(spec=RegistrationFeeRepository)
        mock_repository.get_currency_by_institution_and_city.return_value = None
        mock_repository.get_registration_price_by_sede.return_value = {
            'price': Decimal('100.00'),
            'discount_percentage': Decimal('0.00'),
            'description': 'Test'
        }

        use_case = CalculateRegistrationFeeUseCase(mock_repository)

        # Act
        result = use_case.execute(
            institution_id=1,
            city_id=2,
            program_type_id=3
        )

        # Assert
        assert result['currency'] == 'USD'

