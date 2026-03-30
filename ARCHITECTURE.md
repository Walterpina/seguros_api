# Architecture

## Overview

Seguros API is a production-ready insurance quotation backend built with Clean Architecture principles and Domain-Driven Design. The system provides REST endpoints for creating, retrieving, and managing insurance quotes with JWT authentication and organization-level data isolation.

**Technology Stack**:
- **Runtime**: Python 3.9+ with async/await support
- **Framework**: FastAPI 0.104+ with Starlette
- **Database**: PostgreSQL 14+ with SQLAlchemy 2.0 ORM
- **Cache**: Redis 7+ for configuration caching
- **Authentication**: JWT (HS256, 24h expiration)
- **Testing**: pytest 7.4+ with 80%+ code coverage
- **Deployment**: Docker & Docker Compose (AWS ECS ready)

---

## System Architecture

### Layered Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         API Layer                            │
│  (FastAPI routes, request/response schemas, error handlers)  │
├─────────────────────────────────────────────────────────────┤
│                   Application Layer                          │
│  (Use cases, services, DTOs, dependency injection)          │
├──────────────────────┬──────────────────────────────────────┤
│   Domain Layer       │     Infrastructure Layer              │
│  (Entities,          │  (Repository implementations,         │
│   Value Objects,     │   Database access, Redis caching,    │
│   Aggregates)        │   External service integrations)     │
└──────────────────────┴──────────────────────────────────────┘
```

### Dependency Flow

- **Domain Layer** has zero external dependencies (framework-agnostic)
- **Application Layer** depends only on Domain interfaces
- **Infrastructure Layer** implements Domain interfaces (inversion of control)
- **API Layer** depends on Application services via dependency injection

This ensures:
- ✅ Easy testing (mock Domain/Infrastructure)
- ✅ Technology independence (swap PostgreSQL for another DB)
- ✅ Clear separation of concerns

---

## Layer Responsibilities

### 1. Domain Layer (`src/domain/`)

**Purpose**: Pure business logic, independent of frameworks or external systems.

**Contents**:
- **Entities** (`src/domain/entities/quote.py`):
  - `Quote`: Aggregate root representing an insurance quote
  - Properties: `id`, `organization_id`, `user_id`, `loan_value`, `premium_rate`, `brokerage_rate`, `premium_amount`, `brokerage_amount`, `total_amount`, `monthly_payment`, `status`, `created_at`, `updated_at`
  - Auto-calculates totals via `__post_init__`
  - Immutable value objects for type safety

- **Value Objects** (`src/domain/entities/value_objects.py`):
  - `Money`: Decimal-based currency with min/max validation
  - `Rate`: Percentage value (0.0-1.0) with validation
  - `MonthlyPayment`: Single installment with month, amount, accumulated
  - `PaymentSchedule`: List of 12 monthly payments

**Key Design Decisions**:
- Uses `@dataclass` with frozen=True for immutability
- Decimal type for financial precision (not float)
- ROUND_HALF_UP rounding for banker's fairness
- Payment schedule generation (simple division + adjustment)

---

### 2. Application Layer (`src/application/`)

**Purpose**: Orchestrate business logic, coordinate between Domain and Infrastructure.

**Contents**:

#### Services (`src/application/services/`):

- **QuoteCalculationService**: Pure calculation logic
  - Methods: `calculate_premium()`, `calculate_brokerage()`, `calculate_total()`, `calculate_monthly_payment()`, `validate_quote_input()`, `create_quote()`
  - Zero external dependencies
  - Stateless, thread-safe

- **ConfigurationService**: Rate management
  - Methods: `get_rates()`, `validate_rates()`, `update_rates()`
  - Reads from environment or database
  - Fallback to defaults if not configured

#### Use Cases (`src/application/use_cases/`):

- **CreateQuoteUseCase**: Orchestrates quote creation
  - Validates input
  - Calls QuoteCalculationService
  - Persists via QuoteRepository
  - Returns QuoteResponse DTO

- **ListQuotesUseCase**: Fetch user's quotes with pagination
  - Supports filtering (status, date range)
  - Organization isolation via org_id
  - Pagination: `page` and `limit` parameters

- **GetQuoteUseCase**: Fetch single quote with authorization check
  - Verifies user belongs to quote's organization
  - Returns 404 if unauthorized

- **DeleteQuoteUseCase**: Soft-delete quote
  - Changes status to 'archived'
  - Preserves audit trail

#### DTOs (`src/application/dtos/`):

- **Request DTOs**:
  - `QuoteCreateRequest`: loan_value (required), premium_rate, brokerage_rate (optional)
  - Field validation: loan_value > 0, rates ∈ [0,1]

- **Response DTOs**:
  - `QuoteResponse`: Full quote with payment_schedule (12-month array)
  - `QuoteListResponse`: Paginated list with metadata (total, page, limit, pages)
  - `MonthlyPaymentItem`: Single installment detail

- **Mapping Functions**:
  - `quote_entity_to_response()`: Domain → Response DTO
  - `orm_model_to_response()`: ORM Model → Response DTO
  - `request_dto_to_entity()`: Request DTO → Domain Entity

---

### 3. Infrastructure Layer (`src/infrastructure/`)

**Purpose**: Data access, persistence, external integrations.

**Contents**:

#### Database (`src/infrastructure/database/`):

- **models.py**: SQLAlchemy 2.0 ORM models
  - `Quote`: ORM mapping to quotes table
  - `Configuration`: ORM mapping to configuration table
  - Decimal precision (numeric(19,2))
  - Indexes on frequent queries: (organization_id, status), (created_at)

- **Migrations** (`alembic/versions/`):
  - `001_initial_schema.py`: Creates quotes and configuration tables
  - Alembic for version control

#### Repositories (`src/infrastructure/repositories/`):

- **QuoteRepository** (ABC):
  - Interface: `create()`, `get()`, `list()`, `delete()`, `update_status()`
  - Defines contract for persistence

- **SQLQuoteRepository**:
  - Implements QuoteRepository for PostgreSQL
  - Filters by organization_id for isolation
  - Paginates with LIMIT and OFFSET
  - Orders by created_at DESC

#### Configuration (`config/settings.py`):

- **Settings** (Pydantic BaseSettings):
  - Reads from .env file
  - Environment variable precedence
  - Validation: secret_key min 32 chars, database_url format, etc.
  - LRU cache for performance

---

### 4. API Layer (`src/api/`)

**Purpose**: HTTP contract, request/response handling, authentication.

**Contents**:

#### Security (`src/api/security/`):

- **JWTHandler**:
  - `create_token()`: Generate JWT with 24h expiration
  - `verify_token()`: Validate signature and expiration
  - `decode_token()`: Extract claims safely
  - Uses HS256 (HMAC-SHA256)

- **Dependencies**:
  - `get_current_user()`: FastAPI dependency, extracts user from JWT
  - `get_current_organization()`: Extracts org_id from token
  - `require_role()`: Enforces role-based access
  - Returns 403 if missing/invalid token

#### Schemas (`src/api/schemas/`):

- **quote_schemas.py**: Request/Response models
  - Pydantic v2 with field validation
  - JSON examples for Swagger documentation
  - ErrorResponse with standardized error format

#### Routes (`src/api/routes/`):

- **quotes.py**: 4 CRUD endpoints
  - `POST /api/v1/quotes`: Create (201 Created)
  - `GET /api/v1/quotes`: List (200 OK, paginated)
  - `GET /api/v1/quotes/{quote_id}`: Detail (200 OK, 404 Not Found)
  - `DELETE /api/v1/quotes/{quote_id}`: Soft-delete (204 No Content)

#### Error Handling (`src/api/error_handlers.py`):

- Global exception handlers:
  - `ValidationError` → 400 Bad Request (field errors)
  - `ValueError` → 400 Bad Request (business logic)
  - `PermissionError` → 403 Forbidden
  - `Exception` (catch-all) → 500 Internal Server Error
- Consistent ErrorResponse format with request_id

#### Main App (`src/api/main.py`):

- FastAPI instance with metadata (title, version, contact)
- CORS middleware for cross-origin requests
- Request ID middleware for tracing
- Health check endpoint (`GET /health`)
- Startup/shutdown events for resource management
- Router inclusion with /api/v1 prefix

---

## Data Flow Example: Creating a Quote

```
1. Client POST /api/v1/quotes
   ├─ Headers: Authorization: Bearer <JWT_TOKEN>
   └─ Body: { "loan_value": 100000.00 }

