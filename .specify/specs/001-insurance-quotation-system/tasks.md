---
description: "Task list for Lending Insurance Quotation System (Sistema de Cotação de Seguros Prestamistas)"
---

# Tasks: Lending Insurance Quotation System (Sistema de Cotação de Seguros Prestamistas)

**Input**: Design documents from `/specs/001-insurance-quotation-system/`  
**Prerequisites**: plan.md ✅, spec.md ✅, Confirmed tech stack: FastAPI + PostgreSQL + Redis  
**Generated**: 2026-03-30  
**Status**: 🟢 **READY FOR DEVELOPMENT** - All tasks are granular, executable, with pre-defined fixtures and explicit acceptance criteria

---

## Format & Legend

- **[ID]**: Task identifier (T001, T002, etc.) in execution order
- **[P]**: Parallelizable - different files, no dependencies on incomplete tasks
- **[Story]**: User story context (US1, US2, US3, US4) - REQUIRED for story implementation tasks
- **[SP]**: Story Points (1=30min, 2=1h, 3=2h, 5=half-day, 8=full-day)
- **File paths**: Absolute within src/ and tests/ directories

---

## Phase 0: Setup (Shared Infrastructure & Scaffolding)

**Purpose**: Project initialization, dependency setup, folder structure  
**Duration**: ~3-5 days  
**Checkpoint**: Project compiles, empty FastAPI server runs locally

### T001-T010: Project Structure & Dependencies

- [ ] **T001** Create project directory structure per plan.md
  - **Description**: Initialize folder structure: `src/{domain,application,infrastructure,api}`, `tests/{unit,integration,contract}`, `migrations/versions`, `docs/`, `config/`
  - **Files**: Create directories only (no code yet)
  - **Acceptance**: `ls -R` shows proper structure matching Clean Architecture layers
  - **Story Points**: 1

- [ ] **T002** [P] Initialize Python environment and FastAPI project
  - **Description**: Create `pyproject.toml` with dependencies: FastAPI 0.104+, SQLAlchemy 2.0+, Pydantic v2, psycopg[binary], redis, pytest, pytest-asyncio, python-dotenv, pyjwt
  - **Files**: Create `pyproject.toml`, `poetry.lock` or `requirements.txt`
  - **Acceptance**: `pip install -e .` succeeds, `python -c "import fastapi; print(fastapi.__version__)"` works
  - **Story Points**: 1

- [ ] **T003** [P] Setup project configuration management
  - **Description**: Create `config/settings.py` with Pydantic BaseSettings for environment variables (DATABASE_URL, REDIS_URL, JWT_SECRET, LOG_LEVEL, etc.)
  - **Files**: `src/config/settings.py`, `.env.example`
  - **Acceptance**: Can load configuration from `.env` file, all required fields validated
  - **Story Points**: 1

- [ ] **T004** [P] Initialize Git repository with proper .gitignore and README
  - **Description**: Setup `.gitignore` for Python/FastAPI, create `README.md` with project description and local setup instructions
  - **Files**: `.gitignore`, `README.md`
  - **Acceptance**: `git status` shows only tracked files, README documents build/run steps
  - **Story Points**: 1

- [ ] **T005** [P] Setup Docker and docker-compose for local development
  - **Description**: Create `Dockerfile` and `docker-compose.yml` for FastAPI app, PostgreSQL 14, Redis; enable local development without manual setup
  - **Files**: `Dockerfile`, `docker-compose.yml`, `.dockerignore`
  - **Acceptance**: `docker-compose up` starts app on port 8000, PostgreSQL on 5432, Redis on 6379; health checks pass
  - **Story Points**: 2

- [ ] **T006** [P] Initialize database migrations framework (Alembic)
  - **Description**: Setup Alembic for database schema versioning; create initial migration environment
  - **Files**: `migrations/env.py`, `migrations/script.py.mako`, `migrations/alembic.ini`
  - **Acceptance**: `alembic --version` works, migrations directory structure is initialized
  - **Story Points**: 1

- [ ] **T007** [P] Create database schema migrations (Phase 0)
  - **Description**: Define Alembic migration for Organizations, Users, Configurations, Quotes, and AuditLogs tables with all constraints per plan.md
  - **Files**: `migrations/versions/001_initial_schema.py` (create script, not upgrade yet to Phase 1)
  - **Includes**: Table creation with indexes, ENUM types (user_role, quote_status, audit_event_type), constraints
  - **Acceptance**: Migration script contains all SQL DDL from plan.md, syntax is valid
  - **Story Points**: 3

- [ ] **T008** [P] Setup logging and structured JSON output
  - **Description**: Create `src/infrastructure/logging.py` with JSON formatter for CloudWatch/ELK integration; configure root logger with request ID context
  - **Files**: `src/infrastructure/logging.py`, `src/api/middleware.py` (add request ID middleware placeholder)
  - **Acceptance**: Logs are JSON format, include request_id, timestamp, level, message
  - **Story Points**: 2

- [ ] **T009** [P] Setup testing infrastructure and pytest configuration
  - **Description**: Create `pytest.ini`, `conftest.py` with fixtures for dependency injection (db session, redis client, JWT tokens); enable async test support
  - **Files**: `pytest.ini`, `tests/conftest.py`
  - **Includes**: Database fixture (test DB), Redis fixture, shared test data builders
  - **Acceptance**: `pytest tests/ --collect-only` shows all tests discoverable
  - **Story Points**: 2

- [ ] **T010** [P] Create empty FastAPI main application file
  - **Description**: Create `src/api/main.py` with minimal FastAPI app, CORS middleware, request logging middleware, error handling middleware
  - **Files**: `src/api/main.py`
  - **Acceptance**: `uvicorn src.api.main:app --reload` starts server on port 8000; `curl http://localhost:8000/health` returns 200
  - **Story Points**: 1

---

**Checkpoint Phase 0**: ✅ Project structure initialized, dependencies installed, empty FastAPI app runs, migrations framework ready

---

## Phase 1: Foundational Infrastructure (Blocking Prerequisites)

**Purpose**: Core domain objects, database access layer, auth skeleton, API middleware  
**Duration**: ~5-7 days  
**⚠️ CRITICAL**: No user story work can begin until this phase completes  
**Checkpoint**: Domain entities testable, database migrations apply successfully, JWT framework in place

### T011-T020: Domain Model & Database Layer

- [ ] **T011** [P] Create Quote domain entity and value objects
  - **Description**: Define `src/domain/entities/quote.py` with Quote class (immutable after creation), MoneyAmount VO for currency calculations with 2-decimal precision, PaymentTerms VO for lump-sum and installment breakdown
  - **Files**: `src/domain/entities/quote.py`
  - **Includes**: __eq__, __hash__ for value objects, dataclass decoration, type hints
  - **Acceptance**: Can instantiate Quote with valid loan_value, rates; premium_amount, total_amount calculated correctly; all attributes immutable
  - **Story Points**: 2

- [ ] **T012** [P] Create Configuration domain entity
  - **Description**: Define `src/domain/entities/configuration.py` with Configuration class for rate management (premium_rate, brokerage_rate, effective_from, created_by, notes)
  - **Files**: `src/domain/entities/configuration.py`
  - **Includes**: Validation for rate ranges (premium: 0-1%, brokerage: 0-50%), immutability, temporal aspects
  - **Acceptance**: Can create Configuration with valid rates; invalid rates raise ValueError
  - **Story Points**: 1

- [ ] **T013** [P] Create Organization and User domain entities
  - **Description**: Define `src/domain/entities/organization.py` and `src/domain/entities/user.py` for multi-tenancy support
  - **Files**: `src/domain/entities/organization.py`, `src/domain/entities/user.py`
  - **Includes**: User roles (admin, operator, viewer, api_client), Organization with max_concurrent_requests
  - **Acceptance**: Can instantiate both entities with proper constraints; role validation works
  - **Story Points**: 2

