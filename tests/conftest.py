"""Pytest configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.infrastructure.database.models import Base


# Database fixtures for unit tests (in-memory SQLite)
@pytest.fixture(scope="function")
def test_db_engine():
    """Create an in-memory SQLite database for unit tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def test_db_session(test_db_engine) -> Generator[Session, None, None]:
    """Provide a test database session (in-memory SQLite)."""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# Database fixtures for integration tests (PostgreSQL container)
@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async test database session (PostgreSQL)."""
    # This would connect to postgres:// in integration tests
    # For now, using SQLite async
    from sqlalchemy.ext.asyncio import AsyncSession as Session

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=Session, expire_on_commit=False
    )

    async with async_session() as session:
        yield session


# JWT token fixtures
@pytest.fixture
def jwt_token() -> str:
    """Provide a test JWT token."""
    # Simplified: In production, this would use proper JWT signing
    import jwt
    from datetime import datetime, timedelta

    secret = "test-secret-key-min-32-characters-long"
    payload = {
        "sub": str(uuid4()),
        "user_id": str(uuid4()),
        "organization_id": str(uuid4()),
        "exp": datetime.utcnow() + timedelta(hours=24),
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token


# Request/Response fixtures
@pytest.fixture
def sample_quote_payload() -> dict:
    """Provide sample quote creation payload."""
    return {
        "loan_value": 100000.00,
        "premium_rate": 0.045,
        "brokerage_rate": 0.15,
    }


@pytest.fixture
def sample_configuration_payload() -> dict:
    """Provide sample configuration payload."""
    from datetime import datetime

    return {
        "premium_rate": 0.045,
        "brokerage_rate": 0.15,
        "effective_from": datetime.utcnow().isoformat(),
    }


# Parametrized fixtures for edge cases
@pytest.fixture(
    params=[
        0.01,  # Minimum rate
        0.5,   # Medium rate
        0.999, # Maximum rate
    ]
)
def rate_values(request):
    """Parametrized fixture for testing different rate values."""
    return request.param


@pytest.fixture(
    params=[
        1000.00,      # Minimum loan
        100000.00,    # Standard loan
        1000000.00,   # Large loan
    ]
)
def loan_values(request):
    """Parametrized fixture for testing different loan values."""
    return request.param


# Markers for test categorization
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit test (no external deps)")
    config.addinivalue_line("markers", "integration: Integration test")
    config.addinivalue_line("markers", "slow: Slow test (>1s)")
