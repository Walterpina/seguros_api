"""API schemas for Quote endpoints (request/response models)."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class QuoteCreateRequest(BaseModel):
    """Request schema for creating a quote."""

    loan_value: Decimal = Field(
        ...,
        gt=0,
        description="Principal loan amount (must be > 0)",
    )
    premium_rate: Optional[Decimal] = Field(
        None,
        ge=0,
        le=1,
        description="Premium rate override (0-1). If not provided, uses configuration default.",
    )
    brokerage_rate: Optional[Decimal] = Field(
        None,
        ge=0,
        le=1,
        description="Brokerage rate override (0-1). If not provided, uses configuration default.",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "loan_value": 100000.00,
                "premium_rate": 0.045,
                "brokerage_rate": 0.15,
            }
        }


class MonthlyPaymentItem(BaseModel):
    """Single monthly payment in schedule."""

    month: int = Field(..., description="Month number (1-12)")
    amount: Decimal = Field(..., description="Payment amount for this month")
    accumulated: Decimal = Field(..., description="Accumulated total through this month")


class QuoteResponse(BaseModel):
    """Response schema for a single quote."""

    quote_id: UUID = Field(..., description="Quote UUID")
    loan_value: Decimal = Field(..., description="Principal loan amount")
    premium_rate: Decimal = Field(..., description="Premium rate used")
    premium_amount: Decimal = Field(..., description="Calculated premium amount")
    brokerage_rate: Decimal = Field(..., description="Brokerage rate used")
    brokerage_amount: Decimal = Field(
        ..., description="Calculated brokerage amount"
    )
    total_amount: Decimal = Field(
        ..., description="Total amount (loan + premium + brokerage)"
    )
    monthly_payment: Decimal = Field(..., description="Monthly payment amount")
    payment_schedule: List[MonthlyPaymentItem] = Field(
        ..., description="12-month payment schedule"
    )
    status: str = Field(
        "active", description="Quote status (active, archived, cancelled)"
    )
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
                "payment_schedule": [
                    {"month": 1, "amount": 8764.58, "accumulated": 8764.58},
                    {"month": 2, "amount": 8764.58, "accumulated": 17529.16},
                ],
                "status": "active",
                "created_at": "2026-03-30T10:00:00",
                "updated_at": "2026-03-30T10:00:00",
            }
        }


class QuoteListResponse(BaseModel):
    """Response schema for listing quotes (paginated)."""

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


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    code: str = Field(..., description="Error code (e.g., 'VALIDATION_ERROR', 'NOT_FOUND')")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details (e.g., field errors)"
    )
    request_id: Optional[str] = Field(
        None, description="Request ID for tracing"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "code": "VALIDATION_ERROR",
                "message": "Quote creation failed due to validation errors",
                "details": {
                    "loan_value": "must be greater than 0"
                },
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
            }
        }