- [ ] **T014** [P] Create AuditLog domain entity
  - **Description**: Define `src/domain/entities/audit_log.py` for compliance tracking of all mutations
  - **Files**: `src/domain/entities/audit_log.py`
  - **Includes**: event_type enum (quote_created, quote_archived, config_updated), entity tracking (entity_type, entity_id, changes JSON)
  - **Acceptance**: Can create AuditLog with change tracking; immutable after creation
  - **Story Points**: 1

- [ ] **T015** Create SQLAlchemy ORM models mapping domain entities
  - **Description**: Create `src/infrastructure/models.py` with SQLAlchemy declarative models for Quotes, Configurations, Organizations, Users, AuditLogs with relationship definitions
  - **Files**: `src/infrastructure/models.py`
  - **Includes**: Foreign keys, indexes per plan.md, column types (UUID, NUMERIC, JSONB, ENUM), composite keys if needed
  - **Acceptance**: Models defined match domain entities 1:1; `from src.infrastructure.models import *` works; SQLAlchemy can reflect schema
  - **Story Points**: 3

- [ ] **T016** [P] Create database connection and session management
  - **Description**: Create `src/infrastructure/database.py` with SQLAlchemy engine setup, session factory, async session context manager, connection pooling config (pool_size=20, max_overflow=10)
  - **Files**: `src/infrastructure/database.py`
  - **Includes**: get_db() dependency for FastAPI, transaction isolation level
  - **Acceptance**: Can create session, query tables (empty), close connection cleanly
  - **Story Points**: 2

- [ ] **T017** [P] Create database repository layer (base class)
  - **Description**: Create `src/infrastructure/repositories/base_repository.py` with abstract BaseRepository class defining CRUD interface (create, get_by_id, list, update, soft_delete)
  - **Files**: `src/infrastructure/repositories/base_repository.py`, `src/infrastructure/repositories/__init__.py`
  - **Includes**: Generic type hints, pagination support, filtering interface
  - **Acceptance**: Can subclass BaseRepository; abstract methods defined clearly
  - **Story Points**: 2

- [ ] **T018** [P] Create Quote repository implementation
  - **Description**: Create `src/infrastructure/repositories/quote_repository.py` with QuoteRepository(BaseRepository) for quotes (create, get_by_id, list_by_org, list_by_user, soft_delete, find_recent_for_org)
  - **Files**: `src/infrastructure/repositories/quote_repository.py`
  - **Includes**: Org-isolation enforced, pagination by created_at, filtering by status, date range, user
  - **Acceptance**: Can create, retrieve, archive quotes; queries include org_id WHERE clause always
  - **Story Points**: 3

- [ ] **T019** [P] Create Configuration repository implementation
  - **Description**: Create `src/infrastructure/repositories/configuration_repository.py` with ConfigurationRepository for rates (create, get_current_for_org, get_global_default, get_history_for_org)
  - **Files**: `src/infrastructure/repositories/configuration_repository.py`
  - **Includes**: "Current" = latest effective_from ≤ NOW(); history = all records paginated
  - **Acceptance**: Returns correct configuration for org vs global; history paginated correctly
  - **Story Points**: 2

- [ ] **T020** [P] Create Organization and User repository implementations
  - **Description**: Create `src/infrastructure/repositories/organization_repository.py` and `src/infrastructure/repositories/user_repository.py` for basic CRUD
  - **Files**: `src/infrastructure/repositories/organization_repository.py`, `src/infrastructure/repositories/user_repository.py`
  - **Includes**: User lookup by email (hashed password storage), org lookup by ID, list all active orgs/users
  - **Acceptance**: Can create/retrieve/list entities; email uniqueness enforced
  - **Story Points**: 2

### T021-T030: Authentication & Authorization Framework

- [ ] **T021** Create JWT token generation and validation service
  - **Description**: Create `src/application/services/token_service.py` with generate_access_token(), generate_refresh_token(), validate_token(), decode_token() using PyJWT
  - **Files**: `src/application/services/token_service.py`
  - **Includes**: Token payload includes user_id, org_id, role, exp (24h for access, 7d for refresh)
  - **Acceptance**: Can generate valid JWT with claims; can decode and validate; expired tokens rejected; tampered payload detected
  - **Story Points**: 2

- [ ] **T022** [P] Create password hashing utilities
  - **Description**: Create `src/infrastructure/security.py` with hash_password() and verify_password() using bcrypt
  - **Files**: `src/infrastructure/security.py`
  - **Includes**: Salt rounds = 12
  - **Acceptance**: Password hash not reversible; same plain text always produces different hashes (due to salt); verify works correctly
  - **Story Points**: 1

- [ ] **T023** [P] Create authentication dependency for FastAPI
  - **Description**: Create `src/api/dependencies.py` with get_current_user() dependency that validates JWT token, extracts user_id/org_id, fetches User entity from DB
  - **Files**: `src/api/dependencies.py`
  - **Includes**: Returns User object on success, raises HTTPException(401) on invalid token
  - **Acceptance**: Valid token returns User object; invalid/missing token raises 401; dependency injectable in route handlers
  - **Story Points**: 2

- [ ] **T024** [P] Create role-based authorization decorator
  - **Description**: Create `src/api/permissions.py` with require_role(*roles) decorator for route handlers; allows 'admin', 'operator', 'viewer', 'api_client'
  - **Files**: `src/api/permissions.py`
  - **Includes**: Raises HTTPException(403) if user role not in allowed list
  - **Acceptance**: Decorator applies to route handlers; correct roles allowed, others forbidden
  - **Story Points**: 1

- [ ] **T025** [P] Create auth/login endpoint and user creation service
  - **Description**: Create `src/api/routers/auth.py` with POST /auth/login endpoint; create `src/application/services/user_service.py` with authenticate_user(email, password) and create_user() methods
  - **Files**: `src/api/routers/auth.py`, `src/application/services/user_service.py`
  - **Includes**: Login returns access_token + refresh_token (200 OK); invalid credentials → 401
  - **Acceptance**: Valid credentials return tokens in correct format; invalid credentials return 401; swagger docs show endpoint
  - **Story Points**: 3

### T026-T030: Error Handling & Observability

- [ ] **T026** [P] Create custom exception classes and global error handler
  - **Description**: Create `src/domain/exceptions.py` with DomainException, ApplicationException, ValidationException; create `src/api/error_handlers.py` with FastAPI exception handlers
  - **Files**: `src/domain/exceptions.py`, `src/api/error_handlers.py`
  - **Includes**: Handlers convert exceptions to JSON with request_id, detail, validation_errors arrays
  - **Acceptance**: Can raise custom exceptions; they convert to proper HTTP response JSON
  - **Story Points**: 2

- [ ] **T027** [P] Create request/response logging middleware
  - **Description**: Create `src/api/middleware.py` with middleware that logs HTTP request/response with request_id, user_id, org_id, method, path, status_code, duration_ms
  - **Files**: `src/api/middleware.py`
  - **Includes**: Adds X-Request-ID header to response; logs in JSON format
  - **Acceptance**: Logs are structured JSON; can correlate requests by request_id
  - **Story Points**: 2

- [ ] **T028** [P] Create metrics collection for performance monitoring
  - **Description**: Create `src/infrastructure/metrics.py` with functions to track request latency (p50, p95, p99), error rate, cache hit rate
  - **Files**: `src/infrastructure/metrics.py`
  - **Includes**: Compatible with CloudWatch/Prometheus export
  - **Acceptance**: Can call track_latency(endpoint, latency_ms); can query p95 latency
  - **Story Points**: 2

- [ ] **T029** [P] Create circuit breaker for database resilience
  - **Description**: Create `src/infrastructure/circuit_breaker.py` with CircuitBreaker class for RDS connection; implements states: CLOSED (normal) → OPEN (failures) → HALF_OPEN (testing recovery)
  - **Files**: `src/infrastructure/circuit_breaker.py`
  - **Includes**: Failure threshold = 5 failures, timeout = 30 seconds before half-open
  - **Acceptance**: Can instantiate CB; can track failures; returns 503 when OPEN; recovers after timeout
  - **Story Points**: 2

