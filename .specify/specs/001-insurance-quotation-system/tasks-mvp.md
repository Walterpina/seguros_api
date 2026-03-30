# TASKS-MVP: Lending Insurance Quotation System

**Assessment MVP** | ~35 tasks | ~17-23 hours (1-2 days, 1 developer)  
**Focus**: 5 Evaluation Criteria - Architecture, Security, Code Quality, Test Coverage, Documentation

---

## 📋 Task Legend

- **[P0]**: Phase/milestone constraint  
- **[P]**: Parallelizable (different files, no dependencies)  
- **[ARCH]**: Contributes to Architecture Vision  
- **[SEC]**: Contributes to Security  
- **[CODE]**: Contributes to Code Quality  
- **[TEST]**: Contributes to Test Coverage  
- **[DOC]**: Contributes to Documentation  
- **SP**: Story Points (1=quick, 2=normal, 3=complex)

---

## Phase 0: Setup & Infrastructure (8 tasks)

**Goal**: Establish foundational environment, Docker, database, project structure.

### Acceptance Tests (Phase 0)
- ✅ `docker-compose up` starts all services without errors
- ✅ Database initialized with schema
- ✅ `python -m src.api.main` starts FastAPI app on localhost:8000
- ✅ `pytest tests/` runs without import errors

---

- [ ] **T001** [P0] Create project structure (src/, tests/, config/)
  - **Description**: Establish Python package structure following Clean Architecture principles (domain, application, infrastructure, api layers)
  - **Files**: 
    - `src/__init__.py`
    - `src/domain/__init__.py`, `src/domain/entities/__init__.py`
    - `src/application/__init__.py`, `src/application/services/__init__.py`, `src/application/dtos/__init__.py`
    - `src/infrastructure/__init__.py`, `src/infrastructure/database/__init__.py`, `src/infrastructure/repositories/__init__.py`
    - `src/api/__init__.py`, `src/api/routes/__init__.py`, `src/api/security/__init__.py`, `src/api/schemas/__init__.py`
    - `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py`
    - `config/__init__.py`
  - **Acceptance**: Directory tree matches spec, all `__init__.py` files created, importable via `python -c "import src.domain"`
  - **SP**: 1 | **Dependencies**: None
  - **Tags**: [ARCH] [CODE]

---

- [ ] **T002** [P0] Setup environment variables & configuration management
  - **Description**: Create `.env.example`, `config/settings.py` with Pydantic BaseSettings for database URL, JWT secret, log level, rate limits
  - **Files**: 
    - `.env.example`
    - `config/settings.py` (DATABASE_URL, JWT_SECRET_KEY, JWT_ALGORITHM, LOG_LEVEL, PREMIUM_RATE, BROKERAGE_RATE)
    - `config/__init__.py`
  - **Acceptance**: 
    - `config.settings.DATABASE_URL` loads from env or .env file
    - Missing JWT_SECRET_KEY raises ValidationError with helpful message
    - `.env.example` is complete and documented
  - **SP**: 1 | **Dependencies**: T001
  - **Tags**: [CONFIG] [CODE]

---

- [ ] **T003** [P] [P0] Setup Docker & docker-compose (PostgreSQL + Redis)
  - **Description**: Create `docker-compose.yml` with PostgreSQL 14, Redis 7, and volume persistence. Add `Dockerfile` for FastAPI app.
  - **Files**: 
    - `docker-compose.yml` (postgres, redis services)
    - `Dockerfile` (Python 3.9+, FastAPI)
    - `.dockerignore`
  - **Acceptance**: 
    - `docker-compose up` starts 2 healthy containers
    - `docker-compose logs postgres` shows "ready to accept connections"
    - Redis responds to `redis-cli PING` locally
    - `docker-compose down` cleans up volumes (use named volumes)
  - **SP**: 2 | **Dependencies**: T001, T002
  - **Tags**: [ARCH] [INFRA]

---

- [ ] **T004** [P] [P0] Initialize PostgreSQL schema with migrations (Alembic)
  - **Description**: Setup Alembic for database migrations. Create initial migration with Quote and Configuration tables.
  - **Files**: 
    - `alembic/` directory structure
    - `alembic/env.py` (configured for auto-migration with models)
    - `alembic/versions/001_initial_schema.py` (Quote, Configuration tables)
    - `setup.cfg` or `alembic.ini` with sqlalchemy.url template
  - **Acceptance**: 
    - `alembic upgrade head` runs without errors against docker postgres
    - `psql -c "\\dt"` shows `quotes` and `configurations` tables
    - Can rollback via `alembic downgrade -1` and reapply
    - Migration is version-controlled and repeatable
  - **SP**: 2 | **Dependencies**: T003
  - **Tags**: [ARCH] [CODE]

---

- [ ] **T005** [P] [P0] Create SQLAlchemy ORM models (Quote, Configuration)
  - **Description**: Define SQLAlchemy 2.0 models with type hints, relationships, and indexes aligned to spec.
  - **Files**: 
    - `src/infrastructure/database/models.py` (Quote, Configuration models)
    - `src/infrastructure/database/__init__.py`
  - **Files** should include:
    - Quote: id (UUID), organization_id, user_id, loan_value, premium_rate, premium_amount, brokerage_rate, brokerage_amount, total_amount, monthly_payment, created_at, status (archived/active)
    - Configuration: id (UUID), organization_id (nullable), premium_rate, brokerage_rate, effective_from, created_by (user_id), created_at
    - Indexes on (organization_id, user_id, created_at, status)
  - **Acceptance**: 
    - Models have all required fields with correct types (UUID, Decimal, DateTime, etc.)
    - Relationships defined (organization → quotes, configuration)
    - All fields have proper constraints (nullable, defaults, checks)
    - Type hints present on all attributes
    - Can instantiate model: `Quote(organization_id=..., loan_value=...)`
  - **SP**: 2 | **Dependencies**: T004
  - **Tags**: [ARCH] [CODE]

