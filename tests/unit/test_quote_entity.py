"""Unit tests for Quote domain entity."""

import pytest
from decimal import Decimal
from uuid import UUID

from src.domain.entities.quote import Quote


@pytest.mark.unit
class TestQuoteEntity:
    """Test Quote entity creation and calculations."""

    def test_quote_valid_creation(self):
        """Test creating a quote with valid inputs."""
        quote = Quote(
            loan_value=Decimal("100000.00"),
            premium_rate=Decimal("0.045"),
            brokerage_rate=Decimal("0.15"),
        )

        assert quote.loan_value == Decimal("100000.00")
        assert quote.premium_rate == Decimal("0.045")
        assert quote.brokerage_rate == Decimal("0.15")
        assert quote.status == "active"
        assert isinstance(quote.id, UUID)

    def test_quote_premium_calculation(self):
        """Test premium calculation: loan_value * premium_rate."""
        quote = Quote(
            loan_value=Decimal("100000.00"),
            premium_rate=Decimal("0.045"),
            brokerage_rate=Decimal("0.15"),
        )

        # Premium = 100000 * 0.045 = 4500
        assert quote.premium_amount == Decimal("4500.00")

    def test_quote_brokerage_calculation(self):
        """Test brokerage calculation: premium_amount * brokerage_rate."""
        quote = Quote(
            loan_value=Decimal("100000.00"),
            premium_rate=Decimal("0.045"),
            brokerage_rate=Decimal("0.15"),
        )

        # Brokerage = 4500 * 0.15 = 675
        assert quote.brokerage_amount == Decimal("675.00")

    def test_quote_total_calculation(self):
        """Test total calculation: loan_value + premium + brokerage."""
        quote = Quote(
            loan_value=Decimal("100000.00"),
            premium_rate=Decimal("0.045"),
            brokerage_rate=Decimal("0.15"),
        )

        # Total = 100000 + 4500 + 675 = 105175
        assert quote.total_amount == Decimal("105175.00")

    def test_quote_monthly_payment_calculation(self):
        """Test monthly payment calculation: total / 12."""
        quote = Quote(
            loan_value=Decimal("100000.00"),
            premium_rate=Decimal("0.045"),
            brokerage_rate=Decimal("0.15"),
        )

        # Monthly = 105175 / 12 ≈ 8764.58
        assert quote.monthly_payment == Decimal("8764.58")

    def test_quote_zero_loan_value_raises_error(self):
        """Test that zero loan_value raises ValueError."""
        with pytest.raises(ValueError, match="loan_value must be > 0"):
            Quote(
                loan_value=Decimal("0.00"),
                premium_rate=Decimal("0.045"),
                brokerage_rate=Decimal("0.15"),
            )

    def test_quote_negative_loan_value_raises_error(self):
        """Test that negative loan_value raises ValueError."""
        with pytest.raises(ValueError, match="loan_value must be > 0"):
            Quote(
                loan_value=Decimal("-100000.00"),
                premium_rate=Decimal("0.045"),
                brokerage_rate=Decimal("0.15"),
            )

    def test_quote_invalid_premium_rate_raises_error(self):
        """Test that invalid premium_rate raises ValueError."""
        with pytest.raises(ValueError, match="premium_rate must be 0-1"):
            Quote(
                loan_value=Decimal("100000.00"),
                premium_rate=Decimal("1.5"),
                brokerage_rate=Decimal("0.15"),
            )

    def test_quote_invalid_brokerage_rate_raises_error(self):
        """Test that invalid brokerage_rate raises ValueError."""
        with pytest.raises(ValueError, match="brokerage_rate must be 0-1"):
            Quote(
                loan_value=Decimal("100000.00"),
                premium_rate=Decimal("0.045"),
                brokerage_rate=Decimal("-0.10"),
            )

    def test_quote_large_loan_value_precision(self):
        """Test precision with large loan values (R$10M)."""
        quote = Quote(
            loan_value=Decimal("10000000.00"),
            premium_rate=Decimal("0.045"),
            brokerage_rate=Decimal("0.15"),
        )

        # Premium = 10000000 * 0.045 = 450000
        assert quote.premium_amount == Decimal("450000.00")

        # Brokerage = 450000 * 0.15 = 67500
        assert quote.brokerage_amount == Decimal("67500.00")

        # Total = 10000000 + 450000 + 67500 = 10517500
        assert quote.total_amount == Decimal("10517500.00")

    def test_quote_small_loan_value_rounding(self):
        """Test rounding with small loan values."""
        quote = Quote(
            loan_value=Decimal("0.01"),
            premium_rate=Decimal("0.0002"),
            brokerage_rate=Decimal("0.05"),
        )

        # Premium = 0.01 * 0.0002 = 0.000002 → 0.00
        # Brokerage = 0.00 * 0.05 = 0.00
        # Total = 0.01 + 0.00 + 0.00 = 0.01
        assert quote.total_amount == Decimal("0.01")

    def test_quote_payment_schedule_generated(self):
        """Test that payment schedule is generated with correct months."""
        quote = Quote(
            loan_value=Decimal("100000.00"),
            premium_rate=Decimal("0.045"),
            brokerage_rate=Decimal("0.15"),
        )

        assert quote.payment_schedule is not None
        assert len(quote.payment_schedule.monthly_payments) == 12

        # Verify accumulated total matches
        last_payment = quote.payment_schedule.monthly_payments[-1]
        assert last_payment.accumulated == quote.total_amount

    def test_quote_to_dict_serialization(self):
        """Test conversion to dictionary."""
        quote = Quote(
            loan_value=Decimal("100000.00"),
            premium_rate=Decimal("0.045"),
            brokerage_rate=Decimal("0.15"),
        )

        quote_dict = quote.to_dict()

        assert quote_dict["loan_value"] == 100000.0
        assert quote_dict["premium_amount"] == 4500.0
        assert quote_dict["brokerage_amount"] == 675.0
        assert quote_dict["total_amount"] == 105175.0
        assert quote_dict["monthly_payment"] == 8764.58

    def test_quote_string_representation(self):
        """Test string representation of quote."""
        quote = Quote(
            loan_value=Decimal("100000.00"),
            premium_rate=Decimal("0.045"),
            brokerage_rate=Decimal("0.15"),
        )

        quote_str = str(quote)
        assert "Quote(" in quote_str
        assert "100000" in quote_str
        assert "4500" in quote_str