2. API Layer
   ├─ JWTHandler.verify_token() → Extract user, org_id
   ├─ QuoteCreateRequest validation → Pydantic checks loan_value > 0
   └─ Call CreateQuoteUseCase

3. Application Layer
   ├─ QuoteCalculationService.validate_quote_input()
   ├─ QuoteCalculationService.create_quote()
   │  ├─ Calculate premium = loan_value × premium_rate (0.045)
   │  ├─ Calculate brokerage = premium × brokerage_rate (0.15)
   │  ├─ Calculate total = loan_value + premium + brokerage
   │  ├─ Generate payment_schedule (12 months)
   │  └─ Return Quote entity
   └─ Call QuoteRepository.create()

4. Infrastructure Layer
   ├─ SQLQuoteRepository.create()
   ├─ Map Quote entity → ORM model
   ├─ INSERT into quotes table
   ├─ Commit transaction
   └─ Return persisted quote

5. Application Layer
   ├─ Map ORM model → QuoteResponse DTO
   └─ Return to API layer

6. API Layer
   └─ Return 201 Created with Location header

7. Client receives:
   {
     "quote_id": "123e4567-e89b-12d3-a456-426614174000",
     "loan_value": 100000.00,
     "premium_amount": 4500.00,
     "brokerage_amount": 700.00,
     "total_amount": 105200.00,
     "monthly_payment": 8766.67,
     "payment_schedule": [
       { "month": 1, "amount": 8766.67, "accumulated": 8766.67 },
       ...
       { "month": 12, "amount": 8766.64, "accumulated": 105200.00 }
     ]
   }
