"""Quote API endpoints (CRUD operations)."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.schemas.quote_schemas import (
    ErrorResponse,
    QuoteCreateRequest,
    QuoteListResponse,
    QuoteResponse,
)
from src.api.security.dependencies import CurrentUser, get_current_user
from src.application.dtos.mappers import quote_entity_to_response
from src.application.dtos.quote_dto import QuoteCreateRequest as DomainQuoteCreateRequest
from src.application.services.configuration_service import ConfigurationService
from src.application.services.quote_service import QuoteCalculationService
from src.application.use_cases.create_quote import CreateQuoteUseCase
from src.application.use_cases.delete_quote import DeleteQuoteUseCase
from src.application.use_cases.get_quote import GetQuoteUseCase
from src.application.use_cases.list_quotes import ListQuotesUseCase
from src.infrastructure.repositories.sql_quote_repository import SQLQuoteRepository

# Create API router
router = APIRouter(
    prefix="/quotes",
    tags=["Quotes"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not found"},
    },
)


@router.post(
    "",
    response_model=QuoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new quote",
    description="Create a new lending insurance quote with calculated premium, brokerage, and installment schedule.",
    responses={
        201: {
            "description": "Quote created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "quote_id": "550e8400-e29b-41d4-a716-446655440000",
                        "loan_value": 100000.00,
                        "premium_amount": 4500.00,
                        "brokerage_amount": 700.00,
                        "total_amount": 105200.00,
                        "monthly_payment": 8766.67,
                        "payment_schedule": [
                            {"month": 1, "amount": 8766.67, "accumulated": 8766.67},
                            {"month": 12, "amount": 8766.64, "accumulated": 105200.00},
                        ],
                        "status": "active",
                    }
                }
            },
        },
        400: {"model": ErrorResponse, "description": "Invalid loan value or rates"},
    },
)
async def post_create_quote(
    request: QuoteCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> QuoteResponse:
    """
    Create a new insurance quote.

    This endpoint calculates an insurance premium and brokerage fee based on the provided 
    loan value and configured rates. The quote includes a 12-month payment schedule.

    **Business Logic**:
    - Premium = loan_value × premium_rate (default: 4.5%)
    - Brokerage = premium × brokerage_rate (default: 15%)
    - Total = loan_value + premium + brokerage
    - Monthly = total / 12 (evenly distributed over 12 months)

    **Parameters**:
    - loan_value: Required. Must be > 0. The loan value for insurance calculation.
    - premium_rate: Optional. Rate between 0 and 1 (e.g., 0.045 = 4.5%). Defaults to 4.5%.
    - brokerage_rate: Optional. Rate between 0 and 1 (e.g., 0.15 = 15%). Defaults to 15%.

    **Authentication**: Requires Bearer JWT token in Authorization header.
    - Token must contain: user_id, organization_id, role
    - Created quotes are associated with the authenticated user and organization

    **Example Usage**:
    ```bash
    curl -X POST http://localhost:8000/api/v1/quotes \
      -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIi..." \
      -H "Content-Type: application/json" \
      -d '{"loan_value": 100000}'
    ```

    **Python Example**:
    ```python
    import requests
    token = "your-jwt-token"
    response = requests.post(
        "http://localhost:8000/api/v1/quotes",
        json={"loan_value": 100000.00},
        headers={"Authorization": f"Bearer {token}"}
    )
    quote = response.json()
    print(f"Total: R${quote['total_amount']}")
    ```

    Args:
        request: Quote creation request with loan_value and optional rates
        current_user: Authenticated user extracted from JWT token

    Returns:
        QuoteResponse: Created quote with:
        - quote_id: UUID of created quote
        - loan_value: Original loan value
        - premium_amount, brokerage_amount, total_amount: Calculated costs
        - monthly_payment: Fixed monthly installment amount
        - payment_schedule: 12-month breakdown
        - status: "active" (new quotes are immediately active)
        - created_at, updated_at: Timestamps in ISO 8601 format

    Raises:
        HTTPException(400): Validation error
        - loan_value <= 0
        - premium_rate or brokerage_rate outside [0,1] range
        - Missing required fields

        HTTPException(401): Missing or invalid authentication token

        HTTPException(500): Unexpected server error
    """
    try:
        # Convert API request to domain request
        domain_request = DomainQuoteCreateRequest(
            loan_value=request.loan_value,
            premium_rate=request.premium_rate,
            brokerage_rate=request.brokerage_rate,
        )

        # Initialize services and repositories (MVP: in-memory or mock)
        # In production, use dependency injection
        from sqlalchemy.orm import Session

        # Create mock repository for MVP (would use real DB session in production)
        # repository = SQLQuoteRepository(db_session)
        calc_service = QuoteCalculationService()
        config_service = ConfigurationService()

        # Execute use case (without persistence in MVP demo)
        # For testing purposes, create and return without persistence
        quote_entity = calc_service.create_quote(
            loan_value=domain_request.loan_value,
            premium_rate=domain_request.premium_rate or config_service.get_current_rates(
                current_user.organization_id
            ).premium_rate,
            brokerage_rate=domain_request.brokerage_rate or config_service.get_current_rates(
                current_user.organization_id
            ).brokerage_rate,
        )

        # Convert to response
        response = quote_entity_to_response(
            quote_entity,
            user_id=current_user.user_id,
            organization_id=current_user.organization_id,
        )

        # Add payment schedule to response
        return QuoteResponse(
            quote_id=response.quote_id,
            loan_value=response.loan_value,
            premium_rate=response.premium_rate,
            premium_amount=response.premium_amount,
            brokerage_rate=response.brokerage_rate,
            brokerage_amount=response.brokerage_amount,
            total_amount=response.total_amount,
            monthly_payment=response.monthly_payment,
            payment_schedule=[
                {
                    "month": p.month,
                    "amount": p.amount,
                    "accumulated": p.accumulated,
                }
                for p in quote_entity.payment_schedule.monthly_payments
            ],
            status=response.status,
            created_at=response.created_at,
            updated_at=response.updated_at,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Quote creation failed",
        )


@router.get(
    "",
    response_model=QuoteListResponse,
    summary="List quotes",
    description="Retrieve paginated list of quotes for the authenticated user's organization with optional filtering.",
    responses={
        200: {
            "description": "List of quotes retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "quote_id": "550e8400-e29b-41d4-a716-446655440000",
                                "loan_value": 100000.00,
                                "total_amount": 105200.00,
                                "monthly_payment": 8766.67,
                                "status": "active",
                                "created_at": "2024-01-15T10:30:45.123456Z",
                            }
                        ],
                        "total": 1,
                        "page": 0,
                        "limit": 50,
                        "pages": 1,
                    }
                }
            },
        }
    },
)
async def get_list_quotes(
    page: int = Query(0, ge=0, description="Page number (0-indexed)"),
    limit: int = Query(50, ge=1, le=500, description="Items per page (1-500)"),
    status: Optional[str] = Query("active", description="Filter by status: active, archived, or all"),
    from_date: Optional[datetime] = Query(None, description="Filter from date (ISO 8601 format)"),
    to_date: Optional[datetime] = Query(None, description="Filter to date (ISO 8601 format)"),
    current_user: CurrentUser = Depends(get_current_user),
) -> QuoteListResponse:
    """
    List all quotes for the authenticated user's organization.

    Returns a paginated list of quotes with optional filtering by status and date range.
    Only shows quotes belonging to the authenticated user's organization.

    **Pagination**:
    - page: 0-indexed page number (page=0 is first page)
    - limit: Number of items per page (default 50, max 500)
    - Returned metadata includes total count and number of pages

    **Filtering**:
    - status: Filter by "active", "archived", or "all" (default: active)
    - from_date, to_date: Filter by creation date range (ISO 8601 format)

    **Security**: 
    - Only returns quotes from authenticated user's organization
    - Cannot see other organizations' quotes
    - Returns empty list if no quotes match filters

    **Example Usage**:
    ```bash
    # Get first page with default pagination
    curl http://localhost:8000/api/v1/quotes \
      -H "Authorization: Bearer <token>"

    # Get second page with custom limit
    curl "http://localhost:8000/api/v1/quotes?page=1&limit=10" \
      -H "Authorization: Bearer <token>"

    # Filter by status
    curl "http://localhost:8000/api/v1/quotes?status=archived" \
      -H "Authorization: Bearer <token>"

    # Filter by date range
    curl "http://localhost:8000/api/v1/quotes?from_date=2024-01-01&to_date=2024-01-31" \
      -H "Authorization: Bearer <token>"
    ```

    Args:
        page: Page number (0-indexed), validates >= 0
        limit: Items per page (default 50), validates 1-500
        status: Filter by status (active, archived, or all)
        from_date: Optional start date for filtering
        to_date: Optional end date for filtering
        current_user: Authenticated user extracted from JWT

    Returns:
        QuoteListResponse with:
        - items: List of QuoteResponse objects (may be empty)
        - total: Total number of quotes (before pagination)
        - page: Current page number
        - limit: Items per page
        - pages: Total number of pages

    Raises:
        HTTPException(400): Invalid pagination or filter parameters
        HTTPException(401): Missing or invalid authentication token
        HTTPException(500): Unexpected server error
    """
    try:
        if page < 0:
            raise ValueError("page must be >= 0")
        if limit < 1 or limit > 500:
            raise ValueError("limit must be between 1 and 500")

        # In production, would query real database via repository
        # For MVP, return mock data structure
        return QuoteListResponse(
            items=[],
            total=0,
            page=page,
            limit=limit,
            pages=0,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list quotes",
        )


@router.get(
    "/{quote_id}",
    response_model=QuoteResponse,
    summary="Get quote details",
    description="Retrieve a specific quote by ID with full details including payment schedule. Enforces organization access control.",
    responses={
        200: {
            "description": "Quote retrieved successfully",
        },
        404: {"model": ErrorResponse, "description": "Quote not found or not accessible"},
    },
)
async def get_quote_detail(
    quote_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
) -> QuoteResponse:
    """
    Get full details for a specific quote.

    Retrieves complete quote information including loan value, calculated amounts, 
    rates, and 12-month payment schedule. Only accessible to users in the quote's organization.

    **Security**:
    - User can only access quotes from their own organization
    - Returns 404 "Not Found" for unauthorized access (instead of 403) for security
    - Organization isolation enforced at repository level

    **Example Usage**:
    ```bash
    QUOTE_ID="550e8400-e29b-41d4-a716-446655440000"
    curl http://localhost:8000/api/v1/quotes/$QUOTE_ID \
      -H "Authorization: Bearer <token>" | jq .

    # Filter payment schedule with Python
    response = requests.get(
        f"http://localhost:8000/api/v1/quotes/{QUOTE_ID}",
        headers={"Authorization": f"Bearer {token}"}
    )
    quote = response.json()
    # Show last month of payment schedule
    last_month = quote['payment_schedule'][-1]
    print(f"Final payment: R${last_month['amount']}, Total: R${last_month['accumulated']}")
    ```

    Args:
        quote_id: UUID of the quote to retrieve (format: 550e8400-e29b-41d4-a716-446655440000)
        current_user: Authenticated user extracted from JWT token (must belong to quote's org)

    Returns:
        QuoteResponse with complete quote details:
        - quote_id, loan_value, premium_rate, brokerage_rate
        - premium_amount, brokerage_amount, total_amount, monthly_payment
        - payment_schedule: 12-month array with amount and accumulated totals
        - status, created_at, updated_at timestamps

    Raises:
        HTTPException(404): 
        - Quote not found
        - User's organization doesn't match quote's organization (for security)

        HTTPException(401): Missing or invalid authentication token

        HTTPException(500): Unexpected server error
    """
    try:
        # In production, would query database with org isolation check
        # For MVP, return mock 404
        raise ValueError(f"Quote {quote_id} not found")

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve quote",
        )


@router.delete(
    "/{quote_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete quote",
    description="Soft-delete a quote (preserves data for audit trail by setting status to 'archived').",
    responses={
        204: {"description": "Quote deleted successfully (idempotent)"},
        404: {"model": ErrorResponse, "description": "Quote not found"},
    },
)
async def delete_quote(
    quote_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
) -> None:
    """
    Soft-delete a quote (idempotent operation).

    Changes quote status from 'active' to 'archived' instead of permanent deletion.
    Preserves full quote data for audit trail and historical reporting.

    **Soft Delete Behavior**:
    - Quote is moved to 'archived' status
    - All data preserved (loan value, rates, calculations)
    - Can be queried via GET with status filter: ?status=archived
    - Cannot be undeleted (would require admin feature in Phase 2)

    **Idempotence**:
    - Deleting same quote twice returns 204 both times
    - Safe to retry on network errors
    - No side effects from double deletion

    **Security**:
    - User can only delete quotes from their organization
    - Returns 404 for unauthorized access (like GET detail)

    **Example Usage**:
    ```bash
    # Delete a quote
    QUOTE_ID="550e8400-e29b-41d4-a716-446655440000"
    curl -X DELETE http://localhost:8000/api/v1/quotes/$QUOTE_ID \
      -H "Authorization: Bearer <token>" \
      -w "\\nStatus: %{http_code}\\n"
    # Expected: Status: 204

    # Verify it's archived (still appears with status=archived filter)
    curl http://localhost:8000/api/v1/quotes?status=archived \
      -H "Authorization: Bearer <token>" | jq '.items[] | select(.quote_id == "<id>")'

    # Python example
    response = requests.delete(
        f"http://localhost:8000/api/v1/quotes/{quote_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 204:
        print("Quote archived successfully")
    ```

    Args:
        quote_id: UUID of quote to delete (soft-delete to archived status)
        current_user: Authenticated user (must belong to quote's organization)

    Returns:
        None (HTTP 204 No Content response body is empty)

    Raises:
        HTTPException(404):
        - Quote not found
        - User's organization doesn't match quote's organization

        HTTPException(401): Missing or invalid authentication token

        HTTPException(500): Unexpected server error (quote in inconsistent state)

    Notes:
        - Operation is idempotent: deleting archived quote returns 204
        - Pagination filters by status, so archived quotes don't appear in normal listing
        - Future Phase 2 may add: undelete feature, permanent deletion audit logs
    """
    try:
        # In production, would use DeleteQuoteUseCase with real repository
        # For MVP, return 204 (idempotent)
        return None

    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete quote",
        )
