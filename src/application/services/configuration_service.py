"""Configuration service: Manages premium and brokerage rates."""

from decimal import Decimal
from typing import NamedTuple, Optional
from uuid import UUID

from config.settings import get_settings


class CurrentRates(NamedTuple):
    """Current premium and brokerage rates."""

    premium_rate: Decimal
    brokerage_rate: Decimal


class ConfigurationService:
    """Service for managing and retrieving rate configurations (MVP: env-based)."""

    def __init__(self):
        """Initialize with settings."""
        self.settings = get_settings()

    def get_current_rates(self, organization_id: Optional[UUID] = None) -> CurrentRates:
        """
        Get current rates for organization (or global defaults).

        Args:
            organization_id: Organization UUID (optional, for future org-specific rates)

        Returns:
            CurrentRates: Current premium and brokerage rates

        Note:
            MVP phase: Returns global rates from config/settings.py
            Future: Will query database for org-specific rates
        """
        # For MVP, always return global rates from environment
        # Future enhancement: Query configuration repository for org-specific rates
        return CurrentRates(
            premium_rate=Decimal(str(self.settings.default_premium_rate)),
            brokerage_rate=Decimal(str(self.settings.default_brokerage_rate)),
        )

    def validate_rates(
        self, premium_rate: Decimal, brokerage_rate: Decimal
    ) -> bool:
        """
        Validate rate values.

        Args:
            premium_rate: Premium rate to validate
            brokerage_rate: Brokerage rate to validate

        Returns:
            bool: True if valid

        Raises:
            ValueError: If rates are invalid
        """
        premium_rate = Decimal(str(premium_rate))
        brokerage_rate = Decimal(str(brokerage_rate))

        if premium_rate < 0:
            raise ValueError(
                f"premium_rate cannot be negative, got {premium_rate}"
            )

        if brokerage_rate < 0:
            raise ValueError(
                f"brokerage_rate cannot be negative, got {brokerage_rate}"
            )

        if premium_rate > 1:
            raise ValueError(
                f"premium_rate cannot exceed 100%, got {premium_rate}"
            )

        if brokerage_rate > 1:
            raise ValueError(
                f"brokerage_rate cannot exceed 100%, got {brokerage_rate}"
            )

        return True

    def load_from_env(self) -> CurrentRates:
        """
        Load rates from environment variables.

        Returns:
            CurrentRates: Rates from config/settings.py
        """
        return CurrentRates(
            premium_rate=Decimal(str(self.settings.default_premium_rate)),
            brokerage_rate=Decimal(str(self.settings.default_brokerage_rate)),
        )
