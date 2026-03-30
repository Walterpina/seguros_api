"""Unit tests for JWT authentication."""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from src.api.security.jwt_handler import (
    InvalidTokenError,
    JWTHandler,
    TokenPayload,
)


@pytest.mark.unit
class TestJWTHandler:
    """Test JWT token creation and verification."""

    @pytest.fixture
    def jwt_handler(self):
        """Provide JWT handler instance."""
        return JWTHandler()

    def test_create_token_success(self, jwt_handler):
        """Test creating a valid JWT token."""
        user_id = uuid4()
        org_id = uuid4()

        token = jwt_handler.create_token(
            user_id=user_id,
            organization_id=org_id,
            role="user",
        )

        assert isinstance(token, str)
        assert len(token) > 0
        # JWT format: header.payload.signature
        assert token.count(".") == 2

    def test_create_token_with_custom_expiration(self, jwt_handler):
        """Test creating token with custom expiration."""
        user_id = uuid4()
        org_id = uuid4()
        expires_delta = timedelta(hours=12)

        token = jwt_handler.create_token(
            user_id=user_id,
            organization_id=org_id,
            expires_delta=expires_delta,
        )

        assert isinstance(token, str)

    def test_verify_token_success(self, jwt_handler):
        """Test verifying a valid token."""
        user_id = uuid4()
        org_id = uuid4()
        role = "admin"

        # Create token
        token = jwt_handler.create_token(
            user_id=user_id,
            organization_id=org_id,
            role=role,
        )

        # Verify token
        payload = jwt_handler.verify_token(token)

        assert payload.user_id == user_id
        assert payload.organization_id == org_id
        assert payload.role == role

    def test_verify_token_invalid_signature(self, jwt_handler):
        """Test verifying token with tampered signature."""
        user_id = uuid4()
        org_id = uuid4()

        # Create token
        token = jwt_handler.create_token(
            user_id=user_id,
            organization_id=org_id,
        )

        # Tamper with token
        tampered_token = token[:-5] + "XXXXX"

        # Verify should fail
        with pytest.raises(InvalidTokenError):
            jwt_handler.verify_token(tampered_token)

    def test_verify_token_expired(self, jwt_handler):
        """Test verifying expired token."""
        user_id = uuid4()
        org_id = uuid4()

        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)
        token = jwt_handler.create_token(
            user_id=user_id,
            organization_id=org_id,
            expires_delta=expires_delta,
        )

        # Verify should fail (expired)
        with pytest.raises(InvalidTokenError, match="expired"):
            jwt_handler.verify_token(token)

    def test_verify_token_invalid_format(self, jwt_handler):
        """Test verifying malformed token."""
        with pytest.raises(InvalidTokenError):
            jwt_handler.verify_token("not.a.token")

    def test_verify_token_empty_string(self, jwt_handler):
        """Test verifying empty token."""
        with pytest.raises(InvalidTokenError):
            jwt_handler.verify_token("")

    def test_decode_token_success(self, jwt_handler):
        """Test decoding token payload."""
        user_id = uuid4()
        org_id = uuid4()

        # Create token
        token = jwt_handler.create_token(
            user_id=user_id,
            organization_id=org_id,
        )

        # Decode
        payload = jwt_handler.decode_token(token)

        assert payload["user_id"] == str(user_id)
        assert payload["org_id"] == str(org_id)
        assert "exp" in payload

    def test_token_payload_to_dict(self):
        """Test TokenPayload to_dict conversion."""
        user_id = uuid4()
        org_id = uuid4()
        exp_time = datetime.now(timezone.utc) + timedelta(hours=1)

        payload = TokenPayload(
            user_id=user_id,
            organization_id=org_id,
            role="admin",
            exp=exp_time,
        )

        payload_dict = payload.to_dict()

        assert payload_dict["user_id"] == str(user_id)
        assert payload_dict["org_id"] == str(org_id)
        assert payload_dict["role"] == "admin"
        assert "exp" in payload_dict

    def test_token_payload_from_dict(self):
        """Test TokenPayload from_dict creation."""
        user_id = uuid4()
        org_id = uuid4()
        exp_timestamp = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())

        data = {
            "user_id": str(user_id),
            "org_id": str(org_id),
            "role": "user",
            "exp": exp_timestamp,
        }

        payload = TokenPayload.from_dict(data)

        assert payload.user_id == user_id
        assert payload.organization_id == org_id
        assert payload.role == "user"

    def test_token_default_expiration(self, jwt_handler, monkeypatch):
        """Test token uses config default expiration."""
        # Mock config with 1 hour expiration
        monkeypatch.setenv("JWT_EXPIRATION_MINUTES", "60")

        jwt_handler = JWTHandler()
        token = jwt_handler.create_token(
            user_id=uuid4(),
            organization_id=uuid4(),
        )

        # Should not raise (token is fresh)
        payload = jwt_handler.verify_token(token)
        assert payload is not None

    def test_multiple_tokens_different_ids(self, jwt_handler):
        """Test creating tokens for different users."""
        user_id_1 = uuid4()
        user_id_2 = uuid4()
        org_id = uuid4()

        token_1 = jwt_handler.create_token(user_id_1, org_id)
        token_2 = jwt_handler.create_token(user_id_2, org_id)

        assert token_1 != token_2

        payload_1 = jwt_handler.verify_token(token_1)
        payload_2 = jwt_handler.verify_token(token_2)

        assert payload_1.user_id == user_id_1
        assert payload_2.user_id == user_id_2
