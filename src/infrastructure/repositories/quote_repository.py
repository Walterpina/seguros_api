"""Quote repository interface (Repository pattern)."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.quote import Quote


class QuoteRepository(ABC):
    """Abstract base class for Quote persistence."""

    @abstractmethod
    def create(
        self, quote_entity: Quote, user_id: UUID, organization_id: UUID
    ) -> Quote:
        """
        Create and persist a quote.

        Args:
            quote_entity: Quote domain entity
            user_id: User UUID
            organization_id: Organization UUID

        Returns:
            Quote: Persisted quote with database ID
        """
        pass

    @abstractmethod
    def get(self, quote_id: UUID, organization_id: Optional[UUID] = None) -> Optional[Quote]:
        """
        Retrieve a quote by ID.

        Args:
            quote_id: Quote UUID

        Returns:
            Quote or None if not found
        """
        pass

    @abstractmethod
    def list(
        self,
        organization_id: UUID,
        user_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0,
        status: str = "active",
    ) -> tuple[List[Quote], int]:
        """
        List quotes with pagination.

        Args:
            organization_id: Filter by organization
            user_id: Optional filter by user
            limit: Pagination limit (default 50)
            offset: Pagination offset (default 0)
            status: Filter by status (default 'active')

        Returns:
            Tuple: (quotes_list, total_count)
        """
        pass

    @abstractmethod
    def delete(self, quote_id: UUID, organization_id: Optional[UUID] = None) -> bool:
        """
        Soft-delete a quote (set status='archived').

        Args:
            quote_id: Quote UUID

        Returns:
            bool: True if deleted, False if not found
        """
        pass

    @abstractmethod
    def update_status(self, quote_id: UUID, status: str) -> bool:
        """
        Update quote status.

        Args:
            quote_id: Quote UUID
            status: New status ('active', 'archived', 'cancelled')

        Returns:
            bool: True if updated, False if not found
        """
        pass
