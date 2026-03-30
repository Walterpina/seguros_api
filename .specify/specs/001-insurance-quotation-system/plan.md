# Implementation Plan: Lending Insurance Quotation System

**Branch**: `001-insurance-quotation-system` | **Date**: 2026-03-30 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/001-insurance-quotation-system/spec.md` with clarifications (Q1=C: unlimited loan values, Q2=C: hybrid model with org-level overrides)

---

## Executive Summary

The Lending Insurance Quotation System is a cloud-native, scalable B2B API enabling real-time insurance premium calculations for financial institutions and lending platforms. The system delivers instant sub-100ms quote generation with comprehensive CRUD operations, multi-tenant isolation, and flexible rate configuration per organization.

**Technical Approach**: FastAPI-based microservice on AWS with PostgreSQL (RDS) for persistent storage, Redis (ElastiCache) for configuration caching, and JWT-based authentication. Clean Architecture principles enforce domain isolation; SOLID practices ensure extensibility.

**Delivery Timeline** (3 phases over ~14 weeks):
- **Phase 1 (MVP, Weeks 1-4)**: Core quote calculation + basic CRUD + JWT authentication
- **Phase 2 (Weeks 5-9)**: Multi-tenant org support + rate configuration + admin interface
- **Phase 3 (Weeks 10-14)**: Advanced reporting, audit logs, observability, production hardening

**Key Outcomes**: 
- Production-ready system achieving <100ms p95 latency, 500+ concurrent users
- 99.5% availability with auto-scaling architecture
- Comprehensive OpenAPI documentation with multi-language examples
- Clean Architecture enforcing testability (≥80% coverage) and maintainability

---

## Technical Context

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Language/Version** | Python 3.9+ | Strategic choice: async-first, excellent ecosystem (FastAPI, SQLAlchemy, Pydantic), strong typing with type hints |
| **Primary Framework** | FastAPI 0.104+ | Modern async web framework with integrated OpenAPI generation, dependency injection, automatic request validation |
| **ORM/Data Access** | SQLAlchemy 2.0+ | Mature, flexible ORM with relationship management, query optimization, migration support via Alembic |
| **Schema Validation** | Pydantic v2 | Strict runtime validation, automatic OpenAPI schema generation, rich error messages |
| **Storage (Persistent)** | PostgreSQL 14+ on AWS RDS | ACID guarantees, full-text search, JSON fields for flexible metadata, horizontal scaling via read replicas |
| **Storage (Cache)** | Redis 7+ on AWS ElastiCache | Sub-millisecond access for rate configuration, distributed locking for concurrent updates, session storage |
| **Authentication** | JWT (OAuth2 Bearer tokens) | Stateless, scalable, standard for REST APIs, refresh token support for extended sessions |
| **Testing Framework** | pytest + pytest-asyncio | Industry standard, excellent async support, comprehensive mocking with unittest.mock |
| **API Documentation** | OpenAPI 3.1.0 (Swagger UI) | Automatic generation via FastAPI, interactive exploration at `/api/docs`, code generation for clients |
| **Logging/Observability** | Structured JSON logs → CloudWatch | Production-grade observability, integration with AWS alerting, distributed tracing via X-Ray |
| **Infrastructure** | AWS (ECS + ALB or Lambda + API Gateway) | Managed services reduce operations burden, native VPC/security group support, auto-scaling |
| **Project Type** | Web Service (REST API) | B2B SaaS quotation engine, stateless, horizontally scalable |
| **Performance Goals** | <100ms p95 latency, 500+ concurrent users, 50K+ quotes/day | Driven by user story acceptance criteria and scaling assumptions |
| **Constraints** | Data residency (AWS region), encryption (TLS 1.3 + KMS), audit logging (100% mutations) | Security, compliance, and operational requirements from spec |
| **Scale/Scope** | MVP: 1-5 engineers, ~6 months to production | Small focused team building a single-service monolith; future refactoring to microservices not required for MVP |

---

## Constitution Alignment Check

**GATE: Pre-Phase-0 Validation** — Must pass before proceeding to research & design.

| Principle | Allocation | Status | Notes |
|-----------|-----------|--------|-------|
| **I. Domain Isolation (Clean Architecture)** | All layers (Domain, Application, Infrastructure, API) | ✅ **PASS** | Project structure enforces Clear boundaries; business logic (calculation, rules) isolated in Domain + Application layers; infrastructure (DB, HTTP clients) confined to Infrastructure layer |
| **II. Evolutionary Architecture** | Modular design, versioned API, contract-based interfaces | ✅ **PASS** | Endpoint versioning (`/api/v1/*`), domain-driven API contracts support deprecation; SOLID principles enable refactoring without breaking changes |
| **III. SOLID Compliance** | Code review gates + team enforcement | ✅ **PASS** | Single Responsibility: Controllers handle HTTP, Services handle business logic, Repositories handle data access; Dependency Injection via FastAPI for testability; Interface segregation (slim Pydantic models per use case) |
| **IV. Distributed Resilience** | Circuit breakers, retry logic, timeout policies | ✅ **PASS** | Configuration of database connection pooling (timeout, max retries); cache degradation (calculate live if Redis unavailable); observability instrumentation (request ID tracking, error context) |
| **V. Testability First** | TDD discipline, ≥80% coverage on domain logic | ✅ **PASS** | Premium calculation tested independently (unit), Quote CRUD tested with mocked DB (unit), end-to-end tests with test database (integration); fixtures pre-created for test data |

**Constitutional Violations**: None identified. Architecture aligns with all 5 principles.

**Re-check Phase 1**: Required after design to verify data model, API contracts, and module structure maintain constitutional compliance.

---

## Design Decisions Rationale

### 1. FastAPI vs Alternatives (Django, Starlette, Flask)

| Framework | Async Support | OpenAPI Gen | Validation | Maturity | Decision |
|-----------|---------------|------------|-----------|----------|----------|
| **FastAPI** | Native, optimized | Auto (3.1.0) | Pydantic built-in | 5+ years | ✅ **CHOSEN** |
| Django | Partial (channels) | Manual 3rd-party | Django built-in | 16+ years | ❌ Over-engineered for API-only service |
| Starlette | Native | Manual | Manual | 5+ years | ❌ No automatic validation layer |
| Flask | None (sync) | Manual | Manual | 15+ years | ❌ Blocking I/O incompatible with scale goals |

**Rationale**: FastAPI excels at:
- Async-first design: handles 500+ concurrent users without blocking
- Automatic OpenAPI generation: reduces documentation drift
- Pydantic integration: compile-time type safety, runtime validation, clear error messages
- Developer productivity: minimal boilerplate, excellent IDE autocomplete

### 2. PostgreSQL vs DynamoDB (OLTP vs OLAP Trade-off)

| Aspect | PostgreSQL | DynamoDB | Best For This Project |
|--------|-----------|----------|----------------------|
| **Schema** | Structured, enforced | Flexible, dynamic | ✅ Quotes have fixed schema (loan_value, rates, totals) |
| **Consistency** | ACID (strong) | Eventually consistent | ✅ Financial calculations demand strong consistency |
| **Queries** | Complex JOINs, filters, aggregations | Key-value lookups optimized | ✅ Need list quotes with range filters (date, amount, org) |
| **Scaling (write)** | Vertical (RDS) or read replicas | Unlimited partitioning | ❌ Write scale not critical for MVP (50K quotes/day) |
| **Cost** | Pay per instance size | Pay per request | ~Equal at this scale |
| **Transactions** | Full ACID across tables | Limited (single partition key) | ✅ Need to atomically create quote + audit log |

**Decision**: PostgreSQL (RDS) for MVP.

**Rationale**:
- Quote structure is highly relational (quotes ↔ organizations ↔ users ↔ configurations)
- Reporting queries (list by date range, org, user) straightforward in SQL
- ACID guarantees prevent quote data corruption under concurrent writes
- Audit logging easily integrated via triggers + application logging
- Migration path to DynamoDB available post-MVP if write scaling becomes bottleneck

### 3. Architecture: Monolith vs Microservices

**Decision**: Monolith (single FastAPI service) for MVP.

**Rationale**:
- Scope: Quote calculation + CRUD is singular, cohesive responsibility
- Team: 1-5 engineers; microservices overhead (service discovery, inter-service communication, distributed tracing) not justified
- Operations: Single deployment artifact, centralized logging/monitoring easier
- Refactoring path: If admin interface scales independently, extract to separate service later (no code changes required, just split at API Gateway)

**Deployment Target**: AWS ECS (Fargate) or Lambda, behind Application Load Balancer for orchestration flexibility.

### 4. Multi-Tenancy Model: Org-Level with Override Support

**Design**: 
- **Global default rates**: System-wide premium_rate (0.02%) and brokerage_rate (5%)
- **Organization overrides**: Each org can define custom rates (or inherit global defaults)
- **Per-quote recording**: Each quote stores the premium_rate and brokerage_rate used at creation time (immutable)

**Data Model**:
```
Configurations table:
├─ id (PK)
├─ organization_id (nullable) — NULL = global default, UUID = org-specific
├─ premium_rate
├─ brokerage_rate
├─ effective_from (timestamp)
├─ created_by (user_id)
├─ created_at
└─ notes
```

**Rationale**: 
- Answers Q2 clarification (hybrid model)
- Enables per-org rate management without API changes
- Immutable rate recording prevents retroactive calculation changes
- Cache strategy: global + org-specific configs in Redis, cache invalidation on update

### 5. Error Handling & Distributed Resilience

**Circuit Breaker Pattern** (for database):
- Health check on RDS connection pool; if unhealthy, return 503 Service Unavailable rather than cascading timeout
- Exponential backoff for retries: 100ms, 200ms, 400ms (max 3 attempts)
- Short-circuit: after 5 consecutive failures, fail fast for 30 seconds before retrying

**Cache Degradation** (for rate configuration):
- Lookup order: Redis → RDS → hardcoded defaults
- If Redis unavailable: query RDS directly (slight latency increase, no failure)
- If RDS unavailable: use last-known-good rates from application memory (graceful degradation)

**Observability Instrumentation**:
- Every request gets unique `X-Request-ID` header (distributed tracing)
- Log structure: `{ timestamp, level, message, request_id, user_id, org_id, duration_ms, ...context }`
- Metrics: request latency (p50, p95, p99), error rate, cache hit rate
- Alarms: p95 latency >150ms, error rate >1%, cache hit rate <80%

---

## Data Model

### Domain Entities (Logical)

#### Quote
```
Entity: Quote
Primary Key: quote_id (UUID v4)
Tenant Context: organization_id (UUID)

Attributes:
  - quote_id: UUID, unique
  - organization_id: UUID, foreign key to Organization
  - user_id: UUID, foreign key to User (who created)
  - loan_value: Decimal(15,2), NOT NULL, >0, ≤ 999,999,999.99
  - premium_rate: Decimal(5,4), percentage applied (e.g., 0.0002 = 0.02%)
  - premium_amount: Decimal(12,2), calculated = loan_value × premium_rate
  - brokerage_rate: Decimal(5,2), percentage applied (e.g., 5.00)
  - brokerage_amount: Decimal(12,2), calculated = premium_amount × (brokerage_rate / 100)
  - total_amount: Decimal(12,2), calculated = premium_amount + brokerage_amount
  - monthly_payment: Decimal(10,2), calculated = total_amount / 12, rounded to 2 decimals
  - status: ENUM ('active', 'archived'), default 'active'
  - created_at: Timestamp (UTC), auto-set on insert
  - metadata: JSON, nullable (customer name, vehicle ID, loan product type, etc.)

Indexes:
  - PK: quote_id
  - UK: (organization_id, quote_id) — enables org-scoped queries
  - IX: (organization_id, created_at DESC) — list quotes by org, ordered by date
  - IX: (organization_id, user_id, created_at DESC) — list by user within org
  - IX: (organization_id, status) — filter active vs archived

Relationships:
  - organization_id → Organization.id (FK, NOT NULL, ON DELETE RESTRICT)
  - user_id → User.id (FK, NOT NULL, ON DELETE RESTRICT)

Soft Delete Strategy: 
  - Queries default: WHERE status = 'active'
  - Deletion operation: UPDATE quote SET status = 'archived' WHERE id = ?;
  - Never physically remove (audit trail requirement)
```

#### Configuration
```
Entity: Configuration
Primary Key: config_id (UUID v4)

Attributes:
  - config_id: UUID, unique
  - organization_id: UUID, foreign key to Organization, nullable
      (NULL = system-wide default; UUID = organization-specific override)
  - premium_rate: Decimal(5,4), e.g., 0.0002 = 0.02%
  - brokerage_rate: Decimal(5,2), e.g., 5.00 = 5%
  - effective_from: Timestamp, when rates become active
  - created_by: UUID, foreign key to User (who made the change)
  - created_at: Timestamp (UTC), auto-set on insert
  - notes: Text, change justification (e.g., "Q1 risk adjustment")

Constraints:
  - premium_rate: 0 ≤ value ≤ 0.01 (0% to 1%)
  - brokerage_rate: 0 ≤ value ≤ 50 (0% to 50%)
  - effective_from ≤ now (no future-dated configs in MVP)
  - (organization_id) must be UNIQUE per org: only ONE active config per org at a time
    (handled via application logic: new config replaces old, with historical tracking)

Indexes:
  - PK: config_id
  - UK: (organization_id) where organization_id IS NOT NULL — ensure one active per org
  - UK: (organization_id IS NULL) — ensure one global default (use partial index)
  - IX: (created_at DESC) — audit trail queries

Relationships:
  - organization_id → Organization.id (FK, nullable, ON DELETE CASCADE)
  - created_by → User.id (FK, NOT NULL, ON DELETE RESTRICT)

Immutability:
  - Rates are never updated in-place
  - New rate entry inserted with effective_from timestamp
  - Application queries: SELECT * FROM config WHERE effective_from ≤ NOW() ORDER BY effective_from DESC LIMIT 1
```

#### Organization
```
Entity: Organization
Primary Key: organization_id (UUID v4)

Attributes:
  - organization_id: UUID, unique
  - name: Varchar(255), NOT NULL, unique (org legal name)
  - description: Text, nullable
  - active: Boolean, default TRUE
  - max_concurrent_requests: Integer, default 1000 (rate limiting threshold)
  - created_at: Timestamp (UTC), auto-set
  - updated_at: Timestamp (UTC), auto-update

Indexes:
  - PK: organization_id
  - UK: name
  - IX: active

Relationships:
  - One-to-Many: → Quote (many quotes per org)
  - One-to-Many: → User (many users per org)
  - One-to-One (latest): → Configuration (current rates)
```

#### User
```
Entity: User
Primary Key: user_id (UUID v4)

Attributes:
  - user_id: UUID, unique
  - organization_id: UUID, foreign key to Organization
  - email: Varchar(255), unique, NOT NULL
  - password_hash: Varchar(255), bcrypt hash
  - full_name: Varchar(255), NOT NULL
  - role: ENUM ('admin', 'operator', 'viewer', 'api_client'), default 'operator'
  - active: Boolean, default TRUE
  - created_at: Timestamp (UTC), auto-set
  - updated_at: Timestamp (UTC), auto-update
  - last_login_at: Timestamp, nullable

Indexes:
  - PK: user_id
  - UK: email
  - IX: (organization_id, role) — list admins in org
  - IX: (organization_id, active) — active users per org

Relationships:
  - organization_id → Organization.id (FK, NOT NULL, ON DELETE CASCADE)
  - One-to-Many: → Quote (many quotes per user)

Role Permissions:
  - 'admin': Full CRUD on quotes + configuration management + user management
  - 'operator': CRUD on quotes (own org), read access to rates
  - 'viewer': Read-only access to quotes (own org)
  - 'api_client': Legacy/integration role; same permissions as 'operator'
```

### Database Schema (SQL)

```sql
-- Organizations (tenants)
CREATE TABLE organizations (
  organization_id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL UNIQUE,
  description TEXT,
  active BOOLEAN DEFAULT TRUE,
  max_concurrent_requests INTEGER DEFAULT 1000,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_org_active ON organizations(active);

-- Users
CREATE TYPE user_role AS ENUM ('admin', 'operator', 'viewer', 'api_client');

CREATE TABLE users (
  user_id UUID PRIMARY KEY,
  organization_id UUID NOT NULL REFERENCES organizations(organization_id) ON DELETE CASCADE,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(255) NOT NULL,
  role user_role DEFAULT 'operator',
  active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  last_login_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_user_org_role ON users(organization_id, role);
CREATE INDEX idx_user_org_active ON users(organization_id, active);

-- Configuration (rates)
CREATE TABLE configurations (
  config_id UUID PRIMARY KEY,
  organization_id UUID REFERENCES organizations(organization_id) ON DELETE CASCADE,
  premium_rate NUMERIC(5, 4) NOT NULL CHECK (premium_rate >= 0 AND premium_rate <= 0.01),
  brokerage_rate NUMERIC(5, 2) NOT NULL CHECK (brokerage_rate >= 0 AND brokerage_rate <= 50),
  effective_from TIMESTAMP WITH TIME ZONE NOT NULL,
  created_by UUID NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  notes TEXT,
  CONSTRAINT one_active_per_org UNIQUE (organization_id) WHERE organization_id IS NOT NULL,
  CONSTRAINT one_global_default UNIQUE (organization_id) WHERE organization_id IS NULL
);

CREATE INDEX idx_config_created_at ON configurations(created_at DESC);

-- Quotes (core business entity)
CREATE TYPE quote_status AS ENUM ('active', 'archived');

CREATE TABLE quotes (
  quote_id UUID PRIMARY KEY,
  organization_id UUID NOT NULL REFERENCES organizations(organization_id) ON DELETE RESTRICT,
  user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
  loan_value NUMERIC(15, 2) NOT NULL CHECK (loan_value > 0),
  premium_rate NUMERIC(5, 4) NOT NULL,
  premium_amount NUMERIC(12, 2) NOT NULL,
  brokerage_rate NUMERIC(5, 2) NOT NULL,
  brokerage_amount NUMERIC(12, 2) NOT NULL,
  total_amount NUMERIC(12, 2) NOT NULL,
  monthly_payment NUMERIC(10, 2) NOT NULL,
  status quote_status DEFAULT 'active',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  metadata JSONB
);

CREATE INDEX idx_quote_org_id ON quotes(organization_id, quote_id);
CREATE INDEX idx_quote_org_created_at ON quotes(organization_id, created_at DESC);
CREATE INDEX idx_quote_org_user_created_at ON quotes(organization_id, user_id, created_at DESC);
CREATE INDEX idx_quote_org_status ON quotes(organization_id, status);

-- Audit Logs (compliance & troubleshooting)
CREATE TYPE audit_event_type AS ENUM ('quote_created', 'quote_archived', 'config_updated', 'config_read', 'user_login');

CREATE TABLE audit_logs (
  audit_id UUID PRIMARY KEY,
  organization_id UUID REFERENCES organizations(organization_id) ON DELETE SET NULL,
  user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
  event_type audit_event_type NOT NULL,
  entity_type VARCHAR(50), -- 'quote', 'configuration', 'user'
  entity_id UUID,
  changes JSONB, -- Before & after values
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_org_created_at ON audit_logs(organization_id, created_at DESC);
CREATE INDEX idx_audit_user_created_at ON audit_logs(user_id, created_at DESC);
```

### Data Integrity & Validation Rules

| Rule | Enforcement | Level |
|------|------------|-------|
| Loan value > 0 | CHECK constraint + Pydantic validator | DB + Application |
| Premium rate ∈ [0%, 1%] | CHECK constraint + Pydantic | DB + Application |
| Brokerage rate ∈ [0%, 50%] | CHECK constraint + Pydantic | DB + Application |
| Monetary precision (2 decimals) | NUMERIC(*, 2) type + Decimal class | DB + Application |
| Organization isolation | WHERE org_id = :org_id in all queries | Application pattern |
| Config uniqueness per org | UNIQUE constraint (partial index) | DB |
| Quote immutability | No UPDATE on quote, soft delete only | Application (no UPDATE endpoint) |
| Email uniqueness | UNIQUE constraint | DB |
| Rate audit trail | Every rate change creates new row | Application logic |

---

## API Contracts (OpenAPI 3.1.0)

### Overview

**Base URL**: `https://api.seguros.example.com/api/v1`  
**Authentication**: JWT Bearer token in `Authorization: Bearer <token>` header  
**Rate Limiting**: 1000 req/minute per authenticated user, 100 req/minute per IP (unauthenticated)  
**Response Format**: JSON

### Authentication

#### POST /auth/login
**Summary**: Authenticate user and obtain JWT token.

**Request**:
```json
{
  "email": "john.doe@institution.com",
  "password": "secure_password"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 86400,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Responses**:
- **401 Unauthorized**: Invalid email or password
- **400 Bad Request**: Missing required fields

---

### Quote Management Endpoints

#### POST /quotes
**Summary**: Create a new insurance quote.

**Authentication**: Required (JWT)  
**Roles**: Any authenticated user

**Request**:
```json
{
  "loan_value": 10000.00,
  "metadata": {
    "customer_name": "João Silva",
    "loan_product": "Personal Loan",
    "loan_id": "LOAN-2026-0001"
  }
}
```

**Response** (201 Created):
```json
{
  "quote_id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440002",
  "loan_value": 10000.00,
  "premium_rate": 0.0002,
  "premium_amount": 2.00,
  "brokerage_rate": 5.00,
  "brokerage_amount": 0.10,
  "total_amount": 2.10,
  "monthly_payment": 0.18,
  "payment_terms": {
    "lump_sum": {
      "amount": 2.10,
      "description": "Pay in full upfront"
    },
    "installments": {
      "count": 12,
      "amount_per_month": 0.18,
      "total_over_term": 2.16
    }
  },
  "status": "active",
  "created_at": "2026-03-30T14:30:00Z"
}
```

**Error Responses**:
- **400 Bad Request**: Invalid loan_value (≤0, non-numeric, etc.)
  ```json
  {
    "detail": {
      "validation_errors": [
        {
          "field": "loan_value",
          "message": "ensure this value is greater than 0",
          "type": "value_error.greater_than"
        }
      ]
    }
  }
  ```
- **401 Unauthorized**: Missing or invalid JWT token
- **403 Forbidden**: User's organization not authorized to create quotes
- **500 Internal Server Error**: Database or calculation error
  ```json
  {
    "detail": "Quote creation failed due to internal error",
    "request_id": "550e8400-e29b-41d4-a716-446655440003"
  }
  ```

---

#### GET /quotes/{quote_id}
**Summary**: Retrieve a specific quote by ID.

**Authentication**: Required (JWT)  
**Roles**: 'viewer', 'operator', 'admin'

**Parameters**:
- `quote_id` (path): UUID of the quote

**Response** (200 OK):
```json
{
  "quote_id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440002",
  "loan_value": 10000.00,
  "premium_rate": 0.0002,
  "premium_amount": 2.00,
  "brokerage_rate": 5.00,
  "brokerage_amount": 0.10,
  "total_amount": 2.10,
  "monthly_payment": 0.18,
  "status": "active",
  "created_at": "2026-03-30T14:30:00Z",
  "metadata": {
    "customer_name": "João Silva",
    "loan_product": "Personal Loan"
  }
}
```

**Error Responses**:
- **401 Unauthorized**: Missing JWT token
- **403 Forbidden**: Quote belongs to different organization
- **404 Not Found**: Quote ID does not exist or is archived

---

#### GET /quotes
**Summary**: List quotes with pagination and filtering.

**Authentication**: Required (JWT)  
**Roles**: 'viewer', 'operator', 'admin'

**Query Parameters**:
- `page` (query, optional, default=1): Page number (1-indexed)
- `page_size` (query, optional, default=50): Results per page (max 100)
- `status` (query, optional): Filter by 'active' or 'archived'
- `created_after` (query, optional): ISO 8601 timestamp, e.g., `2026-01-01T00:00:00Z`
- `created_before` (query, optional): ISO 8601 timestamp
- `user_id` (query, optional): Filter by user (admin only)
- `sort_by` (query, optional, default='created_at'): 'created_at', 'loan_value', 'total_amount'
- `sort_order` (query, optional, default='desc'): 'asc' or 'desc'

**Response** (200 OK):
```json
{
  "data": [
    {
      "quote_id": "550e8400-e29b-41d4-a716-446655440000",
      "loan_value": 10000.00,
      "total_amount": 2.10,
      "status": "active",
      "created_at": "2026-03-30T14:30:00Z"
    },
    {
      "quote_id": "550e8400-e29b-41d4-a716-446655440010",
      "loan_value": 50000.00,
      "total_amount": 10.50,
      "status": "active",
      "created_at": "2026-03-29T10:15:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_count": 150,
    "total_pages": 3,
    "has_next": true,
    "has_previous": false
  }
}
```

**Error Responses**:
- **400 Bad Request**: Invalid query parameters (e.g., page_size > 100)
- **401 Unauthorized**: Missing JWT token

---

#### DELETE /quotes/{quote_id}
**Summary**: Archive a quote (soft delete).

**Authentication**: Required (JWT)  
**Roles**: 'operator', 'admin'

**Parameters**:
- `quote_id` (path): UUID of quote to archive

**Response** (204 No Content):
No body returned on success.

**Error Responses**:
- **401 Unauthorized**: Missing JWT token
- **403 Forbidden**: Quote belongs to different organization, or user lacks delete permission
- **404 Not Found**: Quote does not exist or already archived

---

### Configuration Management (Admin)

#### GET /admin/configurations
**Summary**: Retrieve current rate configuration(s).

**Authentication**: Required (JWT)  
**Roles**: 'admin' (org-level), or system admin

**Response** (200 OK):
```json
{
  "global_default": {
    "config_id": "550e8400-e29b-41d4-a716-446655440100",
    "organization_id": null,
    "premium_rate": 0.0002,
    "brokerage_rate": 5.00,
    "effective_from": "2026-03-01T00:00:00Z",
    "created_by": "550e8400-e29b-41d4-a716-446655440050",
    "created_at": "2026-03-01T10:00:00Z"
  },
  "organization_override": {
    "config_id": "550e8400-e29b-41d4-a716-446655440101",
    "organization_id": "550e8400-e29b-41d4-a716-446655440001",
    "premium_rate": 0.00025,
    "brokerage_rate": 7.00,
    "effective_from": "2026-03-15T00:00:00Z",
    "created_by": "550e8400-e29b-41d4-a716-446655440002",
    "created_at": "2026-03-15T14:30:00Z"
  }
}
```

---

#### PUT /admin/configurations
**Summary**: Update premium and brokerage rates (takes effect immediately for new quotes).

**Authentication**: Required (JWT)  
**Roles**: 'admin' only

**Request** (apply to current user's organization):
```json
{
  "premium_rate": 0.00025,
  "brokerage_rate": 7.00,
  "notes": "Q1 2026 rate adjustment due to increased risk"
}
```

**Response** (200 OK):
```json
{
  "config_id": "550e8400-e29b-41d4-a716-446655440102",
  "organization_id": "550e8400-e29b-41d4-a716-446655440001",
  "premium_rate": 0.00025,
  "brokerage_rate": 7.00,
  "effective_from": "2026-03-30T14:35:00Z",
  "created_by": "550e8400-e29b-41d4-a716-446655440002",
  "created_at": "2026-03-30T14:35:00Z",
  "notes": "Q1 2026 rate adjustment due to increased risk"
}
```

**Validation Errors** (400 Bad Request):
```json
{
  "detail": {
    "validation_errors": [
      {
        "field": "premium_rate",
        "message": "ensure this value is less than or equal to 0.01",
        "type": "value_error.less_than_or_equal"
      },
      {
        "field": "brokerage_rate",
        "message": "ensure this value is less than or equal to 50",
        "type": "value_error.less_than_or_equal"
      }
    ]
  }
}
```

---

#### GET /admin/configurations/history
**Summary**: Retrieve historical rate changes for audit.

**Authentication**: Required (JWT)  
**Roles**: 'admin'

**Query Parameters**:
- `limit` (query, optional, default=20): Number of records to return
- `offset` (query, optional, default=0): Pagination offset

**Response** (200 OK):
```json
{
  "history": [
    {
      "config_id": "550e8400-e29b-41d4-a716-446655440102",
      "organization_id": "550e8400-e29b-41d4-a716-446655440001",
      "premium_rate": 0.00025,
      "brokerage_rate": 7.00,
      "created_by_name": "admin@institution.com",
      "created_at": "2026-03-30T14:35:00Z",
      "notes": "Q1 2026 rate adjustment due to increased risk"
    },
    {
      "config_id": "550e8400-e29b-41d4-a716-446655440101",
      "organization_id": "550e8400-e29b-41d4-a716-446655440001",
      "premium_rate": 0.0002,
      "brokerage_rate": 5.00,
      "created_by_name": "setup@institution.com",
      "created_at": "2026-03-15T00:00:00Z",
      "notes": "Initial configuration"
    }
  ]
}
```

---

### Error Handling (Cross-cutting)

All endpoints may return:

#### 401 Unauthorized
```json
{
  "detail": "Invalid or expired authentication token"
}
```

#### 403 Forbidden
```json
{
  "detail": "Insufficient permissions for this operation"
}
```

#### 429 Too Many Requests (Rate Limiting)
```json
{
  "detail": "Rate limit exceeded: maximum 1000 requests per minute",
  "retry_after": 45
}
```

#### 503 Service Unavailable
```json
{
  "detail": "Service temporarily unavailable due to database maintenance",
  "retry_after": 300,
  "request_id": "550e8400-e29b-41d4-a716-446655440003"
}
```

---

## System Architecture

### AWS Infrastructure Topology

```
┌──────────────────────────────────────────────────────────────────────────┐
│                  AWS Cloud (us-east-1, Multi-AZ)                        │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌── Public Layer ────────────────────────────────────────────────────┐  │
│  │                                                                    │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │        AWS CloudFront (Optional CDN)                         │  │  │
│  │  │        - Cache API docs (swagger UI)                         │  │  │
│  │  │        - TLS termination                                     │  │  │
│  │  └────────────────────────┬────────────────────────────────────┘  │  │
│  │                           │                                        │  │
│  │  ┌────────────────────────┴────────────────────────────────────┐  │  │
│  │  │      API Gateway (REST) / Application Load Balancer        │  │  │
│  │  │  - Route /api/v1/* → Target Group                          │  │  │
│  │  │  - Rate limiting (1000 req/min per user)                   │  │  │
│  │  │  - JWT token validation (custom authorizer)                │  │  │
│  │  │  - Request/response logging → CloudWatch                   │  │  │
│  │  │  - TLS 1.3 enforced                                        │  │  │
│  │  └────────────────────────┬────────────────────────────────────┘  │  │
│  │                           │                                        │  │
│  └───────────────────────────┼────────────────────────────────────────┘  │
│                              │                                           │
│  ┌─ VPC (10.0.0.0/16) ───────┼──────────────────────────────────────┐   │
│  │                           │                                      │   │
│  │ ┌─ Public Subnet 1 (AZ-1) │     Public Subnet 2 (AZ-2) ────┐   │   │
│  │ │                         │                                │   │   │
│  │ │  ┌─ NAT Gateway ────────┴────────── NAT Gateway ────┐   │   │   │
│  │ │  │  (Outbound traffic)                              │   │   │   │
│  │ │  └──────────────────────────────────────────────────┘   │   │   │
│  │ └─────────────────────────────────────────────────────────┘   │   │
│  │                         │                                      │   │
│  │ ┌─ Private Subnet 1 (AZ-1)     Private Subnet 2 (AZ-2) ─┐   │   │
│  │ │                                                        │   │   │
│  │ │  ┌───────────────────┐     ┌───────────────────┐     │   │   │
│  │ │  │ ECS Task (Fargate)│     │ ECS Task (Fargate)│     │   │   │
│  │ │  └────────────────────     └───────────────────┘     │   │   │
│  │ │   (FastAPI container)      (Auto-scaled, replicas)   │   │   │
│  │ │                                                        │   │   │
│  │ │  ┌─ Target Group (TG) ──────────────────────────────┐ │   │   │
│  │ │  │ Health checks: /health every 30s                 │ │   │   │
│  │ │  │ Deregistration delay: 30s (graceful shutdown)    │ │   │   │
│  │ │  └────────────────────────────────────────────────── │ │   │   │
│  │ │                                                        │   │   │
│  │ └────────────────────────────────────────────────────────┘   │   │
│  │                                                               │   │
│  │ ┌─ Private Subnet 1 (AZ-1)     Private Subnet 2 (AZ-2) ─┐   │   │
│  │ │                                                        │   │   │
│  │ │  ┌─────────────────────────────────────────────────┐ │   │   │
│  │ │  │   RDS PostgreSQL 14 (Multi-AZ)                 │ │   │   │
│  │ │  │   ├─ Primary Instance (db.t3.medium)           │ │   │   │
│  │ │  │   ├─ Standby Replica (automatic failover)      │ │   │   │
│  │ │  │   ├─ Read Replica (db.t3.small)                │ │   │   │
│  │ │  │   ├─ Storage: 100 GB gp3 (configurable)        │ │   │   │
│  │ │  │   ├─ Backup: daily snapshots, 30 day retention │ │   │   │
│  │ │  │   ├─ Encryption: AWS KMS keys                  │ │   │   │
│  │ │  │   ├─ Security Group: inbound port 5432 only    │ │   │   │
│  │ │  │   └─ Enhanced monitoring (CloudWatch)          │ │   │   │
│  │ │  └─────────────────────────────────────────────────┘ │   │   │
│  │ │                                                        │   │   │
│  │ │  ┌─────────────────────────────────────────────────┐ │   │   │
│  │ │  │   ElastiCache - Redis 7.0 (Multi-AZ)           │ │   │   │
│  │ │  │   ├─ Primary Node (cache.t3.micro)             │ │   │   │
│  │ │  │   ├─ Replica Node (automatic failover)         │ │   │   │
│  │ │  │   ├─ Replication: Asynchronous (ms latency)    │ │   │   │
│  │ │  │   ├─ Encryption in transit: TLS enabled        │ │   │   │
│  │ │  │   ├─ TTL policy (rate config: 5 min)           │ │   │   │
│  │ │  │   └─ Security Group: inbound 6379 from App     │ │   │   │
│  │ │  └─────────────────────────────────────────────────┘ │   │   │
│  │ │                                                        │   │   │
│  │ └────────────────────────────────────────────────────────┘   │   │
│  │                                                               │   │
│  └───────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  AWS Auto Scaling Group (ECS)                              │   │
│  │  ├─ Min: 1 instance (always running)                        │   │
│  │  ├─ Max: 10 instances (scale for peak load)                │   │
│  │  ├─ Target metric: CPU utilization 70%                     │   │
│  │  │  (Trigger scale-up at 75%, scale-down at 50%)          │   │
│  │  ├─ Scale-up cooldown: 60 seconds                          │   │
│  │  ├─ Scale-down cooldown: 300 seconds                       │   │
│  │  └─ Target: 100-500 concurrent requests per instance       │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  CloudWatch Observability                                   │   │
│  │  ├─ Metrics: request latency (p50, p95, p99), error rate   │   │
│  │  ├─ Logs: structured JSON → CloudWatch Logs via stdout    │   │
│  │  ├─ Alarms:                                                 │   │
│  │  │  - p95 latency > 150ms → WARNING                        │   │
│  │  │  - error rate > 1% → CRITICAL                           │   │
│  │  │  - DB CPU > 80% → ALERT                                 │   │
│  │  │  - cache hit ratio < 80% → INVESTIGATE                 │   │
│  │  ├─ Traces: X-Ray integration (sample 10% of requests)    │   │
│  │  └─ Dashboard: real-time view of system health            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Secrets Management                                         │   │
│  │  ├─ JWT signing key (rotate quarterly)                     │   │
│  │  ├─ Database credentials (auto-rotation w/ Secrets Manager)│   │
│  │  ├─ Redis AUTH token (if required)                        │   │
│  │  └─ External API keys (if integrating partners later)     │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

External Integration:
  ├─ Client Applications
  │  └─ Financial institutions, loan platforms, payment processors
  │     (authenticate via JWT, call /api/v1/* endpoints)
  │
  └─ Operational (Team Tools)
     ├─ AWS Console (debugging, manual operations)
     ├─ CloudWatch (monitoring & alerting)
     ├─ ECS Console (task management)
     └─ RDS Console (database administration)
```

### Deployment Strategy

#### Blue-Green Deployment (Zero-Downtime)

```
1. BLUE Environment (Current Production)
   ├─ ALB points to Blue target group
   ├─ ECS service running v1.2.3
   └─ 5-10 active instances

2. GREEN Environment (New Release)
   ├─ ALB does NOT yet point here
   ├─ Pre-warmed with v1.2.4
   ├─ Health checks passing
   └─ Database migrations completed

3. Cutover (Traffic Switch)
   ├─ ALB rules updated → traffic flows to GREEN
   ├─ Monitor metrics (latency, error rate) for 5 min
   ├─ If issues detected: revert to BLUE (1-minute rollback)
   └─ If healthy: decommission BLUE

4. Rollback Path
   ├─ If GREEN fails, ALB switches back to BLUE
   ├─ Previous database state accessible via snapshots
   └─ Communication: notify users of temporary issues
```

### Scalability Architecture (Key Decisions)

| Component | Scaling Strategy | Thresholds | Limits |
|-----------|-----------------|-----------|--------|
| **ECS Tasks** | Horizontal (auto-scaling group) | CPU 70% avg | Min 1, Max 10 per AZ |
| **ALB** | AWS-managed | Request count | Unlimited (AWS scales transparently) |
| **RDS (Read)** | Read replicas | Query latency >100ms | Up to 5 replicas |
| **RDS (Write)** | Vertical (instance type) | If disk >80% or CPU >80% | db.t3.xlarge max for MVP |
| **Redis** | Vertical (instance type) + replication | Memory >80%, latency >10ms | cache.t3.small limits 1.37 GB |
| **Quote Storage** | Partitioning by date (future) | 1M+ records | Indefinite with archiving |

**Concurrency Targets**:
- MVP: 100-500 concurrent users (~5-50K quotes/day)
- Year 1: 1000-5000 concurrent users (~50K-250K quotes/day)
- Year 2+: Scale to 10K+ concurrent users (triggers microservices refactor)

---

## Project Structure

### Source Code Layout (Clean Architecture)

```
seguros_api/
│
├── src/
│   ├── __init__.py
│   │
│   ├── config/                           # Configuration management
│   │   ├── __init__.py
│   │   ├── settings.py                   # Environment-based config (Pydantic ConfigSettings)
│   │   ├── logging.py                    # Structured JSON logging setup
│   │   └── constants.py                  # System-wide constants (min/max rates, etc.)
│   │
│   ├── domain/                           # BUSINESS LOGIC (No external dependencies)
│   │   ├── __init__.py
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   ├── quote.py                  # Quote domain entity
│   │   │   ├── configuration.py          # Rate configuration entity
│   │   │   ├── organization.py           # Tenant entity
│   │   │   └── user.py                   # User entity
│   │   │
│   │   ├── value_objects/
│   │   │   ├── __init__.py
│   │   │   ├── money.py                  # Money value object (amount, currency)
│   │   │   └── rate.py                   # Rate value object (premium, brokerage)
│   │   │
│   │   └── repositories/
│   │       ├── __init__.py
│   │       ├── quote_repository.py       # Abstract interface for quote persistence
│   │       ├── config_repository.py      # Abstract interface for config persistence
│   │       └── user_repository.py        # Abstract interface for user persistence
│   │
│   ├── application/                      # USE CASES (Orchestrate domain + infrastructure)
│   │   ├── __init__.py
│   │   ├── dto/                          # Data Transfer Objects (request/response models)
│   │   │   ├── __init__.py
│   │   │   ├── quote_dto.py              # Quote request/response DTOs (Pydantic models)
│   │   │   ├── config_dto.py             # Configuration DTOs
│   │   │   └── common_dto.py             # Shared DTOs (pagination, errors)
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── quote_service.py          # CreateQuote, RetrieveQuote, ListQuotes, ArchiveQuote use cases
│   │   │   ├── config_service.py         # GetConfig, UpdateConfig use cases
│   │   │   ├── auth_service.py           # Login, TokenValidation use cases
│   │   │   └── calculation_engine.py     # Premium calculation logic
│   │   │
│   │   └── exceptions.py                 # Application-level exceptions (ServiceError, ValidationError)
│   │
│   ├── infrastructure/                   # EXTERNAL SYSTEMS (DB, caching, external APIs)
│   │   ├── __init__.py
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── models.py                 # SQLAlchemy ORM models (mapped to domain entities)
│   │   │   ├── connection.py             # Database connection pooling, session factory
│   │   │   ├── migration/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── env.py                # Alembic migration environment
│   │   │   │   ├── script.py.mako        # Migration template
│   │   │   │   └── versions/
│   │   │   │       ├── 001_initial_schema.py
│   │   │   │       ├── 002_add_audit_logs.py
│   │   │   │       └── ...
│   │   │   └── repositories/             # Concrete repository implementations
│   │   │       ├── __init__.py
│   │   │       ├── quote_repository_impl.py
│   │   │       ├── config_repository_impl.py
│   │   │       └── user_repository_impl.py
│   │   │
│   │   ├── cache/
│   │   │   ├── __init__.py
│   │   │   ├── redis_client.py           # Redis connection, health checks
│   │   │   └── cache_service.py          # Cache abstraction (get, set, delete with TTL)
│   │   │
│   │   ├── security/
│   │   │   ├── __init__.py
│   │   │   ├── jwt.py                    # JWT token generation, validation
│   │   │   ├── password.py               # Password hashing (bcrypt)
│   │   │   └── rbac.py                   # Role-based access control
│   │   │
│   │   ├── observability/
│   │   │   ├── __init__.py
│   │   │   ├── logging.py                # Logger configuration with structured JSON
│   │   │   ├── metrics.py                # Prometheus metrics, CloudWatch reporting
│   │   │   └── tracing.py                # X-Ray distributed tracing
│   │   │
│   │   └── external/
│   │       ├── __init__.py
│   │       ├── http_client.py            # Async HTTP client for external integrations
│   │       └── webhook_sender.py         # (Future) Webhook notifications
│   │
│   └── api/                              # HTTP API LAYER (FastAPI routes, controllers)
│       ├── __init__.py
│       ├── main.py                       # FastAPI app factory, middleware setup
│       ├── dependencies.py               # Dependency injection (JWT user extraction, DB session)
│       ├── middleware/
│       │   ├── __init__.py
│       │   ├── request_id.py             # X-Request-ID generation
│       │   ├── logging.py                # Request/response logging
│       │   ├── error_handler.py          # Global exception handler
│       │   └── rate_limiter.py           # Rate limiting middleware
│       │
│       └── v1/
│           ├── __init__.py
│           ├── routes/
│           │   ├── __init__.py
│           │   ├── auth.py               # POST /login, POST /refresh, POST /logout
│           │   ├── quotes.py             # POST /quotes, GET /quotes/{id}, GET /quotes, DELETE /quotes/{id}
│           │   ├── admin.py              # PUT /admin/configurations, GET /admin/configurations, GET /admin/configurations/history
│           │   └── health.py             # GET /health, GET /readiness (deployment probes)
│           │
│           └── schemas/
│               ├── __init__.py
│               ├── quote_schema.py       # Pydantic models for API request/response
│               ├── config_schema.py      # Configuration schemas
│               ├── user_schema.py        # User schemas
│               └── error_schema.py       # Standard error response models
│
├── tests/
│   ├── __init__.py
│   │
│   ├── conftest.py                       # Pytest fixtures (DB sessions, mock config)
│   ├── fixtures/
│   │   ├── __init__.py
│   │   ├── quote_fixtures.py             # Pre-built Quote objects for tests
│   │   ├── config_fixtures.py            # Pre-built Configuration objects
│   │   └── user_fixtures.py              # Pre-built User objects
│   │
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── domain/
│   │   │   └── test_quote_entity.py      # Test Quote value calculations
│   │   ├── application/
│   │   │   ├── test_quote_service.py     # Test CreateQuote, RetrieveQuote use cases
│   │   │   ├── test_config_service.py    # Test GetConfig, UpdateConfig use cases
│   │   │   └── test_calculation_engine.py # Test premium calculation logic
│   │   └── infrastructure/
│   │       └── test_jwt.py               # Test JWT token generation/validation
│   │
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── database/
│   │   │   ├── test_quote_repository.py  # Test Quote persistence (with test DB)
│   │   │   └── test_config_repository.py # Test Config persistence
│   │   └── api/
│   │       ├── test_quote_endpoints.py   # Test POST /quotes, GET /quotes/{id}, etc.
│   │       ├── test_config_endpoints.py  # Test admin endpoints
│   │       └── test_error_handling.py    # Test error responses
│   │
│   ├── contract/
│   │   ├── __init__.py
│   │   └── test_api_contracts.py         # OpenAPI schema validation
│   │
│   └── load/
│       ├── __init__.py
│       └── locustfile.py                 # Load testing (100-500 concurrent users)
│
├── docs/
│   ├── API.md                            # API documentation (will be generated from OpenAPI)
│   ├── ARCHITECTURE.md                   # System design overview
│   ├── DEVELOPMENT.md                    # Setup & contribution guide
│   ├── INSTALLATION.md                   # Deployment instructions
│   ├── TESTING.md                        # Testing strategy & coverage targets
│   ├── ENV.md                            # Environment variables reference
│   ├── DEPLOYMENT.md                     # CI/CD pipeline & release process
│   └── GLOSSARY.md                       # Domain terminology
│
├── .github/
│   ├── workflows/
│   │   ├── test.yml                      # Unit & integration tests on PR
│   │   ├── lint.yml                      # Black, isort, Flake8, mypy
│   │   ├── security.yml                  # Bandit, safety checks
│   │   └── deploy.yml                    # Build & deploy to AWS on merge
│   │
│   └── pull_request_template.md          # PR template with checklist
│
├── .pre-commit-config.yaml               # Local hooks (Black, isort, Flake8, mypy)
├── .env.example                          # Template for environment variables
├── .env.local                            # (git-ignored) Local dev environment
│
├── docker/
│   ├── Dockerfile                        # Multi-stage build: Python 3.9 slim
│   ├── docker-compose.yml                # Local dev: app + PostgreSQL + Redis
│   └── nginx.conf                        # (Optional) Reverse proxy config
│
├── requirements.txt                      # Python dependencies (locked versions)
├── requirements-dev.txt                  # Dev dependencies (pytest, black, mypy, etc.)
│
├── pyproject.toml                        # Project metadata (name, version, author)
├── setup.py                              # (Optional) Package installation config
│
├── Makefile                              # Common commands (test, lint, run, deploy)
│
├── README.md                             # Project overview & quick start
├── CHANGELOG.md                          # Version history & release notes
│
└── .gitignore                            # Ignore __pycache__, .env.local, etc.
```

### Layer Boundaries & Dependency Flow

```
     API Layer (routes, schemas)
         ↓ (imports)
   Application Layer (use cases, DTOs, services)
         ↓ (imports)
   Domain Layer (entities, repositories, exceptions)
         ↑ (implements)
Infrastructure Layer (DB, cache, security) ← Dependency inversion
         ↓ (imports)
   Repository Implementations (concrete DB code)
```

**Key Rule**: Domain layer NEVER imports Infrastructure or Application layers. All dependencies point inward.

### Configuration Files

#### `pyproject.toml`
```toml
[project]
name = "seguros_api"
version = "1.0.0"
description = "Lending Insurance Quotation System"
authors = [{name = "Team", email = "team@seguros.example.com"}]
requires-python = ">=3.9"
dependencies = [
    "fastapi==0.104.1",
    "uvicorn[standard]==0.24.0",
    "sqlalchemy==2.0.23",
    "alembic==1.13.0",
    "pydantic==2.5.0",
    "pydantic-settings==2.1.0",
    "redis==5.0.1",
    "python-jose[cryptography]==3.3.0",
    "passlib[bcrypt]==1.7.4",
    "python-multipart==0.0.6",
    "httpx==0.25.2",
]

[project.optional-dependencies]
dev = [
    "pytest==7.4.3",
    "pytest-asyncio==0.21.1",
    "pytest-cov==4.1.0",
    "black==23.12.0",
    "isort==5.13.2",
    "flake8==6.1.0",
    "mypy==1.7.0",
    "bandit==1.7.5",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=src --cov-report=html --cov-report=term-missing"

[tool.mypy]
python_version = "3.9"
strict = true

[tool.black]
line-length = 100

[tool.isort]
profile = "black"
```

#### `.env.example`
```bash
# API Configuration
API_ENV=production
API_DEBUG=false
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/seguros
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL_SECONDS=300

# JWT
JWT_SECRET_KEY=<your-secret-key-generate-via-openssl-installed-locally>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# AWS
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=<from-IAM>
AWS_SECRET_ACCESS_KEY=<from-IAM>
AWS_KMS_KEY_ID=<ARN-of-KMS-key>

# Observability
LOG_LEVEL=INFO
SENTRY_DSN=<optional-error-tracking>
```

---

## Implementation Roadmap (Phases)

### Phase 1: MVP Core Functionality (Weeks 1-4)

**Deliverables**:
- Quote creation with premium calculation ✅
- Quote CRUD operations (retrieve, list, delete)
- JWT authentication (login, token validation)
- Single-organization deployment (multi-org backlog)
- Unit tests & integration tests (≥80% coverage)
- OpenAPI/Swagger documentation
- Docker image & local dev setup

**Key Milestones**:
- Week 1: Project setup, database schema, repository layer
- Week 2: Domain logic, calculation engine, application services
- Week 3: API endpoints, authentication, comprehensive tests
- Week 4: Documentation, Docker packaging, manual testing

**Success Criteria**:
- All 5 user stories implement P1 acceptance scenarios
- Quote calculation accurate within 0.01 BRL (2 decimal places)
- Response latency <100ms for quote creation (single instance)
- 100% API endpoint coverage in Swagger/OpenAPI

---

### Phase 2: Multi-Tenancy & Rate Configuration (Weeks 5-9)

**Deliverables**:
- Organization entity & data isolation
- Rate configuration management (global + per-org overrides)
- Admin endpoints for rate updates
- Rate change audit logging
- Configuration caching (Redis)
- User role-based access control (admin, operator, viewer)
- Multi-organization testing

**Key Milestones**:
- Week 5: Organization & user entity setup, RBAC implementation
- Week 6: Configuration service & admin endpoints
- Week 7: Redis caching, rate change auditing, isolation testing
- Week 8: Load testing (100+ concurrent users), performance tuning
- Week 9: Multi-org scenario testing, documentation updates

**Success Criteria**:
- Rate configuration takes effect within 1 second globally
- All quotes in same org share rate configuration (no isolation bugs)
- Admin operations enforce role-based restrictions (403 for non-admins)
- 500+ concurrent users achievable with <100ms p95 latency

---

### Phase 3: Advanced Observability & Production Hardening (Weeks 10-14)

**Deliverables**:
- Distributed tracing (AWS X-Ray)
- CloudWatch metrics & alarms
- Structured JSON logging (JSON formatter)
- Circuit breaker pattern for database
- Advanced error handling & graceful degradation
- Blue-green deployment automation
- Comprehensive disaster recovery procedures
- Performance benchmarking & capacity planning

**Key Milestones**:
- Week 10: X-Ray tracing, CloudWatch metrics setup
- Week 11: Circuit breaker implementation, cache degradation strategy
- Week 12: Automated deployment pipelines (GitHub Actions)
- Week 13: Load testing (500 concurrent users), bottleneck identification
- Week 14: Documentation finalization, runbook creation, production readiness review

**Success Criteria**:
- 99.5% uptime achieved in staging environment
- Database failover completes within 5 minutes with zero data loss
- Error rates <0.5% under sustained 500 concurrent user load
- All critical paths (quote creation, retrieval, deletion) monitored & alarmed

---

### Post-MVP Roadmap (Backlog)

| Feature | Benefit | Phase |
|---------|---------|-------|
| Variable-term payment plans (6, 24, 36 months) | Business flexibility | Phase 4 |
| Multi-currency support (USD, EUR) | International expansion | Phase 4 |
| Insurance underwriting integration | Actual policy generation | Phase 5 |
| Advanced analytics & reporting dashboard | Business intelligence | Phase 5 |
| GraphQL API | Better developer experience | Phase 6 |
| Microservices split (quote service, admin service) | Independent scaling | Phase 6 |
| ML-based pricing engine | Market competitiveness | Future |

---

## Constitution Alignment (Phase 1 Design Review)

**GATE: Post-Phase-1 Validation** — Architecture must maintain all 5 principles after detailed design.

### I. Domain Isolation ✅
- **Evidence**: `/src/domain/` layer has zero external dependencies; calculation engine is pure Python
- **Verification**: Unit tests for Quote entity run in isolation (no DB, no HTTP)
- **Future Risk**: Admin endpoints must not leak domain logic into API layer; use service layer abstraction

### II. Evolutionary Architecture ✅
- **Evidence**: Versioned API (`/api/v1/*`); endpoint changes won't break clients; new features added without modifying core
- **Verification**: Add new endpoint `/api/v1/quotes-v2` in future without touching existing `/quotes`
- **Future Risk**: If multi-tenant model changes, ensure backward compatibility via feature flags

### III. SOLID Principles ✅
- **S**ingle Responsibility: Controllers handle HTTP, Services handle logic, Repositories handle persistence ✅
- **O**pen/Closed: Add new Pydantic validators without modifying existing calculation logic ✅
- **L**iskov: All repository implementations must return same schema (verified in tests) ✅
- **I**nterface Segregation: API models per endpoint (not one bloated Quote schema) ✅
- **D**ependency Inversion: Domain repositories are abstract; infrastructure provides implementations ✅

### IV. Distributed Resilience ✅
- **Evidence**: Circuit breaker for database (if pool exhausted, fail fast not cascade); cache fallback if Redis unavailable
- **Verification**: Integration tests simulate DB failure; application switches to hardcoded rates
- **Future Risk**: When adding external service calls (underwriting), implement exponential backoff & circuit breaker

### V. Testability First ✅
- **Evidence**: All services injected (not constructed in place); repositories mocked in unit tests; E2E tests with test DB
- **Verification**: Project structure enforces dependency injection; 100% of domain logic has unit tests
- **Coverage Target**: ≥80% for domain + application layers (utilities/infrastructure can be lower)

**Constitutional Violations** (Phase 1): None. All principles honored in initial design.

---

## Next Steps & Success Metrics

### Pre-Implementation Checklist ✅
- [ ] Clarifications answered (Q1: unlimited loan values via Decimal(15,2); Q2: hybrid org-level overrides)
- [ ] Architecture approved by team lead
- [ ] AWS account provisioned (dev, staging, production environments)
- [ ] Database credentials & VPC security groups configured
- [ ] Team onboarded on Clean Architecture principles
- [ ] Git repository initialized with branch protection rules

### Phase 0 (Research) → Phase 1 (MVP Development)
This plan document is complete and ready for task breakdown via `/speckit.tasks` command, which will:
1. Generate granular tasks for Phase 1 implementation
2. Assign story points & priority
3. Create pull request templates
4. Set up CI/CD pipeline definition

### Success Metrics (Post-MVP Deployment)

| Metric | Target | Monitoring |
|--------|--------|-----------|
| **Availability** | 99.5% (13.3 hrs/month downtime allowed) | CloudWatch dashboard |
| **Latency (p95)** | ≤100ms for quote creation | CloudWatch metrics + alarms |
| **Throughput** | 50K+ quotes/day supporting 500 concurrent users | Load test simulations |
| **Error Rate** | <0.5% (99.5% success rate) | CloudWatch Logs + alarms |
| **Cache Hit Ratio** | >80% for rate configuration lookups | Redis metrics |
| **Test Coverage** | ≥80% for domain logic, ≥70% overall | pytest-cov reports |
| **Documentation** | 100% API endpoints documented in OpenAPI | Swagger UI validation |
| **Security** | Zero unauthorized access incidents, TLS 1.3 enforced | AWS security monitoring |

---

## Assumptions & Dependencies

### Technical Assumptions
- AWS services available & configured (VPC, RDS, ElastiCache, ECS, CloudWatch)
- PostgreSQL 14+ supports all features used (JSONB, triggers, partitioning)
- FastAPI 0.104+ maintains backward compatibility for life of MVP
- Team familiar with Python async/await patterns

### Operational Assumptions
- Dedicated DevOps engineer for AWS infrastructure provisioning
- Secrets management handled via AWS Secrets Manager (not committed to Git)
- Daily database backups taken automatically by AWS RDS
- On-call rotation established for production incidents

### Business Assumptions
- Premium rate defaults (0.02%, 5%) remain unchanged for 6+ months
- No legal hold or data residency requirements for MVP (align on LGPD compliance later)
- Quote records are immutable post-creation (no edit requirement)
- 24/7 system availability expected (no maintenance windows)

---

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|-----------|
| **Database performance degrades at 1M quotes** | Medium | High | Implement query optimization & read replicas in Phase 2; partition by org_id if needed |
| **Cache (Redis) becomes bottleneck** | Low | Medium | Implement local in-memory cache as fallback; ElastiCache cluster mode if throughput exceeds |
| **JWT expiration causes user frustration** | Medium | Low | Implement refresh token endpoint; update client libraries to auto-refresh |
| **Multi-org isolation bugs leak data** | Low | Critical | Comprehensive integration tests; chaos engineering to test failure scenarios |
| **Rate calculation accuracy issues** | Low | Critical | Pair programming on calculation engine; unit tests with 1000+ random values |
| **AWS service outages** | Low | High | Multi-region failover (future), accepted in MVP for cost/complexity trade-off |

---

## Conclusion

The Lending Insurance Quotation System is architected for production readiness with a 14-week phased delivery approach. Phase 1 delivers core MVP functionality in weeks 1-4; Phase 2 adds multi-tenancy & admin features (weeks 5-9); Phase 3 hardens observability & deployments (weeks 10-14).

The design strictly adheres to Clean Architecture principles and all 5 constitutional mandates. PostgreSQL, FastAPI, and SQLAlchemy provide a solid foundation for scalability, testability, and maintainability. AWS infrastructure enables elastic scaling to handle 500+ concurrent users with <100ms latency.

**Ready for task breakdown & development via `/speckit.tasks` command.**

---

*Plan Version: 1.0.0 | Date: 2026-03-30 | Status: Ready for Implementation*
