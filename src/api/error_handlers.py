"""Global error handlers for FastAPI application."""

import logging
from typing import Optional
from uuid import uuid4

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.api.schemas.quote_schemas import ErrorResponse

logger = logging.getLogger(__name__)


def create_error_response(
    code: str,
    message: str,
    details: Optional[dict] = None,
    request_id: Optional[str] = None,
    status_code: int = 500,
) -> JSONResponse:
    """
    Create standardized error response.

    Args:
        code: Error code (e.g., 'VALIDATION_ERROR')
        message: Human-readable message
        details: Additional error details
        request_id: Request ID for tracing
        status_code: HTTP status code

    Returns:
        JSONResponse: Formatted error response
    """
    error = ErrorResponse(
        code=code,
        message=message,
        details=details,
        request_id=request_id,
    )

    return JSONResponse(
        status_code=status_code,
        content=error.dict(exclude_none=True),
    )


def register_error_handlers(app: FastAPI) -> None:
    """
    Register global error handlers with FastAPI app.

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        """Handle Pydantic ValidationError (400 Bad Request)."""
        request_id = getattr(request.state, "request_id", str(uuid4()))

        # Extract field errors
        field_errors = {}
        for error in exc.errors():
            field_name = ".".join(str(x) for x in error["loc"][1:])
            field_errors[field_name] = error["msg"]

        logger.warning(
            f"[{request_id}] Validation error: {field_errors}",
            extra={"request_id": request_id},
        )

        return create_error_response(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details=field_errors,
            request_id=request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handle ValueError (400 Bad Request)."""
        request_id = getattr(request.state, "request_id", str(uuid4()))

        logger.warning(
            f"[{request_id}] Validation error: {str(exc)}",
            extra={"request_id": request_id},
        )

        return create_error_response(
            code="VALIDATION_ERROR",
            message="Invalid input",
            details={"error": str(exc)},
            request_id=request_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    @app.exception_handler(PermissionError)
    async def permission_error_handler(request: Request, exc: PermissionError):
        """Handle PermissionError (403 Forbidden)."""
        request_id = getattr(request.state, "request_id", str(uuid4()))

        logger.warning(
            f"[{request_id}] Permission denied: {str(exc)}",
            extra={"request_id": request_id},
        )

        return create_error_response(
            code="PERMISSION_DENIED",
            message="Access denied",
            details={"error": str(exc)},
            request_id=request_id,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    @app.exception_handler(KeyError)
    async def key_error_handler(request: Request, exc: KeyError):
        """Handle KeyError (404 Not Found)."""
        request_id = getattr(request.state, "request_id", str(uuid4()))

        logger.warning(
            f"[{request_id}] Not found: {str(exc)}",
            extra={"request_id": request_id},
        )

        return create_error_response(
            code="NOT_FOUND",
            message="Resource not found",
            request_id=request_id,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle all unhandled exceptions (500 Internal Server Error)."""
        request_id = getattr(request.state, "request_id", str(uuid4()))

        logger.error(
            f"[{request_id}] Unhandled exception: {type(exc).__name__}: {str(exc)}",
            exc_info=True,
            extra={"request_id": request_id},
        )

        return create_error_response(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            request_id=request_id,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
