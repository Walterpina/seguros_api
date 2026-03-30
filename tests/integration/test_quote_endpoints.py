"""Integration tests for Quote API endpoints."""

import pytest
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from src.api.main import app


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
        assert data["openapi"] == "3.0.2"
        assert "paths" in data

    def test_create_quote_without_auth(self, client):
        """Test creating quote without JWT returns 401."""
        response = client.post(
            "/api/v1/quotes",
            json={"loan_value": 100000.00},
        )

        assert response.status_code == 403  # Missing auth credentials

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
        assert data["loan_value"] == 100000.00
        assert data["premium_amount"] > 0
        assert data["brokerage_amount"] > 0
        assert data["total_amount"] > 0

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
        assert data["premium_rate"] == 0.05
        assert data["brokerage_rate"] == 0.20

    def test_create_quote_invalid_loan_value(self, client, mock_jwt_token):
        """Test creating quote with invalid loan_value returns 400."""
        headers = {"Authorization": f"Bearer {mock_jwt_token}"}

        # Test zero loan_value
        response = client.post(
            "/api/v1/quotes",
            headers=headers,
            json={"loan_value": 0},
        )
        assert response.status_code == 400

        # Test negative loan_value
        response = client.post(
            "/api/v1/quotes",
            headers=headers,
            json={"loan_value": -100000},
        )
        assert response.status_code == 400

    def test_create_quote_missing_loan_value(self, client, mock_jwt_token):
        """Test creating quote without loan_value returns 400."""
        headers = {"Authorization": f"Bearer {mock_jwt_token}"}
        response = client.post(
            "/api/v1/quotes",
            headers=headers,
            json={},
        )

        assert response.status_code == 400

    def test_create_quote_invalid_rate(self, client, mock_jwt_token):
        """Test creating quote with invalid rates returns 400."""
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
        assert response.status_code == 400

        # Test brokerage_rate < 0
        response = client.post(
            "/api/v1/quotes",
            headers=headers,
            json={
                "loan_value": 100000.00,
                "brokerage_rate": -0.1,
            },
        )
        assert response.status_code == 400

    def test_list_quotes_without_auth(self, client):
        """Test listing quotes without JWT returns 403."""
        response = client.get("/api/v1/quotes")

        assert response.status_code == 403

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
        """Test getting quote without JWT returns 403."""
        quote_id = uuid4()
        response = client.get(f"/api/v1/quotes/{quote_id}")

        assert response.status_code == 403

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
        """Test deleting quote without JWT returns 403."""
        quote_id = uuid4()
        response = client.delete(f"/api/v1/quotes/{quote_id}")

        assert response.status_code == 403

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
            assert payment["amount"] > 0
            assert payment["accumulated"] > 0

    def test_error_response_format(self, client, mock_jwt_token):
        """Test error response has correct format."""
        headers = {"Authorization": f"Bearer {mock_jwt_token}"}
        response = client.post(
            "/api/v1/quotes",
            headers=headers,
            json={"loan_value": -100},
        )

        assert response.status_code == 400
        data = response.json()
        assert "code" in data
        assert "message" in data
