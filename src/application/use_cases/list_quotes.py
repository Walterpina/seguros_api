"""List Quotes use case."""

from typing import List
from uuid import UUID

from src.application.dtos.mappers import quote_entity_to_response
from src.application.dtos.quote_dto import QuoteListResponse, QuoteResponse
from src.infrastructure.repositories.quote_repository import QuoteRepository


class ListQuotesUseCase:
    """Use case for listing quotes with pagination."""

    def __init__(self, repository: QuoteRepository):
        """
        Initialize use case.

        Args:
            repository: Quote repository
        """
        self.repository = repository

    def execute(
        self,
        organization_id: UUID,
        user_id: UUID = None,
        page: int = 0,
        limit: int = 50,
    ) -> QuoteListResponse:
        """
        Execute quote list operation.

        Args:
            organization_id: Organization ID (required)
            user_id: Optional user ID filter
            page: Page number (0-indexed)
            limit: Page size

        Returns:
            QuoteListResponse: Paginated list of quotes
        """
        if page < 0:
            raise ValueError("page must be >= 0")

        if limit <= 0 or limit > 500:
            raise ValueError("limit must be between 1 and 500")

        # Get paginated results
        offset = page * limit
        quotes, total_count = self.repository.list(
            organization_id=organization_id,
            user_id=user_id,
            limit=limit,
            offset=offset,
            status="active",
        )

        # Convert to response DTOs
        items: List[QuoteResponse] = [
            quote_entity_to_response(quote, user_id, organization_id)
            for quote in quotes
        ]

        # Calculate total pages
        total_pages = (total_count + limit - 1) // limit  # Ceiling division

        return QuoteListResponse(
            items=items,
            total=total_count,
            page=page,
            limit=limit,
            pages=total_pages,
        )