```

---

## Security Architecture

### Authentication Flow

1. **Token Generation** (implicit, not in MVP):
   - Client exchanges credentials (username/password) for JWT
   - JWT contains: user_id, organization_id, role, exp

2. **Token Validation** (on each request):
   - Client sends: `Authorization: Bearer <JWT>`
   - FastAPI dependency extracts token
   - JWTHandler.verify_token() checks:
     - ✅ Signature valid (HS256)
     - ✅ Not expired (exp > now)
     - ✅ Required claims present (user_id, org_id)

3. **Authorization** (per resource):
   - Repository filters by organization_id
   - Users cannot see other orgs' quotes
   - Returns 404 instead of 403 (security through obscurity)

### Data Isolation

- **Column-level**: organization_id on every table
- **Query-level**: All queries filtered by `WHERE organization_id = ?`
- **API-level**: JWT provides org_id, repository enforces it

---

## Performance Considerations

### Database

- **Indexing**:
  - (organization_id, status) on quotes
  - created_at on quotes (for ordering)
  - Reduces full table scans

- **Pagination**:
  - Limit 100 default, prevents runaway queries
  - OFFSET/LIMIT efficient for small offsets

- **Connection Pooling**:
  - SQLAlchemy default pool (5 connections)
  - Reused across requests

### Caching

- **Redis** for rate configuration (TTL 5 min)
- **Reduces** database lookups
- **Fallback** to environment variables

### Async/Await

- FastAPI uses Starlette's async
- Non-blocking I/O (database, Redis)
- Handles 10,000+ concurrent requests

---

## Deployment Architecture

### Local Development

```
┌──────────────────────────────────────────┐
│       Docker Compose (docker-compose.yml)│
├──────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐ │
│  │   FastAPI      │  │  PostgreSQL 14 │ │
│  │   :8000        │  │  :5432         │ │
│  └────────────────┘  └────────────────┘ │
│                                          │
│  ┌────────────────┐                     │
│  │   Redis 7      │                     │
│  │  :6379         │                     │
│  └────────────────┘                     │
└──────────────────────────────────────────┘
```

### Production (AWS ECS)

```
┌─────────────────────────────────────────────────────┐
│  AWS Application Load Balancer (ALB) :443 (HTTPS)   │
└────────────────────┬────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼────────┐      ┌───────▼────────┐
│  ECS Task 1    │      │  ECS Task 2    │
│  FastAPI       │      │  FastAPI       │
│  Port 8000     │      │  Port 8000     │
└───────┬────────┘      └───────┬────────┘
        │                       │
        └───────────┬───────────┘
                    │
        ┌───────────┴──────────┐
        │                      │
   ┌────▼──────┐       ┌──────▼────┐
   │  RDS      │       │  ElastiCache  │
   │ PostgreSQL│       │   Redis    │
   │(Multi-AZ) │       └────────────┘
   └───────────┘