- [ ] **T030** [P] Create cache layer with Redis (degradation support)
  - **Description**: Create `src/infrastructure/cache.py` with CacheClient class with get(), set(), delete(); graceful fallback if Redis unavailable
  - **Files**: `src/infrastructure/cache.py`
  - **Includes**: TTL support, supports fallback to None (no cache) on connection error
  - **Acceptance**: Can set/get values; returns None if Redis unavailable (no exception); logs warning
  - **Story Points**: 2

---

**Checkpoint Phase 1**: ✅ All domain entities, repos, and auth infrastructure in place and tested (≥80% coverage). ForeignKey relationships defined. Database migrations ready to apply. No business logic endpoints yet.

---

## Phase 2: User Story 1 - Quote Calculation & Creation (Priority P1) 🎯 MVP

**Goal**: Enable users to request insurance quotes with accurate premium, brokerage, and payment options instantly  
**Independent Test**: Provide loan amount → receive calculated quote with payment breakdowns  
**Duration**: ~5-7 days  
**MVP Foundation**: All downstream features depend on this working correctly

### Unit Tests for US1 (TDD - write FAILING tests first)

- [ ] **T031** [P] [US1] Unit test: Premium calculation formula verification
  - **Description**: Create `tests/unit/domain/test_premium_calculation.py` with test cases for formula: premium = loan_value × premium_rate
  - **Test Cases**:
    - loan_value=10000, premium_rate=0.0002 → premium=2.00 ✓
    - loan_value=50000, premium_rate=0.0002 → premium=10.00 ✓
    - loan_value=1, premium_rate=0.0002 → premium=0.00 (rounding) ✓
    - loan_value=-100 → ValueError ✓
  - **Acceptance**: All test cases defined; tests FAIL before implementation
  - **Story Points**: 1

- [ ] **T032** [P] [US1] Unit test: Brokerage calculation and total amount
  - **Description**: Create `tests/unit/domain/test_brokerage_calculation.py` with test cases for: brokerage = premium × (brokerage_rate / 100), total = premium + brokerage
  - **Test Cases**:
    - premium=2.00, brokerage_rate=5.00 → brokerage=0.10, total=2.10 ✓
    - premium=100.00, brokerage_rate=7.00 → brokerage=7.00, total=107.00 ✓
    - brokerage_rate=0 → brokerage=0, total=premium ✓
    - brokerage_rate=150 (invalid) → ValueError ✓
  - **Acceptance**: Test cases defined; tests FAIL before implementation
  - **Story Points**: 1