---

- [ ] **T006** [P0] Setup pytest, fixtures, and test database (PostgreSQL container)
  - **Description**: Configure `pytest.ini`, `conftest.py` with database fixtures, in-memory SQLite for unit tests, PostgreSQL for integration tests.
  - **Files**: 
    - `pytest.ini` (minversion, testpaths, markers)
    - `tests/conftest.py` (fixtures: db_session, test_db, async_client, jwt_token)
    - `tests/test_config.py` (test database connection)
  - **Acceptance**: 
    - `pytest tests/unit/` runs with SQLite in-memory db
    - `pytest tests/integration/` runs against docker postgres
    - `pytest --cov=src --cov-report=term-missing` shows coverage % on stdout
    - Fixtures auto-cleanup (rollback transactions after each test)
    - `pytest -v` shows all test names without running (collection only)
  - **SP**: 2 | **Dependencies**: T005
  - **Tags**: [TEST] [CODE]

---

- [ ] **T007** [P0] Setup FastAPI app skeleton (main.py, middleware, CORS)
  - **Description**: Create `src/api/main.py` with FastAPI instance, middleware (CORS, logging, error handling), health check endpoint.
  - **Files**: 
    - `src/api/main.py` (app = FastAPI(...), include routers, middleware)
    - `src/api/middleware.py` (RequestID, logging, error handlers)
  - **Acceptance**: 
    - `uvicorn src.api.main:app --reload` starts on http://localhost:8000
    - `GET /health` returns `{"status": "ok"}`
    - `GET /api/docs` loads Swagger UI without errors
    - Middleware logs all requests to stdout (method, path, status, time_ms)
    - CORS configured to allow localhost:3000 (React frontend)
  - **SP**: 2 | **Dependencies**: T002, T003
  - **Tags**: [ARCH] [API]

---

## Phase 1: Core Domain & Application (10 tasks)

**Goal**: Implement quote calculation engine, business logic, and services isolated from infrastructure.