```

---

## Testing Strategy

### Unit Tests (40% of tests)
- **Domain layer**: Quote entity, value objects, calculations
- **Application layer**: Services, use cases in isolation
- Mock repositories, no database
- Fast execution (<1s total)

### Integration Tests (60% of tests)
- **API endpoints**: HTTP requests via TestClient
- **Real database**: In-memory SQLite or PostgreSQL
- **JWT authentication**: Full token validation flow
- **Data isolation**: Verify org-filtering works

### Coverage Target
- **Minimum**: 80% code coverage
- **Ideal**: 85%+ with focus on critical paths (calculations, auth)
- **CI/CD**: GitHub Actions enforces threshold

---

## SOLID Principles

### S: Single Responsibility
- `Quote` entity: Represents state
- `QuoteCalculationService`: Calculates values
- `QuoteRepository`: Persists quotes
- `QuoteCreateUseCase`: Orchestrates creation

### O: Open/Closed
- `QuoteRepository` is abstract interface
- `SQLQuoteRepository` implements for PostgreSQL
- Easy to add `MongoQuoteRepository` without changing API

### L: Liskov Substitution
- `SQLQuoteRepository` implements `QuoteRepository` contract
- Can swap implementations without breaking use cases

### I: Interface Segregation
- `QuoteRepository` has 5 specific methods (not all CRUD at once)
- Clients depend only on what they use

### D: Dependency Inversion
- `CreateQuoteUseCase` depends on `QuoteRepository` interface (abstraction)
- Not on `SQLQuoteRepository` (concrete)
- Dependencies injected via constructor

---

## Future Enhancements

### Phase 2 (Production Hardening)
- [ ] Async repository methods (asyncpg for true async)
- [ ] GraphQL endpoint for flexible queries
- [ ] Webhook integration for notifications
- [ ] Rate limiting (5000 req/min per org)
- [ ] Request signing for audit trail

### Phase 3 (Scale to Itaú)
- [ ] Multi-region deployment (São Paulo + Rio)
- [ ] Event sourcing for audit compliance
- [ ] Kafka for quote processing pipeline
- [ ] Machine learning for fraud detection
- [ ] Mobile app (React Native)

---

## Monitoring & Observability

### Logging
- Structured logging with JSON
- Request ID for tracing across services
- Log levels: DEBUG, INFO, WARNING, ERROR

### Metrics (Future)
- Prometheus endpoints at /metrics
- Track: Quote creation volume, API latency, DB connection pool

### Health Checks
- `/health` returns {"status": "ok"}
- Livenesscheck via ALB for ECS

---

## Compliance & Security

### Data Protection
- HTTPS in transit (TLS 1.3)
- Encrypt sensitive fields at rest (future)
- GDPR: Right to be forgotten via DELETE

### Audit Trail
- All quotes have created_at, updated_at
- Status changes logged (active → archived)
- (Future) Immutable event log

### Financial Accuracy
- Decimal(19,2) precision
- ROUND_HALF_UP for rounding
- Payment schedule totals verified

---

## References

- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Domain-Driven Design by Eric Evans](https://www.domainlanguage.com/ddd/)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
