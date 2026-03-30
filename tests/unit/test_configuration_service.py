"""Unit tests for ConfigurationService."""

import pytest
from decimal import Decimal
from uuid import uuid4

from src.application.services.configuration_service import ConfigurationService


@pytest.mark.unit
class TestConfigurationService:
    """Test ConfigurationService rate loading and validation."""

    def test_get_current_rates_default(self, monkeypatch):
        """Test getting default rates from environment."""
        # Mock environment defaults
        monkeypatch.setenv("DEFAULT_PREMIUM_RATE", "0.045")
        monkeypatch.setenv("DEFAULT_BROKERAGE_RATE", "0.15")

        service = ConfigurationService()
        rates = service.get_current_rates()

        assert rates.premium_rate == Decimal("0.045")
        assert rates.brokerage_rate == Decimal("0.15")

    def test_get_current_rates_with_organization_id(self):
        """Test getting rates with organization_id (MVP returns defaults)."""
        service = ConfigurationService()
        org_id = uuid4()

        rates = service.get_current_rates(organization_id=org_id)

        # MVP phase: always returns global rates
        assert rates.premium_rate > 0
        assert rates.brokerage_rate > 0

    def test_validate_rates_valid(self):
        """Test rate validation with valid values."""
        service = ConfigurationService()

        result = service.validate_rates(
            premium_rate=Decimal("0.045"),
            brokerage_rate=Decimal("0.15"),
        )

        assert result is True

    def test_validate_rates_edge_cases(self):
        """Test rate validation at boundaries (0 and 1)."""
        service = ConfigurationService()

        # Test 0%
        assert (
            service.validate_rates(
                premium_rate=Decimal("0.0"),
                brokerage_rate=Decimal("0.0"),
            )
            is True
        )

        # Test 100%
        assert (
            service.validate_rates(
                premium_rate=Decimal("1.0"),
                brokerage_rate=Decimal("1.0"),
            )
            is True
        )

    def test_validate_rates_negative_premium(self):
        """Test validation with negative premium_rate."""
        service = ConfigurationService()

        with pytest.raises(ValueError, match="premium_rate cannot be negative"):
            service.validate_rates(
                premium_rate=Decimal("-0.01"),
                brokerage_rate=Decimal("0.15"),
            )

    def test_validate_rates_negative_brokerage(self):
        """Test validation with negative brokerage_rate."""
        service = ConfigurationService()

        with pytest.raises(ValueError, match="brokerage_rate cannot be negative"):
            service.validate_rates(
                premium_rate=Decimal("0.045"),
                brokerage_rate=Decimal("-0.05"),
            )

    def test_validate_rates_exceeds_100_percent(self):
        """Test validation with rates > 100%."""
        service = ConfigurationService()

        with pytest.raises(ValueError, match="premium_rate cannot exceed 100%"):
            service.validate_rates(
                premium_rate=Decimal("1.5"),
                brokerage_rate=Decimal("0.15"),
            )

    def test_validate_rates_exceeds_brokerage(self):
        """Test validation with brokerage > 100%."""
        service = ConfigurationService()

        with pytest.raises(ValueError, match="brokerage_rate cannot exceed 100%"):
            service.validate_rates(
                premium_rate=Decimal("0.045"),
                brokerage_rate=Decimal("1.1"),
            )

    def test_load_from_env(self, monkeypatch):
        """Test loading rates from environment."""
        monkeypatch.setenv("DEFAULT_PREMIUM_RATE", "0.05")
        monkeypatch.setenv("DEFAULT_BROKERAGE_RATE", "0.20")

        service = ConfigurationService()
        rates = service.load_from_env()

        assert rates.premium_rate == Decimal("0.05")
        assert rates.brokerage_rate == Decimal("0.20")

    def test_validate_rates_coerce_from_string(self):
        """Test rate validation coerces string to Decimal."""
        service = ConfigurationService()

        # Strings should be coerced to Decimal internally
        result = service.validate_rates(
            premium_rate="0.045",
            brokerage_rate="0.15",
        )

        assert result is True
