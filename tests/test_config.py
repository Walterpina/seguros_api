"""Test configuration and database connection."""

import pytest


@pytest.mark.unit
class TestDatabaseConfiguration:
    """Test database configuration and connection."""

    def test_models_import(self):
        """Test that models can be imported successfully."""
        from src.infrastructure.database.models import Base, Quote, Configuration

        assert Base is not None
        assert Quote.__tablename__ == "quotes"
        assert Configuration.__tablename__ == "configurations"

    def test_database_session_creation(self, test_db_session):
        """Test that a database session can be created."""
        assert test_db_session is not None

    def test_quote_model_instantiation(self):
        """Test that Quote model can be instantiated."""
        from src.infrastructure.database.models import Quote
        from datetime import datetime
        from decimal import Decimal
        from uuid import uuid4

        quote = Quote(
            organization_id=uuid4(),
            user_id=uuid4(),
            loan_value=Decimal("100000.00"),
            premium_rate=Decimal("0.045"),
            premium_amount=Decimal("4500.00"),
            brokerage_rate=Decimal("0.15"),
            brokerage_amount=Decimal("675.00"),
            total_amount=Decimal("105175.00"),
            monthly_payment=Decimal("8764.58"),
            status="active",
        )

        assert quote.loan_value == Decimal("100000.00")
        assert quote.status == "active"

    def test_configuration_model_instantiation(self):
        """Test that Configuration model can be instantiated."""
        from src.infrastructure.database.models import Configuration
        from datetime import datetime
        from decimal import Decimal
        from uuid import uuid4

        config = Configuration(
            organization_id=uuid4(),
            premium_rate=Decimal("0.045"),
            brokerage_rate=Decimal("0.15"),
            effective_from=datetime.utcnow(),
        )

        assert config.premium_rate == Decimal("0.045")
        assert config.brokerage_rate == Decimal("0.15")

    def test_database_insert_and_query(self, test_db_session):
        """Test basic insert and query operations."""
        from src.infrastructure.database.models import Quote
        from decimal import Decimal
        from uuid import uuid4

        org_id = uuid4()
        user_id = uuid4()

        quote = Quote(
            organization_id=org_id,
            user_id=user_id,
            loan_value=Decimal("100000.00"),
            premium_rate=Decimal("0.045"),
            premium_amount=Decimal("4500.00"),
            brokerage_rate=Decimal("0.15"),
            brokerage_amount=Decimal("675.00"),
            total_amount=Decimal("105175.00"),
            monthly_payment=Decimal("8764.58"),
        )

        test_db_session.add(quote)
        test_db_session.commit()

        retrieved = test_db_session.query(Quote).filter_by(id=quote.id).first()
        assert retrieved is not None
        assert retrieved.organization_id == org_id
        assert retrieved.loan_value == Decimal("100000.00")
