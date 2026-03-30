"""FastAPI dependencies for authentication and authorization."""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.api.security.jwt_handler import InvalidTokenError, JWTHandler

# Security scheme for Swagger documentation
security = HTTPBearer(description="JWT Bearer token")


class CurrentUser:
    """Current authenticated user with ID, org_id, and role."""

    def __init__(self, user_id: UUID, organization_id: UUID, role: str = "user"):
        """
        Initialize current user.

        Args:
            user_id: User UUID
            organization_id: Organization UUID
            role: User role
        """
        self.user_id = user_id
        self.organization_id = organization_id
        self.role = role


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer credentials from Authorization header

    Returns:
        CurrentUser: Current user information

    Raises:
        HTTPException(401): If token is missing, invalid, or expired
        HTTPException(403): If user lacks required role
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        jwt_handler = JWTHandler()
        token_payload = jwt_handler.verify_token(token)

        return CurrentUser(
            user_id=token_payload.user_id,
            organization_id=token_payload.organization_id,
            role=token_payload.role,
        )

    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_organization(
    current_user: CurrentUser = Depends(get_current_user),
) -> UUID:
    """
    Get current user's organization ID.

    Args:
        current_user: Current user from JWT

    Returns:
        UUID: Organization ID

    Raises:
        HTTPException(403): If organization is missing
    """
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not associated with an organization",
        )

    return current_user.organization_id


async def require_role(required_role: str):
    """
    Create a dependency that requires a specific role.

    Args:
        required_role: Required role (e.g., 'admin', 'user')

    Returns:
        Dependency function for use with Depends()

    Example:
        @app.get("/admin", dependencies=[Depends(require_role("admin"))])
        async def admin_only():
            pass
    """

    async def check_role(current_user: CurrentUser = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {required_role}, got: {current_user.role}",
            )
        return current_user

    return check_role
