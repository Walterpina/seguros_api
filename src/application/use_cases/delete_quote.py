"""Delete Quote use case."""

from uuid import UUID

from src.infrastructure.repositories.quote_repository import QuoteRepository


class DeleteQuoteUseCase:
    """Use case for deleting (soft-delete) a quote."""

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
        user_id: UUID = None,
        organization_id: UUID = None,
    ) -> bool:
        """
        Execute quote soft-delete.

        Args:
            quote_id: Quote ID to delete
            user_id: Optional user ID (for permission check)
            organization_id: Optional org ID (for permission check)

        Returns:
            bool: True if deleted, False if not found

        Raises:
            PermissionError: If user/org not authorized (future)
        """
        # Soft-delete (set status='archived')
        return self.repository.delete(quote_id, organization_id=organization_id)
