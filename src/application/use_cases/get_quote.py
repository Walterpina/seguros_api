"""Get Quote use case."""

from uuid import UUID

from src.application.dtos.mappers import quote_entity_to_response
from src.application.dtos.quote_dto import QuoteResponse
from src.infrastructure.repositories.quote_repository import QuoteRepository


class GetQuoteUseCase:
    """Use case for retrieving a specific quote."""

    def __init__(self, repository: QuoteRepository):
        """
        Initialize use case.

        Args:
            repository: Quote repository
        """
        self.repository = repository

    def execute(
        self,
        quote_id: UUID,
        user_id: UUID,
        organization_id: UUID,
    ) -> QuoteResponse:
        """
        Execute quote retrieval.

        Args:
            quote_id: Quote ID
            user_id: User ID (for permission check)
            organization_id: Organization ID (for permission check)

        Returns:
            QuoteResponse: Quote details

        Raises:
            ValueError: If quote not found
            PermissionError: If user/org not authorized
        """
        # Retrieve quote
        quote_entity = self.repository.get(quote_id)

        if not quote_entity:
            raise ValueError(f"Quote {quote_id} not found")

        # Future: Implement permission checking
        # if quote.organization_id != organization_id:
        #     raise PermissionError(f"Not authorized for quote {quote_id}")

        # Convert to response
        return quote_entity_to_response(quote_entity, user_id, organization_id)
