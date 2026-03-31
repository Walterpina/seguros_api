"""Integration tests for Quote API endpoints."""

import pytest
from decimal import Decimal
from uuid import uuid4, UUID
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.main import app
from src.infrastructure.database.models import Quote, Configuration


@pytest.mark.integration
class TestQuoteEndpoints:
    """Test Quote API endpoints with real FastAPI app."""

    @pytest.fixture
    def client(self):
        """Provide FastAPI test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_jwt_token(self):
        """Generate a mock JWT token for testing."""
        from src.api.security.jwt_handler import JWTHandler

        jwt_handler = JWTHandler()
        token = jwt_handler.create_token(
            user_id=uuid4(),
            organization_id=uuid4(),
            role="user",
        )
        return token

    def test_health_check_endpoint(self, client):
        """Test health check endpoint is accessible."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data

    def test_swagger_docs_endpoint(self, client):
        """Test Swagger documentation is available."""
        response = client.get("/api/docs")

        assert response.status_code == 200
        assert b"swagger" in response.content.lower()

    def test_openapi_schema_endpoint(self, client):
        """Test OpenAPI schema is available."""
        response = client.get("/api/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert data["openapi"] in ["3.0.2", "3.1.0"]
        assert "paths" in data

    def test_create_quote_without_auth(self, client):
        """Test creating quote without JWT returns 401."""
        response = client.post(
            "/api/v1/quotes",
            json={"loan_value": 100000.00},
        )

        assert response.status_code == 401  # Missing auth credentials

    def test_create_quote_with_auth(self, client, mock_jwt_token):
        """Test creating quote with valid JWT token."""
        headers = {"Authorization": f"Bearer {mock_jwt_token}"}
        response = client.post(
            "/api/v1/quotes",
            headers=headers,
            json={"loan_value": 100000.00},
        )

        assert response.status_code == 201
        data = response.json()
        assert "quote_id" in data
        assert float(data["loan_value"]) == 100000.00
        assert float(data["premium_amount"]) > 0
        assert float(data["brokerage_amount"]) > 0
        assert float(data["total_amount"]) > 0

    def test_create_quote_with_custom_rates(self, client, mock_jwt_token):
        """Test creating quote with custom premium/brokerage rates."""
        headers = {"Authorization": f"Bearer {mock_jwt_token}"}
        response = client.post(
            "/api/v1/quotes",
            headers=headers,
            json={
                "loan_value": 100000.00,
                "premium_rate": 0.05,
                "brokerage_rate": 0.20,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert float(data["premium_rate"]) == 0.05
        assert float(data["brokerage_rate"]) == 0.20

    def test_create_quote_invalid_loan_value(self, client, mock_jwt_token):
        """Test creating quote with invalid loan_value returns 422."""
        headers = {"Authorization": f"Bearer {mock_jwt_token}"}

        # Test zero loan_value
        response = client.post(
            "/api/v1/quotes",
            headers=headers,
            json={"loan_value": 0},
        )
        assert response.status_code == 422

        # Test negative loan_value
        response = client.post(
            "/api/v1/quotes",
            headers=headers,
            json={"loan_value": -100000},
        )
        assert response.status_code == 422

    def test_create_quote_missing_loan_value(self, client, mock_jwt_token):
        """Test creating quote without loan_value returns 422."""
        headers = {"Authorization": f"Bearer {mock_jwt_token}"}
        response = client.post(
            "/api/v1/quotes",
            headers=headers,
            json={},
        )

        assert response.status_code == 422

    def test_create_quote_invalid_rate(self, client, mock_jwt_token):
        """Test creating quote with invalid rates returns 422."""
        headers = {"Authorization": f"Bearer {mock_jwt_token}"}

        # Test premium_rate > 1
        response = client.post(
            "/api/v1/quotes",
            headers=headers,
            json={
                "loan_value": 100000.00,
                "premium_rate": 1.5,
            },
        )
        assert response.status_code == 422

        # Test brokerage_rate < 0
        response = client.post(
            "/api/v1/quotes",
            headers=headers,
            json={
                "loan_value": 100000.00,
                "brokerage_rate": -0.1,
            },
        )
        assert response.status_code == 422

    def test_list_quotes_without_auth(self, client):
        """Test listing quotes without JWT returns 401."""
        response = client.get("/api/v1/quotes")

        assert response.status_code == 401

    def test_list_quotes_with_auth(self, client, mock_jwt_token):
        """Test listing quotes with valid JWT."""
        headers = {"Authorization": f"Bearer {mock_jwt_token}"}
        response = client.get("/api/v1/quotes", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert "pages" in data

    def test_list_quotes_with_pagination(self, client, mock_jwt_token):
        """Test listing quotes with pagination parameters."""
        headers = {"Authorization": f"Bearer {mock_jwt_token}"}
        response = client.get(
            "/api/v1/quotes",
            headers=headers,
            params={"page": 0, "limit": 10},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 0
        assert data["limit"] == 10

    def test_list_quotes_invalid_pagination(self, client, mock_jwt_token):
        """Test listing quotes with invalid pagination returns 400."""
        headers = {"Authorization": f"Bearer {mock_jwt_token}"}

        # Test negative page
        response = client.get(
            "/api/v1/quotes",
            headers=headers,
            params={"page": -1},
        )
        assert response.status_code == 422  # Validation error

    def test_get_quote_detail_without_auth(self, client):
        """Test getting quote without JWT returns 401."""
        quote_id = uuid4()
        response = client.get(f"/api/v1/quotes/{quote_id}")

        assert response.status_code == 401

    def test_get_quote_detail_not_found(self, client, mock_jwt_token):
        """Test getting non-existent quote returns 404."""
        headers = {"Authorization": f"Bearer {mock_jwt_token}"}
        fake_quote_id = uuid4()
        response = client.get(
            f"/api/v1/quotes/{fake_quote_id}",
            headers=headers,
        )

        assert response.status_code == 404

    def test_delete_quote_without_auth(self, client):
        """Test deleting quote without JWT returns 401."""
        quote_id = uuid4()
        response = client.delete(f"/api/v1/quotes/{quote_id}")

        assert response.status_code == 401

    def test_delete_quote_success(self, client, mock_jwt_token):
        """Test deleting quote returns 204."""
        headers = {"Authorization": f"Bearer {mock_jwt_token}"}
        fake_quote_id = uuid4()
        response = client.delete(
            f"/api/v1/quotes/{fake_quote_id}",
            headers=headers,
        )

        # MVP: returns 204 (idempotent)
        assert response.status_code == 204

    def test_quote_payment_schedule_in_response(self, client, mock_jwt_token):
        """Test that quote response includes payment schedule."""
        headers = {"Authorization": f"Bearer {mock_jwt_token}"}
        response = client.post(
            "/api/v1/quotes",
            headers=headers,
            json={"loan_value": 100000.00},
        )

        assert response.status_code == 201
        data = response.json()
        assert "payment_schedule" in data
        assert len(data["payment_schedule"]) == 12
        # Verify month sequence
        for i, payment in enumerate(data["payment_schedule"], 1):
            assert payment["month"] == i
            assert float(payment["amount"]) > 0
            assert float(payment["accumulated"]) > 0

    def test_error_response_format(self, client, mock_jwt_token):
        """Test error response has correct format."""
        headers = {"Authorization": f"Bearer {mock_jwt_token}"}
        response = client.post(
            "/api/v1/quotes",
            headers=headers,
            json={"loan_value": -100},
        )

        assert response.status_code == 422
        data = response.json()
        assert "code" in data
        assert "message" in data


# Database-backed integration tests
@pytest.mark.integration
class TestQuoteEndpointsWithDatabase:
    """Test Quote API endpoints with real database persistence."""

    @pytest.fixture
    def client(self):
        """Provide FastAPI test client."""
        return TestClient(app)

    @pytest.fixture
    def org_id(self):
        """Provide a test organization ID."""
        return uuid4()

    @pytest.fixture
    def user_id(self):
        """Provide a test user ID."""
        return uuid4()

    @pytest.fixture
    def jwt_token_for_org(self, org_id, user_id):
        """Generate JWT token for specific organization."""
        from src.api.security.jwt_handler import JWTHandler

        jwt_handler = JWTHandler()
        token = jwt_handler.create_token(
            user_id=user_id,
            organization_id=org_id,
            role="user",
        )
        return token

    @pytest.fixture
    def sample_quote_in_db(self, test_db_session, org_id, user_id):
        """Create a sample quote in the database."""
        quote = Quote(
            id=uuid4(),
            organization_id=org_id,
            user_id=user_id,
            loan_value=Decimal("100000.00"),
            premium_rate=Decimal("0.045"),
            brokerage_rate=Decimal("0.15"),
            premium_amount=Decimal("4500.00"),
            brokerage_amount=Decimal("700.00"),
            total_amount=Decimal("105200.00"),
            monthly_payment=Decimal("8766.67"),
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        test_db_session.add(quote)
        test_db_session.commit()
        return quote

    def test_create_quote_persists_to_db(
        self, client, jwt_token_for_org, test_db_session, org_id
    ):
        """Test that created quote is persisted to database."""
        headers = {"Authorization": f"Bearer {jwt_token_for_org}"}
        response = client.post(
            "/api/v1/quotes",
            headers=headers,
            json={"loan_value": 100000.00},
        )

        assert response.status_code == 201
        data = response.json()
        quote_id = UUID(data["quote_id"])

        # Verify persistence in database
        persisted_quote = test_db_session.query(Quote).filter_by(id=quote_id).first()
        assert persisted_quote is not None
        assert persisted_quote.loan_value == Decimal("100000.00")
        assert persisted_quote.organization_id == org_id
        assert persisted_quote.status == "active"

    def test_list_quotes_includes_db_quotes(
        self, client, jwt_token_for_org, test_db_session, org_id, user_id
    ):
        """Test that list quotes includes quotes persisted in database."""
        # Create sample quotes in DB
        for i in range(3):
            quote = Quote(
                id=uuid4(),
                organization_id=org_id,
                user_id=user_id,
                loan_value=Decimal("100000.00") + Decimal(i * 10000),
                premium_rate=Decimal("0.045"),
                brokerage_rate=Decimal("0.15"),
                premium_amount=Decimal("4500.00"),
                brokerage_amount=Decimal("700.00"),
                total_amount=Decimal("105200.00"),
                monthly_payment=Decimal("8766.67"),
                status="active",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            test_db_session.add(quote)
        test_db_session.commit()

        # List quotes via API
        headers = {"Authorization": f"Bearer {jwt_token_for_org}"}
        response = client.get("/api/v1/quotes", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_list_quotes_org_isolation(
        self, client, test_db_session, user_id
    ):
        """Test that users only see quotes from their organization."""
        # Create quotes for different organizations
        org1_id = uuid4()
        org2_id = uuid4()

        for i in range(2):
            quote = Quote(
                id=uuid4(),
                organization_id=org1_id,
                user_id=user_id,
                loan_value=Decimal("100000.00"),
                premium_rate=Decimal("0.045"),
                brokerage_rate=Decimal("0.15"),
                premium_amount=Decimal("4500.00"),
                brokerage_amount=Decimal("700.00"),
                total_amount=Decimal("105200.00"),
                monthly_payment=Decimal("8766.67"),
                status="active",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            test_db_session.add(quote)

        for i in range(3):
            quote = Quote(
                id=uuid4(),
                organization_id=org2_id,
                user_id=user_id,
                loan_value=Decimal("100000.00"),
                premium_rate=Decimal("0.045"),
                brokerage_rate=Decimal("0.15"),
                premium_amount=Decimal("4500.00"),
                brokerage_amount=Decimal("700.00"),
                total_amount=Decimal("105200.00"),
                monthly_payment=Decimal("8766.67"),
                status="active",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            test_db_session.add(quote)

        test_db_session.commit()

        # Create token for org1
        from src.api.security.jwt_handler import JWTHandler

        jwt_handler = JWTHandler()
        org1_token = jwt_handler.create_token(
            user_id=user_id,
            organization_id=org1_id,
            role="user",
        )

        # List quotes for org1 - should only see org1 quotes
        headers = {"Authorization": f"Bearer {org1_token}"}
        response = client.get("/api/v1/quotes", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2  # Only org1 quotes
        for item in data["items"]:
            assert item["organization_id"] == str(org1_id)

    def test_list_quotes_filters_by_status(
        self, client, jwt_token_for_org, test_db_session, org_id, user_id
    ):
        """Test that list quotes can filter by status."""
        # Create active and archived quotes
        for status in ["active", "active", "archived"]:
            quote = Quote(
                id=uuid4(),
                organization_id=org_id,
                user_id=user_id,
                loan_value=Decimal("100000.00"),
                premium_rate=Decimal("0.045"),
                brokerage_rate=Decimal("0.15"),
                premium_amount=Decimal("4500.00"),
                brokerage_amount=Decimal("700.00"),
                total_amount=Decimal("105200.00"),
                monthly_payment=Decimal("8766.67"),
                status=status,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            test_db_session.add(quote)
        test_db_session.commit()

        headers = {"Authorization": f"Bearer {jwt_token_for_org}"}
        response = client.get(
            "/api/v1/quotes",
            headers=headers,
            params={"status": "active"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        for item in data["items"]:
            assert item["status"] == "active"

    def test_delete_quote_changes_status_to_archived(
        self, client, jwt_token_for_org, test_db_session, sample_quote_in_db
    ):
        """Test that delete quote soft-deletes by changing status."""
        quote_id = sample_quote_in_db.id

        headers = {"Authorization": f"Bearer {jwt_token_for_org}"}
        response = client.delete(f"/api/v1/quotes/{quote_id}", headers=headers)

        assert response.status_code == 204

        # Verify status changed in database
        quote = test_db_session.query(Quote).filter_by(id=quote_id).first()
        assert quote is not None
        assert quote.status == "archived"

    def test_get_quote_returns_persisted_data(
        self, client, jwt_token_for_org, sample_quote_in_db
    ):
        """Test that get quote returns correctly persisted data."""
        quote_id = sample_quote_in_db.id

        headers = {"Authorization": f"Bearer {jwt_token_for_org}"}
        response = client.get(
            f"/api/v1/quotes/{quote_id}",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["quote_id"] == str(quote_id)
        assert float(data["loan_value"]) == 100000.00
        assert float(data["premium_amount"]) == 4500.00
        assert float(data["brokerage_amount"]) == 700.00
        assert float(data["total_amount"]) == 105200.00

    def test_list_quotes_pagination_ordering(
        self, client, jwt_token_for_org, test_db_session, org_id, user_id
    ):
        """Test that list quotes respects pagination and ordering."""
        # Create 15 quotes with different creation times
        for i in range(15):
            from datetime import timedelta

            quote = Quote(
                id=uuid4(),
                organization_id=org_id,
                user_id=user_id,
                loan_value=Decimal("100000.00") + Decimal(i * 1000),
                premium_rate=Decimal("0.045"),
                brokerage_rate=Decimal("0.15"),
                premium_amount=Decimal("4500.00"),
                brokerage_amount=Decimal("700.00"),
                total_amount=Decimal("105200.00"),
                monthly_payment=Decimal("8766.67"),
                status="active",
                created_at=datetime.utcnow() - timedelta(seconds=15 - i),
                updated_at=datetime.utcnow(),
            )
            test_db_session.add(quote)
        test_db_session.commit()

        headers = {"Authorization": f"Bearer {jwt_token_for_org}"}

        # Get first page (page=0, limit=10)
        response = client.get(
            "/api/v1/quotes",
            headers=headers,
            params={"page": 0, "limit": 10},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 15
        assert len(data["items"]) == 10
        assert data["page"] == 0
        assert data["limit"] == 10
        assert data["pages"] == 2  # ceil(15 / 10)

        # Get second page
        response = client.get(
            "/api/v1/quotes",
            headers=headers,
            params={"page": 1, "limit": 10},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5  # Remaining quotes
        assert data["page"] == 1

