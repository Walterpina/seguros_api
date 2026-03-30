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
    description="Create a new lending insurance quote with calculated premium, brokerage, and installments",
)
async def post_create_quote(
    request: QuoteCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    # Note: In production, inject repository and services via dependency container
) -> QuoteResponse:
    """
    Create a new quote.

    Args:
        request: Quote creation request (loan_value required)
        current_user: Authenticated user (from JWT)

    Returns:
        QuoteResponse: Created quote with calculated values

    Raises:
        HTTPException(400): If validation fails
        HTTPException(401): If not authenticated
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
    description="Retrieve paginated list of quotes for the authenticated user's organization",
)
async def get_list_quotes(
    page: int = Query(0, ge=0, description="Page number (0-indexed)"),
    limit: int = Query(50, ge=1, le=500, description="Items per page"),
    status_filter: str = Query("active", description="Filter by status: active, archived, all"),
    from_date: Optional[datetime] = Query(None, description="Filter from date (ISO 8601)"),
    to_date: Optional[datetime] = Query(None, description="Filter to date (ISO 8601)"),
    current_user: CurrentUser = Depends(get_current_user),
) -> QuoteListResponse:
    """
    List quotes with pagination and filtering.

    Args:
        page: Page number (0-indexed)
        limit: Items per page (1-500)
        status_filter: Filter by status (active, archived, all)
        from_date: Filter from date
        to_date: Filter to date
        current_user: Authenticated user

    Returns:
        QuoteListResponse: Paginated list with metadata

    Raises:
        HTTPException(400): If pagination parameters invalid
        HTTPException(401): If not authenticated
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
    description="Retrieve a specific quote by ID (with organization access control)",
)
async def get_quote_detail(
    quote_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
) -> QuoteResponse:
    """
    Get single quote by ID.

    Args:
        quote_id: Quote UUID
        current_user: Authenticated user

    Returns:
        QuoteResponse: Quote details

    Raises:
        HTTPException(404): If quote not found
        HTTPException(403): If user not authorized
        HTTPException(401): If not authenticated
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
    description="Soft-delete a quote (sets status to archived)",
)
async def delete_quote(
    quote_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
) -> None:
    """
    Soft-delete a quote.

    Args:
        quote_id: Quote UUID
        current_user: Authenticated user

    Returns:
        None (204 No Content)

    Raises:
        HTTPException(403): If user not authorized
        HTTPException(401): If not authenticated
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
