"""Main FastAPI application entry point."""

import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import get_settings
from src.api.error_handlers import register_error_handlers
from src.api.routes.quotes import router as quotes_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Lending Insurance Quotation System API - Calculate premium, brokerage, and installments for lending insurance products",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    contact={
        "name": "API Support",
        "url": "https://github.com/seguros-api",
        "email": "support@seguros.example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom middleware for request ID and logging
@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    """Add request ID and log all requests."""
    request_id = str(uuid4())
    request.state.request_id = request_id

    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000  # Convert to ms

    logger.info(
        f"[{request_id}] {request.method} {request.url.path} - "
        f"Status: {response.status_code} - Time: {process_time:.2f}ms"
    )

    response.headers["X-Request-ID"] = request_id

    return response


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancers."""
    return {
        "status": "ok",
        "version": settings.api_version,
        "environment": settings.environment,
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Lending Insurance Quotation System API",
        "version": settings.api_version,
        "docs": "/api/docs",
    }


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        f"[{request_id}] Unhandled exception: {type(exc).__name__}: {str(exc)}",
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "request_id": request_id,
        },
    )


# Startup and shutdown events
@app.on_event("startup")
async def startup():
    """Application startup event."""
    logger.info(f"Starting {settings.api_title} v{settings.api_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database: {settings.database_url}")


# Register error handlers
register_error_handlers(app)

# Include routers with API version prefix
app.include_router(
    quotes_router,
    prefix="/api/v1",
    tags=["Quotes"],
)


@app.on_event("shutdown")
async def shutdown():
    """Application shutdown event."""
    logger.info("Shutting down application")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        reload=(settings.environment == "development"),
    )