- [ ] **T033** [P] [US1] Unit test: Monthly payment calculation (12 installments)
  - **Description**: Create `tests/unit/domain/test_monthly_payment.py` verifying: monthly = total ÷ 12, banker's rounding to 2 decimals
  - **Test Cases**:
    - total=2.10 → monthly=0.18 (2.10/12 = 0.175 → 0.18 banker's rounding) ✓
    - total=105.00 → monthly=8.75 ✓
    - total=0.01 → monthly=0.00 ✓
    - total=99.99 → monthly=8.33 ✓
  - **Acceptance**: Banker's rounding tested; tests FAIL before implementation
  - **Story Points**: 1

- [ ] **T034** [P] [US1] Integration test: Quote creation end-to-end
  - **Description**: Create `tests/integration/test_quote_creation.py` testing full POST /quotes flow with mocked auth
  - **Test Cases**:
    - Valid loan_value (10000) + authenticated user → 201 Created with full quote details ✓
    - Invalid loan_value (<= 0) → 400 Bad Request ✓
    - Missing loan_value field → 400 Bad Request ✓
    - Unauthenticated request → 401 Unauthorized ✓
    - Under 100 concurrent requests → all succeed within 100ms ✓
  - **Acceptance**: Integration tests defined; tests FAIL before implementation
  - **Story Points**: 2

### Implementation for US1

- [ ] **T035** Create QuoteCalculator domain service
  - **Description**: Create `src/domain/services/quote_calculator.py` with QuoteCalculator class implementing premium/brokerage/total/monthly calculations; immutable, pure functions
  - **Methods**:
    - `calculate_premium(loan_value: Decimal, premium_rate: Decimal) → Decimal`
    - `calculate_brokerage(premium: Decimal, brokerage_rate: Decimal) → Decimal`
    - `calculate_total(premium: Decimal, brokerage: Decimal) → Decimal`
    - `calculate_monthly_payment(total: Decimal) → Decimal`
  - **Files**: `src/domain/services/quote_calculator.py`
  - **Includes**: Use decimal.Decimal for precision, ROUND_HALF_EVEN for banker's rounding, validation for rate ranges
  - **Acceptance**: Tests T031-T033 now PASS with ≥95% coverage
  - **Story Points**: 2

- [ ] **T036** Create CreateQuoteUseCase (application/business logic)
  - **Description**: Create `src/application/use_cases/create_quote.py` with CreateQuoteUseCase orchestrating: validate input → fetch org rates → calculate premium/brokerage → create Quote entity → persist via repository → create audit log → return response
  - **Files**: `src/application/use_cases/create_quote.py`
  - **Includes**: Dependency injection of calculator, quote_repo, config_repo, audit_repo; transaction handling
  - **Acceptance**: Use case can be invoked with LoanRequest DTO; returns QuoteResponse DTO
  - **Story Points**: 3

- [ ] **T037** Create Pydantic request/response schemas for quotes
  - **Description**: Create `src/api/schemas/quote_schemas.py` with CreateQuoteRequest (loan_value, metadata), QuoteResponse (all quote fields + payment_terms breakdown)
  - **Files**: `src/api/schemas/quote_schemas.py`
  - **Includes**: Validation (loan_value > 0), examples in docstring for Swagger
  - **Acceptance**: Schemas generate valid OpenAPI; request/response JSON validates
  - **Story Points**: 1

- [ ] **T038** [P] [US1] Implement POST /quotes endpoint
  - **Description**: Create `src/api/routers/quotes.py` with POST /quotes handler calling CreateQuoteUseCase, requiring JWT auth
  - **Files**: `src/api/routers/quotes.py`
  - **Includes**: @app.post("/quotes"), get_current_user dependency, error handling (400, 401, 403)
  - **Acceptance**: Integration test T034 now PASSES; Swagger shows endpoint with examples
  - **Story Points**: 2

- [ ] **T039** [P] [US1] Create test fixtures for quote testing
  - **Description**: Define `tests/fixtures.py` with reusable factories: create_test_org(), create_test_user(), create_test_quote(), create_test_config(), authenticated_client()
  - **Files**: `tests/fixtures.py`
  - **Includes**: Fixtures parametrizable for different loan values, rates, users
  - **Acceptance**: Can use `@pytest.fixture` to inject into test functions; factories create entities in test DB
  - **Story Points**: 2

- [ ] **T040** [P] [US1] Create test database seeding script
  - **Description**: Create `tests/seeds.py` with seed_test_data() populating test DB with: 1 global org, 2 test users (admin, operator), default config, 5 sample quotes
  - **Files**: `tests/seeds.py`
  - **Includes**: Called from conftest.py before each test session
  - **Acceptance**: Test DB has reproducible seed data; identical state across test runs
  - **Story Points**: 1

- [ ] **T041** [US1] Register quote router in main FastAPI app
  - **Description**: Update `src/api/main.py` to include quote router: `app.include_router(quotes_router, prefix="/api/v1", tags=["quotes"])`
  - **Files**: `src/api/main.py`
  - **Acceptance**: `GET /api/v1/docs` shows POST /quotes endpoint
  - **Story Points**: 1

---

**Checkpoint US1**: ✅ Quote calculation fully implemented and tested. MVP can accept quotes and calculate premiums. All tests T031-T034 PASS. Code coverage ≥80% for domain/application layers.

---

## Phase 3: User Story 2 - Quote Management (Priority P2)

**Goal**: Enable users to retrieve, list, filter, and soft-delete quotes for record-keeping and compliance  
**Independent Test**: Can create → list with filters → retrieve specific quote → archive it  
**Duration**: ~5-7 days  
**Depends On**: Phase 1 (foundational), Phase 2 (US1 quote creation)

### Unit Tests for US2 (TDD - write FAILING tests first)

- [ ] **T042** [P] [US2] Unit test: Quote repository list with pagination
  - **Description**: Create `tests/unit/infrastructure/test_quote_repository.py` with panitation tests
  - **Test Cases**:
    - Empty DB, list() → 0 results ✓
    - 100 quotes in DB, page=1, page_size=50 → 50 results + has_next=true ✓
    - page=2, page_size=50 → next 50 results ✓
    - page=3, page_size=50 → remaining 0 results + has_next=false ✓
  - **Acceptance**: Repository pagination tested; tests FAIL before implementation
  - **Story Points**: 1

- [ ] **T043** [P] [US2] Unit test: Quote filtering by date range and status
  - **Description**: Create `tests/unit/infrastructure/test_quote_filtering.py` verifying filter logic
  - **Test Cases**:
    - Filter by status='active' → returns only active quotes ✓
    - Filter by status='archived' → returns only archived quotes ✓
    - Filter by created_after='2026-03-01' → returns ≥ date ✓
    - Filter by created_before='2026-03-30' → returns ≤ date ✓
    - Combine filters → AND logic ✓
  - **Acceptance**: Tests FAIL before implementation
  - **Story Points**: 1

- [ ] **T044** [P] [US2] Unit test: Organization isolation in list/get operations
  - **Description**: Create `tests/unit/infrastructure/test_org_isolation.py` verifying user cannot access other org's quotes
  - **Test Cases**:
    - User A from Org1 lists quotes → sees only Org1's quotes ✓
    - User B from Org2 lists quotes → sees only Org2's quotes, not Org1's ✓
    - User A tries to GET quote from Org2 → ValueError or 403-level exception ✓
  - **Acceptance**: Tests FAIL before implementation
  - **Story Points**: 1

- [ ] **T045** [P] [US2] Integration test: List quotes with pagination + filtering
  - **Description**: Create `tests/integration/test_quote_list.py` testing GET /quotes endpoint
  - **Test Cases**:
    - No filters, page=1 → 50 results (default page_size) ✓
    - page=2 → next batch ✓
    - Filter by status=archived → 0 results (no archived quotes in seed) ✓
    - Filter by created_after=future date → 0 results ✓
    - Pagination info: pagination.total_count, has_next, has_previous ✓
    - Unauthenticated → 401 ✓
  - **Acceptance**: Integration tests FAIL before implementation
  - **Story Points**: 2

- [ ] **T046** [P] [US2] Integration test: Get specific quote by ID
  - **Description**: Create `tests/integration/test_quote_get.py` testing GET /quotes/{quote_id}
  - **Test Cases**:
    - GET existing quote → 200 OK with full details ✓
    - GET non-existent quote → 404 Not Found ✓
    - GET quote from different org → 403 Forbidden ✓
    - Unauthenticated → 401 ✓
  - **Acceptance**: Integration tests FAIL before implementation
  - **Story Points**: 1

- [ ] **T047** [P] [US2] Integration test: Delete (soft delete) quote
  - **Description**: Create `tests/integration/test_quote_delete.py` testing DELETE /quotes/{quote_id}
  - **Test Cases**:
    - DELETE existing active quote → 204 No Content ✓
    - Verify quote status is now 'archived' in DB ✓
    - Verify quote does NOT appear in list (default filters active only) ✓
    - DELETE already-archived quote → 404 ✓
    - DELETE quote from different org → 403 ✓
    - Insufficient role (viewer) → 403 ✓
  - **Acceptance**: Integration tests FAIL before implementation
  - **Story Points**: 2

### Implementation for US2

- [ ] **T048** Implement quote list (pagination + filtering) in repository
  - **Description**: Extend `src/infrastructure/repositories/quote_repository.py` with list_by_org(org_id, filters, page, page_size) method
  - **Filters**: status, created_after, created_before, loan_value_min, loan_value_max, sort_by, sort_order
  - **Files**: `src/infrastructure/repositories/quote_repository.py`
  - **Includes**: Always filter by org_id (isolation); pagination via LIMIT/OFFSET
  - **Acceptance**: Tests T042-T043 PASS
  - **Story Points**: 2

- [ ] **T049** [P] Implement GetQuoteUseCase
  - **Description**: Create `src/application/use_cases/get_quote.py` with use case to fetch single quote by ID + org_id validation
  - **Files**: `src/application/use_cases/get_quote.py`
  - **Acceptance**: Returns QuoteDTO or raises NotFoundError if quote doesn't exist or org_id mismatch
  - **Story Points**: 1

- [ ] **T050** [P] Implement ListQuotesUseCase
  - **Description**: Create `src/application/use_cases/list_quotes.py` accepting filter params, returning paginated list with total_count, has_next, has_previous
  - **Files**: `src/application/use_cases/list_quotes.py`
  - **Acceptance**: Returns paginated QuoteDTO list with metadata  
  - **Story Points**: 1

- [ ] **T051** [P] Implement ArchiveQuoteUseCase (soft delete)
  - **Description**: Create `src/application/use_cases/archive_quote.py` marking quote as archived + creating audit log entry
  - **Files**: `src/application/use_cases/archive_quote.py`
  - **Includes**: Audit logging with event_type='quote_archived'
  - **Acceptance**: Calls repository.soft_delete(); creates AuditLog
  - **Story Points**: 1

- [ ] **T052** Create Pydantic schemas for list/get/delete responses
  - **Description**: Extend `src/api/schemas/quote_schemas.py` with QuoteDetailResponse, PaginationMeta, QuoteListResponse
  - **Files**: `src/api/schemas/quote_schemas.py`
  - **Includes**: Pagination metadata structure matching OpenAPI spec
  - **Acceptance**: Swagger shows correct response schemas
  - **Story Points**: 1

- [ ] **T053** [P] [US2] Implement GET /quotes endpoint (list with filters)
  - **Description**: Add handler in `src/api/routers/quotes.py` for GET /quotes with query params (page, page_size, status, created_after, created_before, sort_by, sort_order)
  - **Files**: `src/api/routers/quotes.py`
  - **Includes**: Calls ListQuotesUseCase; enforces page_size ≤ 100; returns JSON with pagination info
  - **Acceptance**: Integration test T045 PASSES; Swagger shows endpoint with filter examples
  - **Story Points**: 2

- [ ] **T054** [P] [US2] Implement GET /quotes/{quote_id} endpoint
  - **Description**: Add handler in `src/api/routers/quotes.py` for GET /quotes/{quote_id}
  - **Files**: `src/api/routers/quotes.py`
  - **Includes**: Path parameter validation, calls GetQuoteUseCase
  - **Acceptance**: Integration test T046 PASSES
  - **Story Points**: 1

- [ ] **T055** [P] [US2] Implement DELETE /quotes/{quote_id} endpoint
  - **Description**: Add handler in `src/api/routers/quotes.py` for DELETE /quotes/{quote_id}; require 'operator' or 'admin' role
  - **Files**: `src/api/routers/quotes.py`
  - **Includes**: @require_role('operator', 'admin'), calls ArchiveQuoteUseCase
  - **Acceptance**: Integration test T047 PASSES; returns 204 No Content
  - **Story Points**: 1

- [ ] **T056** [P] [US2] Add comprehensive error handling for quote endpoints
  - **Description**: Add exception handlers for NotFoundError → 404, ForbiddenError → 403, ValidationError → 400 in quote routers
  - **Files**: `src/api/routers/quotes.py`, potentially update `src/api/error_handlers.py`
  - **Acceptance**: All error scenarios return correct HTTP status codes with descriptive JSON
  - **Story Points**: 1

- [ ] **T057** [US2] Create comprehensive integration test fixtures
  - **Description**: Extend `tests/fixtures.py` with factory for 50+ test quotes in various states, different users, date ranges
  - **Files**: `tests/fixtures.py`
  - **Acceptance**: Tests can use fixtures to create different quote scenarios
  - **Story Points**: 1

---

**Checkpoint US2**: ✅ Full quote CRUD (except UPDATE, which is intentionally not implemented) is functional. Tests T042-T047 PASS. Code coverage ≥85%. Users can manage quote history independently.

---

## Phase 4: User Story 3 - Configuration & Rate Management (Priority P2)

**Goal**: Enable administrators to update global and org-specific premium/brokerage rates without code changes; maintain audit trail  
**Independent Test**: Can read current rates → update rates → verify new quotes use new rates → check rate history  
**Duration**: ~5-7 days  
**Depends On**: Phase 1, Phase 2 (to verify new quotes use new rates)

### Unit Tests for US3 (TDD)

- [ ] **T058** [P] [US3] Unit test: Configuration validation (rate ranges)
  - **Description**: Create `tests/unit/domain/test_configuration_validation.py`
  - **Test Cases**:
    - premium_rate=0.0002 (0.02%) → Valid ✓
    - premium_rate=0.01 (1.0%) → Valid (boundary) ✓
    - premium_rate=0.011 (1.1%) → Invalid, ValueError ✓
    - premium_rate=-0.0001 → Invalid, ValueError ✓
    - brokerage_rate=5.00 (5%) → Valid ✓
    - brokerage_rate=50.00 (50%) → Valid (boundary) ✓
    - brokerage_rate=50.01 → Invalid, ValueError ✓
  - **Acceptance**: Tests FAIL before implementation
  - **Story Points**: 1

- [ ] **T059** [P] [US3] Unit test: Configuration repository - get current vs history
  - **Description**: Create `tests/unit/infrastructure/test_configuration_repository.py`
  - **Test Cases**:
    - 3 configs in DB (different effective_from dates), get_current() → returns latest (effective_from ≤ NOW()) ✓
    - get_history(limit=2) → returns last 2; older ones excluded ✓
    - New config with future effective_from (should not happen in MVP, but edge case) → get_current() ignores it ✓
  - **Acceptance**: Tests FAIL before implementation
  - **Story Points**: 1

- [ ] **T060** [P] [US3] Integration test: Update configuration endpoint
  - **Description**: Create `tests/integration/test_config_update.py`
  - **Test Cases**:
    - Admin user POSTs valid rates → 200 OK, returns new config ✓
    - New quotes immediately use new rates ✓
    - Operator user attempts update → 403 Forbidden ✓
    - Invalid rate (negative) → 400 Bad Request ✓
    - Unauthenticated → 401 ✓
  - **Acceptance**: Tests FAIL before implementation
  - **Story Points**: 2

- [ ] **T061** [P] [US3] Integration test: Read configuration endpoint
  - **Description**: Create `tests/integration/test_config_read.py`
  - **Test Cases**:
    - GET /admin/configurations → returns current global + org overrides ✓
    - Different org sees only own override (or global default if none) ✓
  - **Acceptance**: Tests FAIL before implementation
  - **Story Points**: 1

- [ ] **T062** [P] [US3] Integration test: Configuration history audit
  - **Description**: Create `tests/integration/test_config_history.py`
  - **Test Cases**:
    - GET /admin/configurations/history → returns all past configs paginated ✓
    - Each entry shows who made change (created_by_name), when, previous rates if available ✓
  - **Acceptance**: Tests FAIL before implementation
  - **Story Points**: 1

### Implementation for US3

- [ ] **T063** Create UpdateConfigurationUseCase
  - **Description**: Create `src/application/use_cases/update_configuration.py` orchestrating: validate new rates → fetch current config → create new entry with effective_from=NOW() → cache invalidation → create audit log
  - **Files**: `src/application/use_cases/update_configuration.py`
  - **Includes**: Org-level vs global default selection; audit logging
  - **Acceptance**: Returns new ConfigurationDTO; triggers cache reset
  - **Story Points**: 2

- [ ] **T064** [P] Create GetConfigurationUseCase
  - **Description**: Create `src/application/use_cases/get_configuration.py` to retrieve current rates (global default + org override if applicable); uses cache with fallback
  - **Files**: `src/application/use_cases/get_configuration.py`
  - **Includes**: Try cache first (Redis key: config:{org_id}), fallback to DB, fallback to hardcoded defaults
  - **Acceptance**: Returns ConfigurationDTO
  - **Story Points**: 1

- [ ] **T065** [P] Create GetConfigurationHistoryUseCase
  - **Description**: Create `src/application/use_cases/get_configuration_history.py` retrieving paginated history of configuration changes
  - **Files**: `src/application/use_cases/get_configuration_history.py`
  - **Includes**: For admin use, pagination support
  - **Acceptance**: Returns list of ConfigurationHistoryDTO with pagination metadata
  - **Story Points**: 1

- [ ] **T066** [P] Create cache invalidation service
  - **Description**: Create `src/infrastructure/cache_invalidation.py` with invalidate_config_cache(org_id) that clears Redis key for that org
  - **Files**: `src/infrastructure/cache_invalidation.py`
  - **Includes**: Called after every rate update
  - **Acceptance**: Cache cleared immediately; next query fetches from DB
  - **Story Points**: 1

- [ ] **T067** Create Pydantic schemas for configuration
  - **Description**: Create `src/api/schemas/configuration_schemas.py` with UpdateConfigurationRequest, ConfigurationResponse, ConfigurationHistoryResponse
  - **Files**: `src/api/schemas/configuration_schemas.py`
  - **Includes**: Validation annotations for rate ranges
  - **Acceptance**: Swagger shows correct schemas
  - **Story Points**: 1

- [ ] **T068** [P] [US3] Implement PUT /admin/configurations endpoint
  - **Description**: Add handler in new `src/api/routers/admin.py` for PUT /admin/configurations; require 'admin' role
  - **Files**: `src/api/routers/admin.py`
  - **Includes**: Input validation, calls UpdateConfigurationUseCase
  - **Acceptance**: Integration test T060 PASSES
  - **Story Points**: 2

- [ ] **T069** [P] [US3] Implement GET /admin/configurations endpoint
  - **Description**: Add handler in `src/api/routers/admin.py` for GET /admin/configurations
  - **Files**: `src/api/routers/admin.py`
  - **Includes**: Returns current rates (global and org override); visible to all authenticated users (read-only)
  - **Acceptance**: Integration test T061 PASSES
  - **Story Points**: 1

- [ ] **T070** [P] [US3] Implement GET /admin/configurations/history endpoint
  - **Description**: Add handler in `src/api/routers/admin.py` for GET /admin/configurations/history with pagination; require 'admin'
  - **Files**: `src/api/routers/admin.py`
  - **Includes**: Query params: limit, offset
  - **Acceptance**: Integration test T062 PASSES
  - **Story Points**: 1

- [ ] **T071** [US3] Register admin router in main app
  - **Description**: Update `src/api/main.py` to include admin router: `app.include_router(admin_router, prefix="/api/v1", tags=["admin"])`
  - **Files**: `src/api/main.py`
  - **Acceptance**: Swagger shows all /admin/* endpoints
  - **Story Points**: 1

- [ ] **T072** [P] [US3] Create test fixtures for configurations
  - **Description**: Extend `tests/fixtures.py` with create_test_config() factory; seed multiple configs with different rates/effective_from dates
  - **Files**: `tests/fixtures.py`
  - **Acceptance**: Tests can use config fixtures
  - **Story Points**: 1

---

**Checkpoint US3**: ✅ Configuration management fully operational. Admins can update rates without code. Rate history maintains audit trail. Cache layer working. Tests T058-T062 PASS. Code coverage ≥85%.

---

## Phase 5: User Story 4 - Production Hardening & Observability (Priority P3)

**Goal**: Prepare system for production: monitoring, rate limiting, documentation, performance optimization  
**Duration**: ~7-10 days  
**Depends On**: All previous phases complete and tested

### Observability & Monitoring

- [ ] **T073** [P] Implement request rate limiting (1000 req/min per user, 100 per IP)
  - **Description**: Create `src/infrastructure/rate_limiting.py` with RateLimiter class using Redis for tracking; integrate into middleware
  - **Files**: `src/infrastructure/rate_limiting.py`, update `src/api/middleware.py`
  - **Includes**: Raises HTTPException(429) when limit exceeded; includes Retry-After header
  - **Acceptance**: Can make 1000 requests/min as auth user, 101st returns 429; can make 100/min from IP, 101st returns 429
  - **Story Points**: 3

- [ ] **T074** [P] Add structured logging for all domain/application layer operations
  - **Description**: Instrument domain services and use cases with logging calls (DEBUG for calculation steps, INFO for mutations, ERROR for exceptions)
  - **Files**: `src/domain/services/*.py`, `src/application/use_cases/*.py`
  - **Includes**: JSON struct logs with context (user_id, org_id, quote_id, request_id)
  - **Acceptance**: Logs appear in JSON format with all context fields
  - **Story Points**: 2

- [ ] **T075** [P] Add performance metrics collection to all endpoints
  - **Description**: Create `src/api/instrumentation.py` with decorator @track_performance that records latency, error rate for each endpoint
  - **Files**: `src/api/instrumentation.py`
  - **Includes**: Metrics tracked: POST /quotes timing, GET /quotes list timing, etc.
  - **Acceptance**: Metrics recorded after each endpoint; can query latency for endpoints
  - **Story Points**: 2

- [ ] **T076** [P] Add database query performance monitoring
  - **Description**: Instrument SQLAlchemy with event listeners to track query execution time; log slow queries (>100ms) with WARN level
  - **Files**: `src/infrastructure/database.py`
  - **Includes**: Logs include SQL, parameters, execution_time_ms
  - **Acceptance**: Slow queries logged; can identify bottlenecks
  - **Story Points**: 2

- [ ] **T077** [P] Create CloudWatch integration and alarm definitions
  - **Description**: Create `src/infrastructure/cloudwatch.py` with functions to emit custom metrics (quote_created_count, avg_latency, error_rate); define alarm CloudFormation template in `infra/alarms.yaml`
  - **Files**: `src/infrastructure/cloudwatch.py`, `infra/alarms.yaml`
  - **Includes**: Alarms: p95 latency >150ms, error rate >1%, cache hit rate <80%
  - **Acceptance**: Custom metrics appear in CloudWatch dashboard
  - **Story Points**: 3

### API Documentation & Developer Experience

- [ ] **T078** Create comprehensive OpenAPI documentation
  - **Description**: Update FastAPI docstrings and add Swagger examples; generate/verify OpenAPI JSON at https://api.seguros.example.com/api/v1/openapi.json
  - **Files**: All route handlers in `src/api/routers/`
  - **Includes**: Request/response examples, error code definitions, authentication requirements
  - **Acceptance**: Swagger UI at /api/docs shows all endpoints with examples; OpenAPI JSON is valid
  - **Story Points**: 2

- [ ] **T079** [P] Create multi-language client code examples
  - **Description**: Create `docs/client_examples/` with example code: Python (requests), Node.js (fetch), PHP (cURL), Java (HttpClient)
  - **Files**: `docs/client_examples/{python,nodejs,php,java}_example.md`
  - **Includes**: Login, create quote, list quotes, error handling for each language
  - **Acceptance**: Examples compile/run successfully
  - **Story Points**: 3

- [ ] **T080** [P] Create deployment guide and architecture diagram
  - **Description**: Create `docs/DEPLOYMENT.md` covering: AWS infrastructure setup, environment variables, migrations, RDS setup, Redis setup; create `docs/architecture.md` with ASCII/Mermaid diagram
  - **Files**: `docs/DEPLOYMENT.md`, `docs/architecture.md`, potentially `infra/` CloudFormation or Terraform files (outline only)
  - **Acceptance**: Instructions clear enough for DevOps to deploy; architecture documented
  - **Story Points**: 3

- [ ] **T081** Create Quickstart guide for developers
  - **Description**: Create `docs/QUICKSTART.md` with: clone repo, install deps, docker-compose up, run migrations, seed test data, make first API call examples
  - **Files**: `docs/QUICKSTART.md`
  - **Includes**: Troubleshooting section
  - **Acceptance**: New developer can follow guide and make successful API calls within 10 minutes
  - **Story Points**: 2

- [ ] **T082** [P] Create API migration and versioning strategy document
  - **Description**: Create `docs/API_VERSIONING.md` documenting: current version (v1), how to handle breaking changes (new /v2), deprecation policy (12+ month transition)
  - **Files**: `docs/API_VERSIONING.md`
  - **Acceptance**: Strategy is clear and documented
  - **Story Points**: 1

### Performance Optimization

- [ ] **T083** Optimize quote list queries with indexed filtering
  - **Description**: Verify database indexes from plan.md are created on (organization_id, created_at DESC), (organization_id, user_id, created_at DESC); add query EXPLAIN plans to tests
  - **Files**: `migrations/versions/001_initial_schema.py` (indexes), `tests/performance/test_query_plans.py` (new)
  - **Includes**: Confirm index usage with EXPLAIN ANALYZE
  - **Acceptance**: List queries use indexes (no sequential scans on large tables)
  - **Story Points**: 2

- [ ] **T084** [P] Implement query result caching for rates
  - **Description**: Cache configuration lookup results in Redis with TTL=300s; already partially implemented in T030 (cache layer) and T066 (cache invalidation)
  - **Files**: `src/application/use_cases/get_configuration.py` (verify caching)
  - **Acceptance**: Repeated config lookups (GET /quotes) use cache; can observe cache hit rate >95%
  - **Story Points**: 1

- [ ] **T085** [P] Load test the API (locust or k6)
  - **Description**: Create `tests/load/load_test.py` (locust) or `tests/load/load_test.js` (k6) simulating: 100 concurrent users creating quotes + listing quotes + updating config over 5 minutes
  - **Files**: `tests/load/load_test.py` or `tests/load/load_test.js`
  - **Includes**: Success criteria: p95 latency <100ms (create), <500ms (list), zero errors
  - **Acceptance**: Load test runs; latency targets met
  - **Story Points**: 3

- [ ] **T086** Profile and optimize hot paths using cProfile or similar
  - **Description**: Profile quote creation endpoint under load; identify bottlenecks (DB calls, calculation, etc.); apply optimizations (batch inserts for audit logs if needed, query optimization)
  - **Files**: `profiling/profile_results.txt` (output only)
  - **Acceptance**: Profile shows no obvious bottlenecks; hot functions optimized
  - **Story Points**: 2

### Testing Coverage & Hardening

- [ ] **T087** [P] Achieve ≥80% unit test coverage on domain and application layers
  - **Description**: Run `pytest tests/unit/ --cov=src/domain --cov=src/application --cov-report=html` and ensure coverage ≥80%; fill gaps with additional unit tests
  - **Files**: Add missing `tests/unit/**/*.py` as needed
  - **Acceptance**: Coverage report shows ≥80% for domain/ and application/
  - **Story Points**: 3

- [ ] **T088** [P] Add contract tests for all API endpoints
  - **Description**: Create `tests/contract/` directory with Pact or similar tests verifying request/response schemas for all endpoints (POST/GET/DELETE /quotes, GET/PUT /admin/configurations)
  - **Files**: `tests/contract/test_*.py`
  - **Includes**: Consumer-driven contracts; can be used for API gateway validation
  - **Acceptance**: All endpoints have contract tests; contracts match OpenAPI spec
  - **Story Points**: 3

- [ ] **T089** Implement audit logging for all mutations (100% compliance requirement)
  - **Description**: Add audit logging calls to: all quote operations (create, archive), all config updates, all user login/logout (if login tracked)
  - **Files**: Update use cases in `src/application/use_cases/*.py` to call audit_repository.create_audit_log()
  - **Includes**: Audit log captures: event_type, entity_type, entity_id, changes (before/after JSON), user_id, org_id, ip_address, timestamp
  - **Acceptance**: Every mutation creates audit log entry; can review audit log for any entity
  - **Story Points**: 2

- [ ] **T090** [P] Add security hardening: input validation, SQL injection prevention
  - **Description**: Review all Pydantic models and SQL queries to ensure: parameterized queries (SQLAlchemy handles this), no string concatenation in ORM, request body size limits
  - **Files**: All route handlers and repositories
  - **Includes**: Add request body size limit (e.g., 1MB) at middleware level
  - **Acceptance**: No security vulnerabilities detected in code review
  - **Story Points**: 2

- [ ] **T091** [P] Add CORS configuration and security headers
  - **Description**: Configure CORS in FastAPI (allow origins from specify/*.md or configurable), add security headers (X-Content-Type-Options, X-Frame-Options, Strict-Transport-Security)
  - **Files**: `src/api/main.py`, potentially `src/api/middleware.py`
  - **Acceptance**: Headers present in all responses; CORS properly configured for development and production
  - **Story Points**: 1

- [ ] **T092** Create error recovery and retry strategies document
  - **Description**: Document: what happens if PostgreSQL is down (503 Service Unavailable), what happens if Redis is down (fallback to DB), retry logic for transient failures
  - **Files**: `docs/ERROR_HANDLING.md`
  - **Acceptance**: All failure scenarios documented
  - **Story Points**: 1

### Database & Migration Validation

- [ ] **T093** [P] Create Alembic migration for schema initialization (upgrade script)
  - **Description**: Implement upgrade() and downgrade() in `migrations/versions/001_initial_schema.py` to actually CREATE/DROP tables when running `alembic upgrade head`
  - **Files**: `migrations/versions/001_initial_schema.py`
  - **Includes**: All DDL for organizations, users, configurations, quotes, audit_logs
  - **Acceptance**: `alembic upgrade head` creates all tables; `alembic downgrade base` removes them; schema matches plan.md
  - **Story Points**: 2

- [ ] **T094** [P] Create migration rollback tests
  - **Description**: Create `tests/integration/test_migrations.py` that: applies migration, inserts test data, rolls back, verifies tables gone, applies again, verifies data intact
  - **Files**: `tests/integration/test_migrations.py`
  - **Acceptance**: Migration can be applied and rolled back cleanly
  - **Story Points**: 2

- [ ] **T095** [P] Backup/restore strategy documentation
  - **Description**: Create `docs/BACKUP_RESTORE.md` documenting: AWS RDS automated backups, point-in-time restore procedure, disaster recovery plan
  - **Files**: `docs/BACKUP_RESTORE.md`
  - **Acceptance**: Documentation clear for DevOps
  - **Story Points**: 1

### Deployment & CI/CD

- [ ] **T096** [P] Create GitHub Actions CI/CD workflow
  - **Description**: Create `.github/workflows/ci.yml` with steps: install deps → lint (flake8, black) → unit tests → integration tests → build Docker image → push to ECR
  - **Files**: `.github/workflows/ci.yml`
  - **Acceptance**: Workflow runs on every push; tests must pass before merge
  - **Story Points**: 2

- [ ] **T097** [P] Create GitHub Actions deployment workflow (blue-green)
  - **Description**: Create `.github/workflows/deploy.yml` with steps: pull from ECR → deploy to ECS (blue environment) → health checks → traffic switch (green) → monitor
  - **Files**: `.github/workflows/deploy.yml`
  - **Acceptance**: Deployment can be triggered manually; zero-downtime
  - **Story Points**: 3

- [ ] **T098** Create rolling deployment strategy and runbook
  - **Description**: Document the blue-green deployment process, rollback procedure, monitoring dashboard to watch during deployment
  - **Files**: `docs/DEPLOYMENT_RUNBOOK.md`
  - **Acceptance**: Clear steps for operator to execute deployment and rollback
  - **Story Points**: 1

---

**Checkpoint US4/Phase 5**: ✅ Production-ready system with comprehensive observability, documentation, and testing. Rate limiting enabled. Performance optimized. ≥80% test coverage achieved. All requirements met.

---

## Phase 6: Polish & Final Validation

**Purpose**: Final cleanup, code review, documentation completeness, validation against spec

- [ ] **T099** [P] Code review: domain and application layers for SOLID compliance
  - **Description**: Review src/domain/* and src/application/* for SRP (single responsibility), OCP (open/closed), LSP (Liskov), ISP (interface segregation), DIP (dependency inversion)
  - **Files**: All files in src/domain/ and src/application/
  - **Acceptance**: Code passes architectural review; no violations detected
  - **Story Points**: 2

- [ ] **T100** [P] Code review: infrastructure and API layers for security
  - **Description**: Review src/infrastructure/* and src/api/* for: SQL injection prevention, authentication enforcement, authorization checks, input validation
  - **Files**: All files in src/infrastructure/ and src/api/
  - **Acceptance**: Security review passed
  - **Story Points**: 2

- [ ] **T101** [P] Documentation completeness audit
  - **Description**: Verify: README.md ✓, QUICKSTART.md ✓, DEPLOYMENT.md ✓, API_VERSIONING.md ✓, BACKUP_RESTORE.md ✓, client examples for 4 languages ✓, architecture diagram ✓
  - **Files**: All docs in docs/ and README.md
  - **Acceptance**: Checklist complete; no TBD sections
  - **Story Points**: 1

- [ ] **T102** [P] Run quickstart.md end-to-end validation
  - **Description**: Fresh developer follows QUICKSTART.md on clean machine (or in fresh Docker container): clone → install → docker-compose up → migrations → seed → make successful API calls
  - **Files**: docs/QUICKSTART.md
  - **Acceptance**: All steps work without modification; no manual fixes required
  - **Story Points**: 1

- [ ] **T103** [P] Verify all acceptance criteria from spec.md are met
  - **Description**: For each user story (US1-US4) in spec.md, verify all acceptance scenarios pass:
    - US1: Quote calculation ✓ (T031-T034 passed)
    - US2: Quote management ✓ (T042-T047 passed)
    - US3: Rate config ✓ (T058-T062 passed)
    - US4: Production ready ✓ (T073-T091 passed)
  - **Files**: spec.md, checklist in .specify/specs/001-insurance-quotation-system/checklists/
  - **Acceptance**: All acceptance scenarios verified via integration tests
  - **Story Points**: 2

- [ ] **T104** Final API documentation review (Swagger/OpenAPI)
  - **Description**: Verify /api/docs shows all endpoints with: correct HTTP methods, request/response schemas, error codes, authentication requirements, examples
  - **Files**: All route handlers
  - **Acceptance**: Swagger UI complete and accurate; no 404 examples or missing schemas
  - **Story Points**: 1

- [ ] **T105** [P] Prepare release notes and CHANGELOG
  - **Description**: Document: features included (US1-US4), breaking changes (none for v1), migration notes for first deployment, known limitations
  - **Files**: `CHANGELOG.md`, `RELEASE_NOTES.md`
  - **Acceptance**: Release notes guide users on what's new and what to watch out for
  - **Story Points**: 1

---

**Checkpoint Phase 6**: ✅ **PRODUCTION READY**. All acceptance criteria met. Code quality verified. Documentation complete. System ready to deploy.

---

## Dependency Graph & Execution Strategy

```
Phase 0: Setup (T001-T010)
  ↓ (blocks all)
Phase 1: Foundational (T011-T030) [DB, Auth, Error Handling, Cache]
  ↓ (blocks all stories)
Phase 2: US1 (T031-T041) — Quote Calculation (INDEPENDENT)
Phase 3: US2 (T042-T057) — Quote CRUD (INDEPENDENT, can start after Phase 1)
Phase 4: US3 (T058-T072) — Rate Configuration (INDEPENDENT, can start after Phase 1)
Phase 5: US4 (T073-T098) — Production Hardening (can start after Phase 3/4 complete)
Phase 6: Polish (T099-T105) — Final validation (after all phases)
```

### Parallelization Examples

**After Phase 1 completes**:
- Developer A: Work on Phase 2 (US1 - Quote calculation)
- Developer B: Work on Phase 3 (US2 - Quote CRUD)
- Developer C: Work on Phase 4 (US3 - Configuration)

**Within each phase, parallelizable tasks** (marked [P]):
- T002, T003, T004, T005, T006, T008, T009 can run in parallel during Phase 0
- T012, T013, T014, T016, T017, T018, T019, T020 can run in parallel during Phase 1
- etc.

---

## Sprint Planning Recommendation

### Sprint 1 (Week 1-2): Foundation
- **T001-T010**: Setup (all Phase 0)
- **T011-T020**: Domain models + database layer (Phase 1)
- **Target**: Project structure, DB migrations, domain entities all working

### Sprint 2 (Week 2-3): Core Calculation
- **T021-T030**: Auth + error handling (Phase 1)
- **T031-T041**: Quote calculation + POST endpoint (Phase 2 US1)
- **Target**: MVP quote creation working; can calculate premiums

### Sprint 3 (Week 3-4): Quote Management
- **T042-T057**: Quote CRUD + list (Phase 3 US2)
- **Target**: Users can create, list, retrieve, delete quotes

### Sprint 4 (Week 4-5): Rate Configuration
- **T058-T072**: Configuration management (Phase 4 US3)
- **Target**: Admins can manage rates; history maintained

### Sprint 5 (Week 5-6): Observability & Hardening
- **T073-T098**: Monitoring, load testing, documentation (Phase 5 US4)
- **Target**: Production-ready; monitored; documented

### Sprint 6 (Week 6): Final Polish
- **T099-T105**: Code review, final validation
- **Target**: Ready to ship

---

## MVP Scope (Minimum Viable Product)

**Recommended MVP = Phases 0-3 (T001-T057)**:
- ✅ Project setup
- ✅ Authentication & database
- ✅ Quote calculation (US1)
- ✅ Quote CRUD (US2)
- ❌ Configuration management (defer to Phase 2 release)
- ❌ Production hardening (defer to Phase 2 release)

**Rationale**: MVP delivers core business value (instant quotes + management) in ~4-5 weeks with 3 developers. US3 and US4 can follow in Phase 2 after gathering user feedback.

*Alternative: Include Phase 4 (US3 Configuration) if "admin rate updates without code" is business-critical.*

---

## Test Data Fixtures & Seeds

### Pre-Defined Test Data (in `tests/seeds.py` and `tests/fixtures.py`)

**Organizations**:
```python
ORG_MAIN = Organization(
  org_id="550e8400-e29b-41d4-a716-446655440001",
  name="Org Main Test",
  active=True,
)
ORG_SECONDARY = Organization(
  org_id="550e8400-e29b-41d4-a716-446655440002",
  name="Org Secondary Test",
  active=True,
)
```

**Users**:
```python
ADMIN_USER = User(
  user_id="550e8400-e29b-41d4-a716-446655440050",
  org_id=ORG_MAIN.org_id,
  email="admin@test.com",
  full_name="Admin User",
  role='admin',
)
OPERATOR_USER = User(
  user_id="550e8400-e29b-41d4-a716-446655440051",
  org_id=ORG_MAIN.org_id,
  email="operator@test.com",
  full_name="Operator User",
  role='operator',
)
# ... more users
```

**Configurations**:
```python
GLOBAL_DEFAULT_CONFIG = Configuration(
  config_id="550e8400-e29b-41d4-a716-446655440100",
  organization_id=None,  # Global default
  premium_rate=Decimal("0.0002"),  # 0.02%
  brokerage_rate=Decimal("5.00"),  # 5%
  effective_from=datetime(2026, 1, 1),
)
```

**Sample Quotes** (50+ pre-created for list/filter testing):
```python
SAMPLE_QUOTES = [
  Quote(
    quote_id=...,
    org_id=ORG_MAIN.org_id,
    user_id=OPERATOR_USER.user_id,
    loan_value=Decimal("10000.00"),
    premium_rate=Decimal("0.0002"),
    premium_amount=Decimal("2.00"),
    brokerage_rate=Decimal("5.00"),
    brokerage_amount=Decimal("0.10"),
    total_amount=Decimal("2.10"),
    monthly_payment=Decimal("0.18"),
    status='active',
    created_at=<date>,
  ),
  # ... 49 more quotes with various amounts, dates, statuses
]
```

### JWT Test Tokens

Pre-generated valid JWT tokens for testing (in conftest.py fixtures):
```python
ADMIN_TOKEN = <JWT signed with test key, user_id=ADMIN_USER.id, org_id=ORG_MAIN.id, role='admin'>
OPERATOR_TOKEN = <JWT for OPERATOR_USER>
VIEWER_TOKEN = <JWT for viewer role>
EXPIRED_TOKEN = <JWT with exp in past>
INVALID_TOKEN = "invalid.signature.token"
```

---

## SQL Migrations Checklist

[x] **From `migrations/versions/001_initial_schema.py`**:
- [ ] Organizations table created
- [ ] Users table created + indexes on (org_id, role), (org_id, active)
- [ ] Configurations table created + unique constraints on (org_id) + indexes
- [ ] Quotes table created + all indexes (org_id, org+created_at, org+user+created_at,org+status)
- [ ] AuditLogs table created + indexes on (org_id, created_at), (user_id, created_at)
- [ ] Enum types defined (user_role, quote_status, audit_event_type)
- [ ] Foreign keys with ON DELETE constraints enforced
- [ ] Check constraints on rates and loan amounts

**Verification** (`alembic current` after upgrade):
```
alembic current
# Output: 001_initial_schema (head)

psql -h localhost -U user seguros_api -c "\dt"
# Should list: audit_logs, configurations, organizations, quotes, users
```

---

## API Contracts (OpenAPI 3.1.0) - Summary

| Endpoint | Method | Auth | Role | Implemented | Tested |
|----------|--------|------|------|-------------|--------|
| /auth/login | POST | No | - | T025 | ✓ |
| /quotes | POST | JWT | any | T038 | T034 ✓ |
| /quotes | GET | JWT | viewer+ | T053 | T045 ✓ |
| /quotes/{id} | GET | JWT | viewer+ | T054 | T046 ✓ |
| /quotes/{id} | DELETE | JWT | operator+ | T055 | T047 ✓ |
| /admin/configurations | GET | JWT | any | T069 | T061 ✓ |
| /admin/configurations | PUT | JWT | admin | T068 | T060 ✓ |
| /admin/configurations/history | GET | JWT | admin | T070 | T062 ✓ |

---

## Success Criteria Checklist

### Code Quality
- [x] ≥80% unit test coverage (domain + application)
- [ ] All endpoints have contract tests
- [ ] SOLID principles enforced (code review T099-T100)
- [ ] No SQL injection vulnerabilities
- [ ] No hardcoded secrets in source

### Performance
- [ ] Quote calculation <100ms (p95)
- [ ] Quote list <500ms (p95) with 1000 quotes
- [ ] Config lookup <50ms (cached)
- [ ] Handle 500+ concurrent users

### Functionality
- [ ] US1: Quote calculation + instant response ✓
- [ ] US2: Full quote CRUD with soft delete ✓
- [ ] US3: Admin rate management with history ✓
- [ ] US4: Production monitoring + documentation ✓

### Documentation
- [ ] README with setup instructions
- [ ] Quickstart guide (developers up & running in 10 min)
- [ ] API documentation (Swagger + client examples)
- [ ] Deployment guide + runbook
- [ ] Architecture diagram

### Deployment
- [ ] Alembic migrations working (up/down)
- [ ] Docker & docker-compose working
- [ ] GitHub Actions CI/CD passing
- [ ] Blue-green deployment strategy documented

---

**Generated**: 2026-03-30  
**Status**: 🟢 **READY FOR DEVELOPMENT**  
**Total Tasks**: 105  
**Estimated Duration**: 6 weeks (3 developers, parallel sprints)  
**MVP Completion**: ~4 weeks (Phases 0-3 only)
