"""
Configuration management using Pydantic v2 BaseSettings.
Loads environment variables with type validation and default values.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = Field(
        default="postgresql://postgres:password@localhost:5432/seguros_api",
        description="PostgreSQL connection string",
        alias="DATABASE_URL",
    )

    # JWT Authentication
    jwt_secret_key: str = Field(
        default="your-super-secret-jwt-key-change-in-production-min-32-chars",
        description="Secret key for JWT token signing (min 32 chars)",
        alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT algorithm for token encoding",
        alias="JWT_ALGORITHM",
    )
    jwt_expiration_minutes: int = Field(
        default=1440,
        description="JWT token expiration time in minutes (default 24h)",
        alias="JWT_EXPIRATION_MINUTES",
    )

    # API Configuration
    api_title: str = Field(
        default="Lending Insurance Quotation API",
        alias="API_TITLE",
    )
    api_version: str = Field(
        default="1.0.0",
        alias="API_VERSION",
    )
    log_level: str = Field(
        default="INFO",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
        alias="LOG_LEVEL",
    )

    # Premium & Brokerage Rates
    default_premium_rate: float = Field(
        default=0.045,
        ge=0.0,
        le=1.0,
        description="Default premium rate (45%)",
        alias="DEFAULT_PREMIUM_RATE",
    )
    default_brokerage_rate: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        description="Default brokerage rate (15%)",
        alias="DEFAULT_BROKERAGE_RATE",
    )

    # API Server
    api_host: str = Field(
        default="0.0.0.0",
        alias="API_HOST",
    )
    api_port: int = Field(
        default=8000,
        ge=1024,
        le=65535,
        alias="API_PORT",
    )

    # Redis (Cache)
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string for caching",
        alias="REDIS_URL",
    )
    cache_ttl_minutes: int = Field(
        default=5,
        ge=1,
        le=1440,
        description="Cache TTL in minutes",
        alias="CACHE_TTL_MINUTES",
    )

    # Environment
    environment: str = Field(
        default="development",
        pattern="^(development|staging|production)$",
        alias="ENVIRONMENT",
    )

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        populate_by_name = True

    def validate_jwt_secret_key(self) -> None:
        """Validate JWT secret key length."""
        if len(self.jwt_secret_key) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be at least 32 characters long. "
                f"Current length: {len(self.jwt_secret_key)}"
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Returns the same Settings instance across the application.
    """
    settings = Settings()
    settings.validate_jwt_secret_key()
    return settings
