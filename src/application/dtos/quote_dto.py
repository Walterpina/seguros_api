"""Quote DTOs (Data Transfer Objects) for API requests/responses."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class QuoteCreateRequest(BaseModel):
    """Request DTO for creating a quote."""

    loan_value: Decimal = Field(
        ..., gt=0, description="Principal loan amount (must be > 0)"
    )
    premium_rate: Optional[Decimal] = Field(
        None, ge=0, le=1, description="Premium rate (0-1)"
    )
    brokerage_rate: Optional[Decimal] = Field(
        None, ge=0, le=1, description="Brokerage rate (0-1)"
    )

    @field_validator("loan_value", mode="before")
    def coerce_loan_value(cls, v):
        """Coerce loan_value to Decimal."""
        if v is None:
            raise ValueError("loan_value is required")
        return Decimal(str(v))

    @field_validator("premium_rate", mode="before")
    def coerce_premium_rate(cls, v):
        """Coerce premium_rate to Decimal."""
        if v is None:
            return None
        return Decimal(str(v))

    @field_validator("brokerage_rate", mode="before")
    def coerce_brokerage_rate(cls, v):
        """Coerce brokerage_rate to Decimal."""
        if v is None:
            return None
        return Decimal(str(v))

    class Config:
        json_schema_extra = {
            "example": {
                "loan_value": 100000.00,
                "premium_rate": 0.045,
                "brokerage_rate": 0.15,
            }
        }


class QuoteResponse(BaseModel):
    """Response DTO for a single quote."""

    quote_id: UUID = Field(..., description="Quote UUID")
    loan_value: Decimal = Field(..., description="Principal loan amount")
    premium_rate: Decimal = Field(..., description="Premium rate used")
    premium_amount: Decimal = Field(..., description="Calculated premium")
    brokerage_rate: Decimal = Field(..., description="Brokerage rate used")
    brokerage_amount: Decimal = Field(..., description="Calculated brokerage")
    total_amount: Decimal = Field(..., description="Total amount (loan + premium + brokerage)")
    monthly_payment: Decimal = Field(..., description="Monthly payment amount")
    payment_schedule: List[dict] = Field(default_factory=list, description="Payment schedule")
    status: str = Field("active", description="Quote status (active, archived, cancelled)")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "quote_id": "550e8400-e29b-41d4-a716-446655440000",
                "loan_value": 100000.00,
                "premium_rate": 0.045,
                "premium_amount": 4500.00,
                "brokerage_rate": 0.15,
                "brokerage_amount": 675.00,
                "total_amount": 105175.00,
                "monthly_payment": 8764.58,
                "status": "active",
                "created_at": "2026-03-30T10:00:00",
                "updated_at": "2026-03-30T10:00:00",
            }
        }


class QuoteListResponse(BaseModel):
    """Response DTO for listing quotes (paginated)."""

    items: List[QuoteResponse] = Field(..., description="List of quotes")
    total: int = Field(..., description="Total number of quotes")
    page: int = Field(..., description="Current page number (0-indexed)")
    limit: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 0,
                "page": 0,
                "limit": 50,
                "pages": 0,
            }
        }
