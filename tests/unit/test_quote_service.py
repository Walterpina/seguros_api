"""Unit tests for QuoteCalculationService."""

import pytest
from decimal import Decimal

from src.application.services.quote_service import (
    QuoteCalculationService,
    ValidationResult,
)


@pytest.mark.unit
class TestQuoteCalculationService:
    """Test QuoteCalculationService business logic."""

    def test_calculate_premium(self):
        """Test premium calculation."""
        result = QuoteCalculationService.calculate_premium(
            loan_value=Decimal("100000.00"),
            premium_rate=Decimal("0.045"),
        )

        assert result == Decimal("4500.00")

    def test_calculate_premium_with_floats(self):
        """Test premium calculation with float inputs."""
        result = QuoteCalculationService.calculate_premium(
            loan_value=100000.0,
            premium_rate=0.045,
        )

        assert result == Decimal("4500.00")

    def test_calculate_brokerage(self):
        """Test brokerage calculation."""
        result = QuoteCalculationService.calculate_brokerage(
            premium_amount=Decimal("4500.00"),
            brokerage_rate=Decimal("0.15"),
        )

        assert result == Decimal("675.00")

    def test_calculate_total(self):
        """Test total calculation."""
        result = QuoteCalculationService.calculate_total(
            loan_value=Decimal("100000.00"),
            premium_amount=Decimal("4500.00"),
            brokerage_amount=Decimal("675.00"),
        )

        assert result == Decimal("105175.00")

    def test_calculate_monthly_payment(self):
        """Test monthly payment calculation."""
        result = QuoteCalculationService.calculate_monthly_payment(
            total_amount=Decimal("105175.00"),
            num_months=12,
        )

        assert result == Decimal("8764.58")

    def test_calculate_monthly_payment_invalid_months(self):
        """Test monthly payment with invalid num_months."""
        with pytest.raises(ValueError, match="num_months must be > 0"):
            QuoteCalculationService.calculate_monthly_payment(
                total_amount=Decimal("100.00"),
                num_months=0,
            )

    def test_generate_payment_schedule(self):
        """Test payment schedule generation."""
        schedule = QuoteCalculationService.generate_payment_schedule(
            total_amount=Decimal("105175.00"),
            num_months=12,
        )

        assert len(schedule) == 12

        # Verify monthly amounts
        for i, payment in enumerate(schedule, 1):
            assert payment.month == i
            assert payment.amount > 0
            assert payment.accumulated > 0

        # Verify last payment accumulated equals total
        assert schedule[-1].accumulated == Decimal("105175.00")

    def test_validate_quote_input_valid(self):
        """Test validation with valid inputs."""
        result = QuoteCalculationService.validate_quote_input(
            loan_value=Decimal("100000.00"),
            premium_rate=Decimal("0.045"),
            brokerage_rate=Decimal("0.15"),
        )

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_quote_input_zero_loan(self):
        """Test validation with zero loan_value."""
        result = QuoteCalculationService.validate_quote_input(
            loan_value=Decimal("0.00"),
            premium_rate=Decimal("0.045"),
            brokerage_rate=Decimal("0.15"),
        )

        assert result.is_valid is False
        assert "loan_value must be > 0" in result.errors

    def test_validate_quote_input_negative_loan(self):
        """Test validation with negative loan_value."""
        result = QuoteCalculationService.validate_quote_input(
            loan_value=Decimal("-100000.00"),
            premium_rate=Decimal("0.045"),
            brokerage_rate=Decimal("0.15"),
        )

        assert result.is_valid is False
        assert "loan_value must be > 0" in result.errors

    def test_validate_quote_input_invalid_premium_rate(self):
        """Test validation with invalid premium_rate."""
        result = QuoteCalculationService.validate_quote_input(
            loan_value=Decimal("100000.00"),
            premium_rate=Decimal("1.5"),
            brokerage_rate=Decimal("0.15"),
        )

        assert result.is_valid is False
        assert "premium_rate must be between 0 and 1" in result.errors

    def test_validate_quote_input_negative_rate(self):
        """Test validation with negative brokerage_rate."""
        result = QuoteCalculationService.validate_quote_input(
            loan_value=Decimal("100000.00"),
            premium_rate=Decimal("0.045"),
            brokerage_rate=Decimal("-0.10"),
        )

        assert result.is_valid is False
        assert "brokerage_rate must be between 0 and 1" in result.errors

    def test_validate_quote_input_non_numeric(self):
        """Test validation with non-numeric input."""
        result = QuoteCalculationService.validate_quote_input(
            loan_value="not a number",
            premium_rate=Decimal("0.045"),
            brokerage_rate=Decimal("0.15"),
        )

        assert result.is_valid is False
        assert "loan_value must be numeric" in result.errors

    def test_create_quote_valid(self):
        """Test creating a quote entity via service."""
        quote = QuoteCalculationService.create_quote(
            loan_value=Decimal("100000.00"),
            premium_rate=Decimal("0.045"),
            brokerage_rate=Decimal("0.15"),
        )

        assert quote.loan_value == Decimal("100000.00")
        assert quote.premium_amount == Decimal("4500.00")
        assert quote.total_amount == Decimal("105175.00")

    def test_create_quote_invalid_raises_error(self):
        """Test creating quote with invalid input raises ValueError."""
        with pytest.raises(ValueError, match="Invalid quote input"):
            QuoteCalculationService.create_quote(
                loan_value=Decimal("-100.00"),
                premium_rate=Decimal("0.045"),
                brokerage_rate=Decimal("0.15"),
            )
