"""SQL Quote Repository implementation using SQLAlchemy."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.domain.entities.quote import Quote
from src.infrastructure.database.models import Quote as QuoteModel
from src.infrastructure.repositories.quote_repository import QuoteRepository


class SQLQuoteRepository(QuoteRepository):
    """SQLAlchemy implementation of QuoteRepository."""

    def __init__(self, session: Session):
        """
        Initialize with database session.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def create(
        self, quote_entity: Quote, user_id: UUID, organization_id: UUID
    ) -> Quote:
        """Create and persist a quote."""
        # Convert domain entity to ORM model
        quote_model = QuoteModel(
            id=quote_entity.id,
            organization_id=organization_id,
            user_id=user_id,
            loan_value=quote_entity.loan_value,
            premium_rate=quote_entity.premium_rate,
            premium_amount=quote_entity.premium_amount,
            brokerage_rate=quote_entity.brokerage_rate,
            brokerage_amount=quote_entity.brokerage_amount,
            total_amount=quote_entity.total_amount,
            monthly_payment=quote_entity.monthly_payment,
            status=quote_entity.status,
            created_at=quote_entity.created_at,
            updated_at=quote_entity.updated_at,
        )

        self.session.add(quote_model)
        self.session.commit()

        # Return domain entity with persisted ID
        return quote_entity

    def get(self, quote_id: UUID, organization_id: Optional[UUID] = None) -> Optional[Quote]:
        """Retrieve a quote by ID and optionally organization."""
        query = self.session.query(QuoteModel).filter_by(id=quote_id)
        if organization_id:
            query = query.filter_by(organization_id=organization_id)
        
        quote_model = query.first()

        if not quote_model:
            return None

        # Convert ORM model back to domain entity
        return self._orm_to_entity(quote_model)

    def list(
        self,
        organization_id: UUID,
        user_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0,
        status: str = "active",
    ) -> tuple[List[Quote], int]:
        """List quotes with pagination."""
        query = self.session.query(QuoteModel).filter_by(
            organization_id=organization_id, status=status
        )

        if user_id:
            query = query.filter_by(user_id=user_id)

        total_count = query.count()

        # Fetch paginated results
        results = query.order_by(QuoteModel.created_at.desc()).limit(limit).offset(
            offset
        ).all()

        # Convert ORM models to domain entities
        quotes = [self._orm_to_entity(model) for model in results]

        return quotes, total_count

    def delete(self, quote_id: UUID, organization_id: Optional[UUID] = None) -> bool:
        """Soft-delete a quote (set status='archived')."""
        query = self.session.query(QuoteModel).filter_by(id=quote_id)
        if organization_id:
            query = query.filter_by(organization_id=organization_id)
            
        quote_model = query.first()

        if not quote_model:
            return False

        quote_model.status = "archived"
        self.session.commit()

        return True

    def update_status(self, quote_id: UUID, status: str) -> bool:
        """Update quote status."""
        valid_statuses = {"active", "archived", "cancelled"}

        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}")

        quote_model = self.session.query(QuoteModel).filter_by(id=quote_id).first()

        if not quote_model:
            return False

        quote_model.status = status
        self.session.commit()

        return True

    @staticmethod
    def _orm_to_entity(quote_model: QuoteModel) -> Quote:
        """Convert ORM model to domain entity."""
        return Quote(
            id=quote_model.id,
            loan_value=quote_model.loan_value,
            premium_rate=quote_model.premium_rate,
            brokerage_rate=quote_model.brokerage_rate,
            status=quote_model.status,
            created_at=quote_model.created_at,
            updated_at=quote_model.updated_at,
        )
