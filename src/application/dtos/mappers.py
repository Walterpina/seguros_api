"""DTO mappers: Convert between domain entities, ORM models, and DTOs."""

from datetime import datetime
from uuid import UUID

from src.application.dtos.quote_dto import QuoteCreateRequest, QuoteResponse
from src.domain.entities.quote import Quote
from src.infrastructure.database.models import Quote as QuoteModel


def quote_entity_to_response(
    quote_entity: Quote, user_id: UUID = None, organization_id: UUID = None
) -> QuoteResponse:
    """
    Convert domain Quote entity to QuoteResponse DTO.

    Args:
        quote_entity: Quote domain entity
        user_id: Optional user ID (not included in response)
        organization_id: Optional org ID (not included in response)

    Returns:
        QuoteResponse: Response DTO
    """
    return QuoteResponse(
        quote_id=quote_entity.id,
        loan_value=quote_entity.loan_value,
        premium_rate=quote_entity.premium_rate,
        premium_amount=quote_entity.premium_amount,
        brokerage_rate=quote_entity.brokerage_rate,
        brokerage_amount=quote_entity.brokerage_amount,
        total_amount=quote_entity.total_amount,
        monthly_payment=quote_entity.monthly_payment,
        payment_schedule=[
            {
                "month": p.month,
                "amount": p.amount,
                "accumulated": p.accumulated,
            }
            for p in quote_entity.payment_schedule.monthly_payments
        ] if quote_entity.payment_schedule else [],
        status=quote_entity.status,
        created_at=quote_entity.created_at,
        updated_at=quote_entity.updated_at,
    )


def orm_model_to_response(quote_model: QuoteModel) -> QuoteResponse:
    """
    Convert ORM QuoteModel to QuoteResponse DTO.

    Args:
        quote_model: SQLAlchemy Quote model

    Returns:
        QuoteResponse: Response DTO
    """
    return QuoteResponse(
        quote_id=quote_model.id,
        loan_value=quote_model.loan_value,
        premium_rate=quote_model.premium_rate,
        premium_amount=quote_model.premium_amount,
        brokerage_rate=quote_model.brokerage_rate,
        brokerage_amount=quote_model.brokerage_amount,
        total_amount=quote_model.total_amount,
        monthly_payment=quote_model.monthly_payment,
        payment_schedule=[],  # Will be recalculated or left empty from ORM
        status=quote_model.status,
        created_at=quote_model.created_at,
        updated_at=quote_model.updated_at,
    )


def request_dto_to_entity(request: QuoteCreateRequest) -> Quote:
    """
    Convert QuoteCreateRequest DTO to domain Quote entity.

    Args:
        request: Request DTO

    Returns:
        Quote: Domain entity (with calculated values)
    """
    return Quote(
        loan_value=request.loan_value,
        premium_rate=request.premium_rate or 0.045,  # default fallback
        brokerage_rate=request.brokerage_rate or 0.15,  # default fallback
    )