### Acceptance Tests (Phase 1)
- ✅ Quote calculation returns correct premium, brokerage, total
- ✅ Premium calculation: `loan_value * premium_rate`
- ✅ Brokerage calculation: `premium_amount * brokerage_rate`
- ✅ Monthly installment: `total / 12` (banker's rounding)
- ✅ Services can be instantiated and tested independently

---

- [ ] **T008** [P] [US1] Create Quote domain entity with value objects
  - **Description**: Define `src/domain/entities/quote.py` with Quote class, value objects (Money, Rate), equality/hashing, and immutable design.
  - **Files**: 
    - `src/domain/entities/quote.py` (Quote class with __init__, properties, immutability checks)
    - `src/domain/entities/value_objects.py` (Money, Rate, PaymentSchedule)
  - **Acceptance**: 
    - Quote instantiation: `Quote(loan_value=10000.0, premium_rate=0.0002, brokerage_rate=0.05)`
    - Premium calculated on init: `quote.premium_amount == 2.0`
    - Brokerage calculated: `quote.brokerage_amount == 0.10`
    - Total: `quote.total_amount == 2.10`
    - Monthly: `quote.monthly_payment ≈ 0.175` (rounded to 2 decimals)
    - All prices are Decimal (not float) for precision
    - Entity is iterable for inspection (str representation shows all fields)
  - **SP**: 3 | **Dependencies**: T001
  - **Tags**: [ARCH] [CODE] [DOMAIN]

---

- [ ] **T009** [P] [US1] Implement QuoteCalculationService (business logic)
  - **Description**: Create `src/application/services/quote_service.py` with pure business logic for quote calculation, validation, and payment schedule generation.
  - **Files**: 
    - `src/application/services/quote_service.py` (QuoteCalculationService class)
  - **Methods**:
    - `calculate_premium(loan_value: Decimal, premium_rate: Decimal) → Decimal`
    - `calculate_brokerage(premium_amount: Decimal, brokerage_rate: Decimal) → Decimal`
    - `calculate_total(premium_amount: Decimal, brokerage_amount: Decimal) → Decimal`
    - `calculate_monthly_payment(total_amount: Decimal, num_months: int = 12) → Decimal`
    - `generate_payment_schedule(total_amount: Decimal, num_months: int = 12) → List[MonthlyPayment]`
    - `validate_quote_input(loan_value: Decimal, premium_rate: Decimal, brokerage_rate: Decimal) → ValidationResult`
  - **Acceptance**: 
    - Service has zero dependencies (no DB, no HTTP)
    - All calculations use Decimal for precision
    - Validation errors are clear: "loan_value must be > 0"
    - Payment schedule has 12 installments, each ≈ total/12
    - Last installment may differ by 1 centavo due to rounding
    - 100% unit test coverage
  - **SP**: 3 | **Dependencies**: T008
  - **Tags**: [CODE] [DOMAIN] [TEST]

---

- [ ] **T010** [P] [US1] Create configuration service (rate management)
  - **Description**: Create `src/application/services/configuration_service.py` to load/validate premium and brokerage rates with fallback to defaults.
  - **Files**: 
    - `src/application/services/configuration_service.py` (ConfigurationService class)
  - **Methods**:
    - `get_current_rates(organization_id: UUID = None) → CurrentRates`
    - `validate_rates(premium_rate: Decimal, brokerage_rate: Decimal) → bool`
    - `load_from_env() → CurrentRates` (fallback for MVP)
  - **Acceptance**: 
    - `service.get_current_rates()` returns global rates (0.0002, 0.05) by default
    - `service.get_current_rates(org_uuid)` returns org-specific rates if exists, else global
    - `service.validate_rates(0.025, 0.10)` returns True
    - `service.validate_rates(-0.01, 0.05)` raises ValueError("premium_rate cannot be negative")
    - Rates loaded from config.settings if not in DB (MVP phase)
  - **SP**: 2 | **Dependencies**: T002, T009
  - **Tags**: [CODE] [DOMAIN]

---

- [ ] **T011** [P] [US1] Create QuoteRepository interface (Repository pattern)
  - **Description**: Define `src/infrastructure/repositories/quote_repository.py` with abstract interface (create, get, list, delete, update_status).
  - **Files**: 
    - `src/infrastructure/repositories/quote_repository.py` (QuoteRepository ABC)
    - `src/infrastructure/repositories/sql_quote_repository.py` (SQLAlchemy implementation)
  - **Acceptance**: 
    - Abstract class with @abstractmethod decorators
    - `create(quote_entity: Quote, user_id: UUID, org_id: UUID) → Quote` (persists and returns with quote_id)
    - `get(quote_id: UUID) → Quote | None`
    - `list(org_id: UUID, user_id: UUID, limit: int = 50, offset: int = 0) → List[Quote]`
    - `delete(quote_id: UUID) → bool` (soft delete - sets status='archived')
    - SQL implementation uses SQLAlchemy ORM, handles transactions
  - **SP**: 3 | **Dependencies**: T005, T011
  - **Tags**: [ARCH] [CODE]

---

- [ ] **T012** [P] [US2] Create Quote ApplicationDTO and mappers
  - **Description**: Create `src/application/dtos/quote_dto.py` with request/response DTOs, mapper functions (domain ↔ dto ↔ orm).
  - **Files**: 
    - `src/application/dtos/quote_dto.py` (QuoteCreateRequest, QuoteResponse, QuoteListResponse)
    - `src/application/dtos/mappers.py` (quote_entity_to_response, orm_to_entity, etc.)
  - **DTOs**:
    - `QuoteCreateRequest`: loan_value (required, > 0)
    - `QuoteResponse`: quote_id, loan_value, premium_amount, brokerage_amount, total_amount, monthly_payment, created_at, status
    - `QuoteListResponse`: items: List[QuoteResponse], total: int, page: int, limit: int
  - **Acceptance**: 
    - Pydantic models with validation
    - `QuoteCreateRequest(loan_value=-100)` raises ValidationError
    - Mappers are pure functions (no side effects)
    - `quote_entity_to_response(entity)` includes all required fields
  - **SP**: 2 | **Dependencies**: T009
  - **Tags**: [CODE] [API]

---

- [ ] **T013** [P] [US1+US2] Create use-case/application services (Command handlers)
  - **Description**: Create `src/application/use_cases/` with CreateQuoteUseCase, ListQuotesUseCase, GetQuoteUseCase, DeleteQuoteUseCase (orchestrate domain + repos).
  - **Files**: 
    - `src/application/use_cases/__init__.py`
    - `src/application/use_cases/create_quote.py` (CreateQuoteUseCase)
    - `src/application/use_cases/list_quotes.py` (ListQuotesUseCase)
    - `src/application/use_cases/get_quote.py` (GetQuoteUseCase)
    - `src/application/use_cases/delete_quote.py` (DeleteQuoteUseCase)
  - **Acceptance**: 
    - `CreateQuoteUseCase(repo=..., calc_service=..., config_service=...).execute(QuoteCreateRequest(...))`
    - Returns QuoteResponse with calculated values
    - ListQuotesUseCase returns paginated results
    - GetQuoteUseCase enforces user/org isolation (raises PermissionError)
    - DeleteQuoteUseCase soft-deletes (status='archived')
    - All use cases injectable (dependencies via __init__)
  - **SP**: 3 | **Dependencies**: T009, T010, T011, T012
  - **Tags**: [ARCH] [CODE]

---

- [ ] **T014** [P] [US1] Create unit tests for Quote entity
  - **Description**: Write `tests/unit/test_quote_entity.py` with 100% coverage for Quote instantiation, calculations, edge cases.
  - **Files**: 
    - `tests/unit/test_quote_entity.py` (test_creation, test_premium_calculation, test_edge_cases, etc.)
  - **Test Cases**:
    - Valid instantiation with positive loan_value
    - Zero loan_value raises ValueError
    - Negative loan_value raises ValueError
    - Premium calculation: 10000 * 0.0002 = 2.0
    - Brokerage: 2.0 * 0.05 = 0.10
    - Total: 2.10
    - Monthly: 2.10 / 12 ≈ 0.175
    - Large loan value (R$10M) precision preserved
    - Decimal precision (no float rounding errors)
  - **Acceptance**: 
    - `pytest tests/unit/test_quote_entity.py -v` shows all tests passing
    - `pytest tests/unit/test_quote_entity.py --cov=src.domain.entities.quote` shows 100% coverage
  - **SP**: 2 | **Dependencies**: T008, T006
  - **Tags**: [TEST] [CODE]

---

- [ ] **T015** [P] [US1] Create unit tests for QuoteCalculationService
  - **Description**: Write `tests/unit/test_quote_service.py` with comprehensive coverage for calculate methods, validation, payment schedules.
  - **Files**: 
    - `tests/unit/test_quote_service.py`
  - **Test Cases**:
    - `test_calculate_premium`
    - `test_calculate_brokerage`
    - `test_calculate_total`
    - `test_calculate_monthly_payment` (with last installment edge case)
    - `test_validate_quote_input` (valid, negative, zero, non-numeric)
    - `test_generate_payment_schedule` (12 items, sum = total, each ≈ total/12)
  - **Acceptance**: 
    - `pytest tests/unit/test_quote_service.py -v` all pass
    - `pytest --cov=src.application.services.quote_service` shows ≥95% coverage
  - **SP**: 2 | **Dependencies**: T009, T006
  - **Tags**: [TEST] [CODE]

---

- [ ] **T016** [P] [US1] Create unit tests for ConfigurationService
  - **Description**: Write `tests/unit/test_configuration_service.py` testing rate loading, validation, fallback logic.
  - **Files**: 
    - `tests/unit/test_configuration_service.py`
  - **Test Cases**:
    - `test_get_current_rates_default` (from env)
    - `test_get_current_rates_org_specific` (mock DB/repository lookup)
    - `test_validate_rates_valid`
    - `test_validate_rates_negative_premium` (raises)
    - `test_validate_rates_too_high_brokerage` (raises if > 50%)
    - `test_load_from_env`
  - **Acceptance**: 
    - All tests pass with mocked dependencies
    - `pytest --cov=src.application.services.configuration_service` ≥90% coverage
  - **SP**: 2 | **Dependencies**: T010, T006
  - **Tags**: [TEST] [CODE]

---

## Phase 2: API & Security (9 tasks)

**Goal**: Implement FastAPI endpoints, JWT authentication, input validation, error handling.

### Acceptance Tests (Phase 2)
- ✅ POST /api/v1/quotes creates quote, returns 201 with quote_id
- ✅ GET /api/v1/quotes lists quotes with pagination
- ✅ GET /api/v1/quotes/{id} retrieves specific quote
- ✅ DELETE /api/v1/quotes/{id} soft-deletes quote (returns 204)
- ✅ Missing JWT token returns 401
- ✅ Expired JWT token returns 401
- ✅ Invalid input returns 400 with validation error details
- ✅ All endpoints return proper content-type and status codes

---

- [ ] **T017** [P0] [SEC] Implement JWT authentication & token generation
  - **Description**: Create `src/api/security/jwt_handler.py` with JWT encode/decode, token validation, role extraction.
  - **Files**: 
    - `src/api/security/jwt_handler.py` (JWTHandler class)
    - `src/api/security/schemas.py` (TokenPayload, User schemas)
  - **Methods**:
    - `create_token(user_id: UUID, org_id: UUID, role: str, expires_delta: timedelta = 24h) → str`
    - `verify_token(token: str) → TokenPayload` (raises InvalidTokenError)
    - `decode_token(token: str) → dict`
  - **Acceptance**: 
    - Token created with exp, user_id, org_id, role claims
    - Token expires after configured duration (default 24h)
    - Expired token raises InvalidTokenError
    - Invalid signature raises InvalidTokenError
    - Use JWT_SECRET_KEY from config.settings
    - Algorithm: HS256
  - **SP**: 2 | **Dependencies**: T002, T007
  - **Tags**: [SEC] [CODE]

---

- [ ] **T018** [P] [SEC] Create FastAPI dependency for JWT verification
  - **Description**: Create `src/api/security/dependencies.py` with get_current_user, get_current_org FastAPI Depends for route protection.
  - **Files**: 
    - `src/api/security/dependencies.py`
  - **Acceptance**: 
    - `@app.get("/protected", dependencies=[Depends(get_current_user)])`
    - Extracts Bearer token from Authorization header
    - Returns user_id, org_id, role if valid
    - Raises HTTPException(401) if token missing/invalid
    - Raises HTTPException(403) if user lacks required role
    - Can compose: `user = Depends(get_current_user)`, `org = Depends(get_current_org)`
  - **SP**: 2 | **Dependencies**: T017
  - **Tags**: [SEC] [CODE]

---

- [ ] **T019** [P0] [CODE] Create Pydantic request/response schemas for Quote endpoints
  - **Description**: Create `src/api/schemas/quote_schemas.py` with request/response models (QuoteCreateRequest, QuoteResponse, QuoteListResponse, ErrorResponse).
  - **Files**: 
    - `src/api/schemas/quote_schemas.py`
    - Include example values for Swagger documentation
  - **Schemas**:
    - `QuoteCreateRequest`: loan_value: Decimal, optional custom rates (if admin)
    - `QuoteResponse`: quote_id, loan_value, premium_amount, brokerage_amount, total_amount, monthly_payment, created_at, status, payment_schedule
    - `QuoteListResponse`: items: List[QuoteResponse], total: int, page: int, limit: int
    - `ErrorResponse`: code: str, message: str, details: dict (optional)
  - **Acceptance**: 
    - All models have docstrings
    - Example values present (Config.schema_extra)
    - Validation: loan_value > 0, rates 0-100%
    - Swagger shows examples when loading /api/docs
  - **SP**: 1 | **Dependencies**: T012, T007
  - **Tags**: [CODE] [API]

---

- [ ] **T020** [P] [US1] Create Quote creation endpoint (POST /api/v1/quotes)
  - **Description**: Implement `src/api/routes/quotes.py` with POST endpoint calling CreateQuoteUseCase, returning 201 Created with Location header.
  - **Files**: 
    - `src/api/routes/quotes.py` (router, post_create_quote)
  - **Acceptance**: 
    - `POST /api/v1/quotes` with `{"loan_value": 10000}`
    - Returns 201 with `Location: /api/v1/quotes/{quote_id}`
    - Response body: full QuoteResponse JSON
    - Invalid loan_value returns 400 with validation error
    - Missing JWT returns 401
    - Authenticated user: quote.user_id = current_user.id, quote.org_id = current_user.org_id
  - **SP**: 2 | **Dependencies**: T018, T019, T013
  - **Tags**: [API] [CODE] [US1]

---

- [ ] **T021** [P] [US2] Create Quote list endpoint (GET /api/v1/quotes)
  - **Description**: Implement GET endpoint with pagination, filtering by date range/status, returning paginated response.
  - **Files**: 
    - `src/api/routes/quotes.py` (get_list_quotes) — add to existing file
  - **Query Parameters**:
    - `page: int = 1`, `limit: int = 50`
    - `status: str = "active"` (active, archived, all)
    - `from_date: datetime`, `to_date: datetime` (optional date range)
  - **Acceptance**: 
    - `GET /api/v1/quotes` returns all active quotes for authenticated user's org
    - Pagination: page=2, limit=20 returns quotes 20-39
    - Filter by status="archived" returns only archived quotes
    - Filter by date range: `from_date=2026-03-01&to_date=2026-03-31`
    - Response: QuoteListResponse with total count, current page, limit
    - Returns only quotes for user's org (org_id filtering)
  - **SP**: 2 | **Dependencies**: T018, T019, T013
  - **Tags**: [API] [CODE] [US2]

---

- [ ] **T022** [P] [US2] Create Quote detail endpoint (GET /api/v1/quotes/{quote_id})
  - **Description**: Implement GET endpoint for single quote by ID with org/user isolation check.
  - **Files**: 
    - `src/api/routes/quotes.py` (get_quote_detail) — add to existing file
  - **Acceptance**: 
    - `GET /api/v1/quotes/{valid-quote-id}` returns QuoteResponse (200)
    - User can only access their own org's quotes (compare org_id)
    - Invalid quote_id returns 404
    - Another org's quote returns 403 Forbidden
    - Missing JWT returns 401
  - **SP**: 1 | **Dependencies**: T018, T019, T013
  - **Tags**: [API] [CODE] [SEC] [US2]

---

- [ ] **T023** [P] [US2] Create Quote delete endpoint (DELETE /api/v1/quotes/{quote_id})
  - **Description**: Implement soft-delete endpoint, returns 204, enforces ownership check.
  - **Files**: 
    - `src/api/routes/quotes.py` (delete_quote) — add to existing file
  - **Acceptance**: 
    - `DELETE /api/v1/quotes/{valid-quote-id}` returns 204 No Content
    - Quote is soft-deleted (status='archived' in DB)
    - Deleted quote no longer appears in list (status filter)
    - User cannot delete another org's quote (403)
    - Cannot delete already-deleted quote (idempotent - still returns 204)
  - **SP**: 1 | **Dependencies**: T018, T019, T013
  - **Tags**: [API] [CODE] [SEC] [US2]

---

- [ ] **T024** [P0] [SEC] Create global error handler & validation error formatting
  - **Description**: Create `src/api/error_handlers.py` with exception handlers for ValueError, ValidationError, PermissionError, returns consistent ErrorResponse JSON.
  - **Files**: 
    - `src/api/error_handlers.py`
    - Update `src/api/main.py` to register handlers
  - **Handlers**:
    - ValueError → 400 Bad Request
    - pydantic.ValidationError → 400 with detailed field errors
    - PermissionError → 403 Forbidden
    - Quote not found → 404 Not Found
    - Generic Exception → 500 Internal Server Error (log context)
  - **Acceptance**: 
    - All errors return ErrorResponse: `{"code": "...", "message": "...", "details": {...}}`
    - Request ID included in response headers (X-Request-ID)
    - Stack trace logged on 5xx errors (not returned to client)
    - Validation error details include field name + reason
  - **SP**: 2 | **Dependencies**: T007, T019
  - **Tags**: [SEC] [CODE] [API]

---

- [ ] **T025** [P0] [CODE] Integrate routers into FastAPI app
  - **Description**: Update `src/api/main.py` to include quote routes, configure API version prefix, documentation URLs.
  - **Files**: 
    - Update `src/api/main.py`
  - **Acceptance**: 
    - `app.include_router(quotes_router, prefix="/api/v1", tags=["Quotes"])`
    - All routes accessible at `/api/v1/*`
    - Swagger UI at `/api/docs` shows all endpoints (title, description, parameters)
    - ReDoc at `/api/redoc` available
    - Health check `/health` still works
    - No import errors on startup
  - **SP**: 1 | **Dependencies**: T020, T021, T022, T023, T024
  - **Tags**: [API] [CODE]

---

## Phase 3: Tests & Documentation (8 tasks)

**Goal**: Achieve 80%+ code coverage, document architecture, write deployment guide, create API examples.

### Acceptance Tests (Phase 3)
- ✅ Overall test coverage ≥80% (pytest --cov reports)
- ✅ All unit tests pass (tests/unit/)
- ✅ All integration tests pass (tests/integration/)
- ✅ README includes installation, usage, deployment steps
- ✅ ARCHITECTURE.md documents layers, dependencies, design decisions
- ✅ DEPLOYMENT.md includes local, Docker, AWS steps
- ✅ Swagger UI loads at http://localhost:8000/api/docs with all endpoints

---

- [ ] **T026** [P] [TEST] Create integration tests for Quote endpoints
  - **Description**: Write `tests/integration/test_quote_endpoints.py` testing full flow (create, list, get, delete) with real database.
  - **Files**: 
    - `tests/integration/test_quote_endpoints.py`
  - **Test Cases**:
    - `test_create_quote_success` (POST with valid data → 201)
    - `test_create_quote_invalid_loan_value` (POST with negative amount → 400)
    - `test_list_quotes_paginated` (GET with page/limit)
    - `test_list_quotes_filtered_by_status` (GET with status=archived)
    - `test_list_quotes_filtered_by_date_range`
    - `test_get_quote_success` (GET {id} → 200)
    - `test_get_quote_not_found` (GET invalid_id → 404)
    - `test_get_quote_org_isolation` (cannot access other org's quote)
    - `test_delete_quote_success` (DELETE → 204)
    - `test_delete_quote_idempotent` (delete twice → both 204)
    - `test_unauthenticated_request` (no JWT → 401)
    - `test_expired_jwt_token` (expired token → 401)
  - **Acceptance**: 
    - All tests pass: `pytest tests/integration/test_quote_endpoints.py -v`
    - Tests use async client (AsyncClient)
    - Database state reset between tests (via conftest fixtures)
    - Coverage for all happy-path + error cases
  - **SP**: 3 | **Dependencies**: T006, T020, T021, T022, T023, T025
  - **Tags**: [TEST] [CODE]

---

- [ ] **T027** [TEST] Create authentication & authorization tests
  - **Description**: Write `tests/integration/test_auth.py` testing JWT validation, role enforcement, org isolation.
  - **Files**: 
    - `tests/integration/test_auth.py`
  - **Test Cases**:
    - `test_valid_jwt_token_accepted`
    - `test_expired_jwt_token_rejected`
    - `test_invalid_signature_rejected`
    - `test_missing_bearer_token_returns_401`
    - `test_user_cannot_access_other_org_quotes`
    - `test_admin_can_access_admin_endpoints` (optional for MVP)
    - `test_non_admin_cannot_update_configuration` (403)
  - **Acceptance**: 
    - All tests pass
    - Test tokens created with different payloads (org_id, role)
    - Coverage ≥85% for security modules
  - **SP**: 2 | **Dependencies**: T017, T018, T006
  - **Tags**: [TEST] [SEC] [CODE]

---

- [ ] **T028** [TEST] Create test coverage report & CI configuration
  - **Description**: Configure coverage goal (80%), create GitHub Actions workflow for testing, coverage badges.
  - **Files**: 
    - `.github/workflows/test.yml` (run pytest, upload coverage)
    - `.coveragerc` (coverage configuration, exclude lines)
    - Update `README.md` with coverage badge
  - **Acceptance**: 
    - `pytest --cov=src --cov-report=term-missing` shows ≥80% coverage
    - `coverage html` generates HTML report in htmlcov/
    - GitHub Actions workflow runs on push (show badge in README)
    - Excluded lines documented (.coveragerc)
  - **SP**: 1 | **Dependencies**: T006, T026, T027
  - **Tags**: [TEST] [DOC]

---

- [ ] **T029** [P] [DOC] Create ARCHITECTURE.md with system design diagram
  - **Description**: Document Clean Architecture layers, dependency flow, key decisions, include ASCII or PlantUML diagram.
  - **Files**: 
    - `ARCHITECTURE.md`
  - **Sections**:
    - Overview (what is the system, scope for MVP)
    - Layers (Domain, Application, Infrastructure, API)
    - Entities & Value Objects (Quote, Money, Rate)
    - Services (QuoteCalculationService, ConfigurationService)
    - Repositories (data access patterns)
    - API Contracts (endpoints, versioning)
    - Security (JWT, role-based access, org isolation)
    - Scalability (horizontal scaling, caching with Redis, DB read replicas)
    - Diagram (PlantUML or ASCII) showing layer dependencies:
      ```
      API Layer
        ↓ (depends on)
      Application Layer (Use Cases)
        ↓ (depends on)
      Domain Layer (Entities, Services)
      Infrastructure Layer (DB, HTTP)
      ```
    - Key Design Decisions (why FastAPI, PostgreSQL, JWT)
    - Future Improvements (multi-tenant admin, advanced reporting)
  - **Acceptance**: 
    - Document is readable and complete (5-10 sections)
    - Diagram shows layer isolation
    - Code examples for key classes
    - Can be displayed at http://localhost:8000/api/docs (reference in sidebar)
  - **SP**: 2 | **Dependencies**: T001, T013
  - **Tags**: [DOC] [ARCH]

---

- [ ] **T030** [P] [DOC] Create DEPLOYMENT.md with AWS, Docker, local instructions
  - **Description**: Document deployment to AWS ECS, Docker local setup, environment variables, database migrations, health checks.
  - **Files**: 
    - `DEPLOYMENT.md`
  - **Sections**:
    - Local Development (docker-compose up, .env setup, running migrations)
    - Docker Build & Push (Dockerfile, ECR registry)
    - AWS ECS Deployment (task definition, service, ALB configuration)
    - Environment Variables (checklist of required vars)
    - Database Migrations (Alembic, rollback procedures)
    - Health Checks & Monitoring (GET /health endpoint, CloudWatch logs)
    - Scaling Configuration (auto-scaling policy, target metrics)
    - Rollback Procedures (how to revert to previous version)
    - Troubleshooting (common errors, logs location)
  - **Acceptance**: 
    - Follow-along instructions for local setup work without errors
    - AWS steps reference official docs (IAM roles, VPC, RDS, ECS, ALB)
    - Environment variable checklist matches config/settings.py
    - Can replicate from scratch using doc alone
  - **SP**: 2 | **Dependencies**: T003, T004, T007
  - **Tags**: [DOC]

---

- [ ] **T031** [P] [DOC] Create README.md with quick start & API examples
  - **Description**: Write comprehensive README with overview, features, quick start, API examples, testing, contributing guidelines.
  - **Files**: 
    - `README.md`
  - **Sections**:
    - Project Overview (what, why, target users)
    - Key Features (quote calculation, CRUD, JWT auth, documentation)
    - Tech Stack (fastapi, postgresql, redis, pytest, jwt)
    - Quick Start
      ```bash
      git clone ...
      cd seguros_api
      cp .env.example .env
      docker-compose up -d
      python -m alembic upgrade head
      uvicorn src.api.main:app --reload
      ```
    - API Examples (curl/Python requests for create, list, get, delete)
      - With JWT token generation example
      - Full request/response for each endpoint
    - Testing
      ```bash
      pytest tests/      # all
      pytest tests/unit/ # unit only
      pytest --cov=src   # with coverage
      ```
    - Project Structure (directory tree explanation)
    - Architecture Overview (link to ARCHITECTURE.md)
    - Contributing (branch naming, PR process)
    - License/Support
    - Coverage Badge ([![Coverage](https://img.shields.io/...)](...))
  - **Acceptance**: 
    - README is 100-150 lines
    - Quick start section works (step-by-step)
    - API examples use real endpoints and test data
    - All commands can be copy-pasted and executed
    - Links to other docs (ARCHITECTURE.md, DEPLOYMENT.md)
  - **SP**: 2 | **Dependencies**: T007, T020, T021, T022, T023
  - **Tags**: [DOC]

---

- [ ] **T032** [P] [DOC] Create API documentation in code (docstrings) & Swagger export
  - **Description**: Add docstrings to all endpoints with operation IDs, request/response examples, error responses. Export Swagger spec as OPENAPI.json.
  - **Files**: 
    - Update `src/api/routes/quotes.py` (all functions have docstrings)
    - Export `openapi.json` on server start
  - **Docstrings** should include:
    - Summary (one-liner)
    - Full description
    - Request body example (if applicable)
    - Response example (200, 400, 401, 403, 404)
    - Error codes & meanings
  - **Example Docstring**:
    ```python
    async def create_quote(request: QuoteCreateRequest, current_user = Depends(get_current_user)):
        """
        Create a new insurance quote.
        
        This endpoint calculates an insurance premium and brokerage fee 
        based on the provided loan value and configured rates.
        
        Args:
            request: Quote request with loan_value (required)
            current_user: Authenticated user (via JWT)
            
        Returns:
            201 Created: QuoteResponse with calculated totals
            400 Bad Request: Invalid loan_value
            401 Unauthorized: Missing or invalid JWT token
            
        Example:
            POST /api/v1/quotes
            Authorization: Bearer <token>
            Content-Type: application/json
            
            {"loan_value": 10000.0}
            
            Response (201):
            {"quote_id": "...", "loan_value": 10000.0, "premium_amount": 2.0, ...}
        """
    ```
  - **Acceptance**: 
    - `GET /api/docs` shows full documentation with all examples
    - `openapi.json` available at `GET /api/openapi.json`
    - Swagger spec is valid (can import into Postman, client generators)
    - All endpoints have operation_id
  - **SP**: 2 | **Dependencies**: T020, T021, T022, T023
  - **Tags**: [DOC] [API]

---

- [ ] **T033** [P] [DOC] Create ASSESSMENT-EVIDENCE.md summarizing evaluation criteria alignment
  - **Description**: Create document mapping all 5 evaluation criteria to implemented code, test coverage, documentation.
  - **Files**: 
    - `ASSESSMENT-EVIDENCE.md`
  - **Sections**:
    - **1. Visão de Arquitetura**
      - ✅ Clean Architecture (domain, application, infrastructure, api layers)
      - ✅ SOLID principles (examples: QuoteCalculationService, Repository pattern)
      - ✅ Scalability (FastAPI async, PostgreSQL, Redis caching ready)
      - ✅ AWS deployment path (DEPLOYMENT.md, ECS/RDS architecture)
      - Evidence: Links to src/domain/, src/application/, src/infrastructure/, src/api/
    - **2. Segurança Implementada**
      - ✅ JWT authentication (JWTHandler, token validation)
      - ✅ Pydantic input validation (request schemas, field validation)
      - ✅ Org-level data isolation (repository filters by org_id)
      - ✅ HTTPS-ready (TLS 1.3 in deployment config)
      - Evidence: src/api/security/, src/api/schemas/, tests/integration/test_auth.py
    - **3. Qualidade de Código**
      - ✅ Type hints (all functions, models)
      - ✅ Error handling (try/except, custom exceptions, global handlers)
      - ✅ SOLID principles (dependency injection, single responsibility)
      - Evidence: src/application/services/, src/domain/entities/, code review
    - **4. Cobertura de Testes**
      - ✅ Unit tests (Quote entity, services)
      - ✅ Integration tests (endpoints, auth, database)
      - ✅ 80%+ coverage (pytest --cov report)
      - Evidence: tests/unit/, tests/integration/, .coveragerc
    - **5. Documentação**
      - ✅ README (quick start, API examples)
      - ✅ ARCHITECTURE.md (design decisions, diagrams)
      - ✅ DEPLOYMENT.md (AWS, Docker, local setup)
      - ✅ Swagger/OpenAPI (interactive at /api/docs)
      - ✅ Inline docstrings & examples
      - Evidence: README.md, ARCHITECTURE.md, DEPLOYMENT.md, /api/docs
  - **Acceptance**: 
    - Document is clear and concise (3-5 pages)
    - All criteria explicitly addressed with code examples
    - Can be used in interview as checklist ("6 of 6 criteria met")
  - **SP**: 1 | **Dependencies**: All phase tasks
  - **Tags**: [DOC]

---

## Dependency Graph & Parallelization

```
Phase 0: Setup & Infrastructure (must complete first)
├─ T001: Project structure
├─ T002: Env & config
├─ T003: Docker (depends T001, T002)
├─ T004: Alembic (depends T003)
├─ T005: SQLAlchemy models (depends T004)
├─ T006: pytest setup (depends T005)
└─ T007: FastAPI app (depends T002, T003)

Phase 1: Core Domain & Application
├─ T008: Quote entity (depends T001)
├─ T009: QuoteCalculationService (depends T008)
├─ T010: ConfigurationService (depends T002, T009)
├─ T011: QuoteRepository (depends T005)
├─ T012: DTOs (depends T009)
├─ T013: Use Cases (depends T009-T012)
├─ T014: Unit tests Quote (depends T008, T006) [P]
├─ T015: Unit tests Service (depends T009, T006) [P]
└─ T016: Unit tests Config (depends T010, T006) [P]

Phase 2: API & Security
├─ T017: JWT handler (depends T002, T007)
├─ T018: JWT dependency (depends T017)
├─ T019: Pydantic schemas (depends T012, T007)
├─ T020: POST /quotes (depends T018-T019, T013) [US1]
├─ T021: GET /quotes (depends T018-T019, T013) [US2]
├─ T022: GET /quotes/{id} (depends T018-T019, T013) [US2]
├─ T023: DELETE /quotes/{id} (depends T018-T019, T013) [US2]
├─ T024: Error handlers (depends T007, T019)
└─ T025: Integrate routers (depends T020-T024)

Phase 3: Tests & Documentation
├─ T026: Integration tests endpoints (depends T006, T020-T025)
├─ T027: Auth tests (depends T017-T018, T006)
├─ T028: Coverage & CI (depends T006, T026-T027) [P]
├─ T029: ARCHITECTURE.md (depends T001, T013) [P]
├─ T030: DEPLOYMENT.md (depends T003-T004, T007) [P]
├─ T031: README.md (depends T007, T020-T023) [P]
├─ T032: Swagger docs (depends T020-T023) [P]
└─ T033: Assessment evidence (depends all)
```

---

## MVP Parallelization Opportunities

**Day 1, Morning (4-5 hours)**:
- **Parallel Stream A** (Infrastructure): T001 → T002 → T003 → T004 → T005
- **Parallel Stream B** (Domain logic, once T001 done): T008 → T009 → T010 → T012 → T013

**Day 1, Afternoon (4-5 hours)**:
- **Parallel Stream A** (API routes): T017 → T018 → T019 → T020-T023-T025
- **Parallel Stream B** (Unit tests): T006 → T014-T016 (parallel) → T026

**Day 2, Morning (3-4 hours)**:
- **Parallel Stream A** (Tests): T026 → T027 → T028
- **Parallel Stream B** (Docs): T029-T032 (parallel)

**Day 2, Afternoon (1-2 hours)**:
- T033: Assessment evidence summary

---

## Estimation Summary

| Phase | Tasks | Total SP | Estimated Hours |
|-------|-------|----------|-----------------|
| Phase 0: Setup | 7 | 12 | 6-8h |
| Phase 1: Domain | 9 | 16 | 8-10h |
| Phase 2: API | 9 | 15 | 8-9h |
| Phase 3: Tests & Docs | 8 | 11 | 6-7h |
| **TOTAL** | **33** | **54** | **28-34h** |

**Experience Adjustment**:
- Senior (5+ years): ~28-32 hours (0.85 speed multiplier)
- Mid-level (2-5 years): ~32-34 hours (normal speed)
- Junior (< 2 years): 40-45 hours (1.3 speed multiplier)

**MVP Configuration for 2-Day Sprint**:
- Working hours: 8h/day × 2 = 16 hours max
- **Realistic scope in 2 days: Phase 0-2 (26 tasks, 43 SP) + core docs (README, basic ARCHITECTURE)**
- **Phase 3 tests can be added in day 3 if needed for 80%+ coverage**

---

## Implementation Strategy

### Sprint Day 1
1. **Morning (0-4h)**: Set up infrastructure (T001-T007) — by noon, FastAPI app running
2. **Afternoon (4-8h)**: Implement core domain + services (T008-T013) — by EOD, services testable

### Sprint Day 2
1. **Morning (0-4h)**: Implement API endpoints + security (T017-T025) — by noon, all 4 CRUD endpoints working
2. **Afternoon (4-8h)**: Write tests (T026-T027) + basic docs (T031, T032) — by EOD, 80%+ coverage

### Sprint Day 3 (Optional)
- Complete ARCHITECTURE.md, DEPLOYMENT.md, assessment evidence (T029-T033)
- Polish error messages, add edge case handling
- Final coverage optimization

---

## Success Criteria (MVP Complete)

✅ **All 5 Evaluation Criteria Met**:
1. [ARCH] Clean Architecture (domain/application/infrastructure/api layers working)
2. [SEC] Security (JWT auth functional, org isolation enforced)
3. [CODE] Quality (type hints, error handling, SOLID principles)
4. [TEST] 80%+ coverage (unit + integration tests passing)
5. [DOC] (README, ARCHITECTURE, DEPLOYMENT, Swagger, inline docs)

✅ **Functional Features**:
- Quote creation with automatic calculation (premium + brokerage)
- Quote listing with pagination & filtering
- Quote retrieval & soft deletion
- JWT authentication on all endpoints
- Organization-level data isolation
- Input validation with clear error messages

✅ **Non-Functional**:
- <100ms response time for quote operations (local testing)
- All endpoints have proper HTTP status codes
- Swagger UI auto-generated at /api/docs
- Code is deployable to Docker/AWS (via docker-compose → DEPLOYMENT.md → ECS)

---

## File Summary

**Total Files to Create**: ~45

### Source Code (src/)
- `src/__init__.py`
- `src/domain/entities/quote.py`, `value_objects.py`, `__init__.py`
- `src/application/services/quote_service.py`, `configuration_service.py`, `__init__.py`
- `src/application/dtos/quote_dto.py`, `mappers.py`, `__init__.py`
- `src/application/use_cases/create_quote.py`, `list_quotes.py`, `get_quote.py`, `delete_quote.py`, `__init__.py`
- `src/infrastructure/database/models.py`, `__init__.py`
- `src/infrastructure/repositories/quote_repository.py`, `sql_quote_repository.py`, `__init__.py`
- `src/api/main.py`, `middleware.py`, `error_handlers.py`, `__init__.py`
- `src/api/security/jwt_handler.py`, `dependencies.py`, `schemas.py`, `__init__.py`
- `src/api/routes/quotes.py`, `__init__.py`
- `src/api/schemas/quote_schemas.py`, `error_schemas.py`, `__init__.py`

### Configuration (root)
- `config/settings.py`, `__init__.py`
- `.env.example`
- `docker-compose.yml`
- `Dockerfile`
- `.dockerignore`
- `pytest.ini`
- `.coveragerc`

### Database (alembic/)
- `alembic/env.py`, `alembic.ini`
- `alembic/versions/001_initial_schema.py`

### Tests (tests/)
- `tests/conftest.py`, `__init__.py`
- `tests/unit/test_quote_entity.py`, `test_quote_service.py`, `test_configuration_service.py`, `__init__.py`
- `tests/integration/test_quote_endpoints.py`, `test_auth.py`, `__init__.py`

### Documentation (root)
- `README.md`
- `ARCHITECTURE.md`
- `DEPLOYMENT.md`
- `ASSESSMENT-EVIDENCE.md`
- `OPENAPI.md` (generated)

### CI/CD (.github/)
- `.github/workflows/test.yml`

---

**Total Effort**: 54 Story Points ≈ 28-34 hours (1-2 developers, 2-3 days)

**Ready to implement?** Each task has clear acceptance criteria and can be assigned independently.
