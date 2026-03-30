"""JWT authentication and token handling."""

from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from uuid import UUID

from jose import JWTError, jwt

from config.settings import get_settings


class TokenPayload:
    """JWT token payload."""

    def __init__(
        self,
        user_id: UUID,
        organization_id: UUID,
        role: str = "user",
        exp: Optional[datetime] = None,
    ):
        """
        Initialize token payload.

        Args:
            user_id: User UUID
            organization_id: Organization UUID
            role: User role (e.g., 'user', 'admin')
            exp: Expiration datetime (optional)
        """
        self.user_id = user_id
        self.organization_id = organization_id
        self.role = role
        self.exp = exp

    def to_dict(self) -> Dict:
        """Convert to dictionary for JWT encoding."""
        payload = {
            "sub": str(self.user_id),
            "user_id": str(self.user_id),
            "org_id": str(self.organization_id),
            "role": self.role,
        }

        if self.exp:
            payload["exp"] = int(self.exp.timestamp())

        return payload

    @classmethod
    def from_dict(cls, data: Dict) -> "TokenPayload":
        """Create TokenPayload from JWT decoded dictionary."""
        return cls(
            user_id=UUID(data.get("user_id") or data.get("sub")),
            organization_id=UUID(data.get("org_id")),
            role=data.get("role", "user"),
            exp=datetime.fromtimestamp(data.get("exp"), tz=timezone.utc)
            if data.get("exp")
            else None,
        )


class InvalidTokenError(Exception):
    """Raised when token is invalid or expired."""

    pass


class JWTHandler:
    """Handler for JWT token creation and verification."""

    def __init__(self):
        """Initialize with settings."""
        self.settings = get_settings()

    def create_token(
        self,
        user_id: UUID,
        organization_id: UUID,
        role: str = "user",
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a JWT token.

        Args:
            user_id: User UUID
            organization_id: Organization UUID
            role: User role (default 'user')
            expires_delta: Custom expiration duration (default from config)

        Returns:
            str: Encoded JWT token

        Raises:
            ValueError: If JWT secret is too short
        """
        if len(self.settings.jwt_secret_key) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be at least 32 characters for security"
            )

        # Set expiration
        if expires_delta is None:
            expires_delta = timedelta(minutes=self.settings.jwt_expiration_minutes)

        expire = datetime.now(timezone.utc) + expires_delta

        # Create payload
        payload = TokenPayload(
            user_id=user_id,
            organization_id=organization_id,
            role=role,
            exp=expire,
        )

        # Encode and return
        encoded_jwt = jwt.encode(
            payload.to_dict(),
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm,
        )

        return encoded_jwt

    def verify_token(self, token: str) -> TokenPayload:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token string

        Returns:
            TokenPayload: Decoded token payload

        Raises:
            InvalidTokenError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm],
            )

            # Check expiration manually
            if "exp" in payload:
                exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
                if exp_time < datetime.now(timezone.utc):
                    raise InvalidTokenError("Token has expired")

            return TokenPayload.from_dict(payload)

        except JWTError as e:
            raise InvalidTokenError(f"Invalid token: {str(e)}")
        except ValueError as e:
            raise InvalidTokenError(f"Token error: {str(e)}")

    def decode_token(self, token: str) -> Dict:
        """
        Decode token without verification (use with caution).

        Args:
            token: JWT token string

        Returns:
            dict: Decoded payload

        Raises:
            InvalidTokenError: If token cannot be decoded
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm],
            )
            return payload

        except JWTError as e:
            raise InvalidTokenError(f"Cannot decode token: {str(e)}")
