<!--
═════════════════════════════════════════════════════════════════════════════
SYNC IMPACT REPORT
═════════════════════════════════════════════════════════════════════════════

**Version Change**: N/A → 1.0.0 (MAJOR: Initial constitution creation)

**New Principles** (5 principles defined):
- I. Isolamento do Domínio (Clean Architecture)
- II. Design para Arquiteturas Evolutivas
- III. Adesão Estrita aos Princípios SOLID
- IV. Resiliência e Tratamento em Ambiente Distribuído
- V. Testabilidade First

**New Sections Added**:
✅ Technology Stack — Python 3.9+, FastAPI, SQLAlchemy, Pydantic, PostgreSQL, Redis
✅ Security Requirements — Input validation, authentication, data protection, secrets management
✅ Performance Standards — Latency targets, query optimization, caching strategies
✅ Governance — Code review standards, testing requirements, continuous delivery compliance

**Template Consistency Status**:
✅ .specify/templates/spec-template.md — Aligned (user stories should include testing per principle V)
✅ .specify/templates/plan-template.md — Aligned (Constitution Check section present)
✅ .specify/templates/tasks-template.md — Aligned (test-first approach reflected)
✅ .specify/templates/checklist-template.md — Review recommended (verify testing checklist matches ≥80% coverage requirement)
⚠️ Runtime guidance docs — No README or quickstart found (PENDING: Create docs/DEVELOPMENT.md with architecture overview and setup instructions)

**Follow-up TODOs**:
1. Create docs/DEVELOPMENT.md with Clean Architecture layers and module boundaries
2. Create docs/API_STANDARDS.md with OpenAPI/Swagger requirements
3. Setup pre-commit hooks for linting (Black, isort, Flake8, mypy strict)
4. Document environment variable schema in docs/ENV.md
5. Create testing strategy doc: docs/TESTING.md (unit, integration, contract tests)

**Compliance Verification**:
All placeholder tokens have been replaced with concrete values. No unresolved brackets remain.
Dates are in ISO format (YYYY-MM-DD). Principles are declarative and testable. Version increments follow semantic versioning.

═════════════════════════════════════════════════════════════════════════════
-->

# seguros_api Constitution

## Core Principles

### I. Isolamento do Domínio (Clean Architecture)
Separation of concerns is non-negotiable. Business logic MUST be isolated from infrastructure and framework dependencies. Domain entities and use-cases exist in a clean boundary; infrastructure concerns (databases, HTTP clients, external services) are adapters at the periphery. This ensures the core business logic remains testable, portable, and independent of technological implementations.

### II. Design para Arquiteturas Evolutivas
Systems MUST be designed to accommodate change without major rewrites. Use modular design with clear contracts between modules; avoid tight coupling; enable incremental refactoring. Architectural decisions should be documented and revisited periodically to ensure they remain valid as requirements evolve.

### III. Adesão Estrita aos Princípios SOLID
- **S**ingle Responsibility Principle: Each class/module has one reason to change
- **O**pen/Closed Principle: Open for extension, closed for modification
- **L**iskov Substitution Principle: Subtypes must be substitutable
- **I**nterface Segregation Principle: Clients depend on specific interfaces, not bloated ones
- **D**ependency Inversion Principle: Depend on abstractions, not concrete implementations

Violations of SOLID are grounds for code review rejection.

### IV. Resiliência e Tratamento em Ambiente Distribuído
APIs MUST handle transient failures gracefully. Implement circuit breakers, retry logic with exponential backoff, timeout policies, and bulkheads for isolated fault domains. All external service calls MUST be instrumented for observability; failures MUST be logged with full context (request ID, service name, operation, retry count). Degradation strategies (fallbacks, caching) are preferred over hard failures.

### V. Testabilidade First
Tests are written BEFORE implementation (TDD discipline). Every public interface MUST have both unit tests (mocked dependencies) and integration tests (real contracts). Test coverage MUST be ≥80% for domain logic. Tests serve as executable specification; they drive design toward testability. Untestable code is refactored on discovery.

## Technology Stack

Python 3.9+ is the mandated runtime. Asynchronous I/O via `asyncio` for non-blocking operations. FastAPI for HTTP API contracts; SQLAlchemy ORM for data access abstraction. Pydantic for strict schema validation and type hints. PostgreSQL for persistent storage; Redis for caching and distributed locking. All dependencies MUST be pinned in `requirements.txt` with hash verification enabled.

## Security Requirements

All API endpoints MUST validate and sanitize inputs using Pydantic models. SQL injection prevention via parameterized queries (enforced by ORM). Authentication via OAuth2/JWT; authorization via role-based access control (RBAC). Sensitive data (passwords, tokens) NEVER logged; PII handled per compliance requirements. HTTPS only in production. Secrets managed via environment variables or secure vault, never committed to repository.

## Performance Standards

API response latency targets: p99 ≤ 500ms for standard queries. Database queries MUST use indexes on foreign keys and common filters. N+1 query problems systematically eliminated via query optimization. Caching strategies (HTTP cache headers, Redis) applied to frequently-accessed, slowly-changing data. Load testing required before production deployment; bottlenecks identified and addressed.

## Governance

This constitution supersedes all other practices and guides architectural decisions. Amendments MUST be documented with rationale, approval by the team lead, and a migration plan for existing code.

**Code Review Standards:**
- Every commit MUST pass linting (Black, isort, Flake8, mypy) and automated tests before review.
- Pull Requests MUST be atomic, containing a single logical responsibility.
- API contract changes (endpoints, request/response schemas) MUST be reflected in updated OpenAPI/Swagger documentation.
- Code Review acts as guardian of architecture; architectural violations are rejected outright. Any breach of module boundaries (e.g., infrastructure details leaking into domain logic) is grounds for mandatory rework.
- Type hints in Python are not optional; mypy strict mode compliance is REQUIRED.

The following are non-negotiable:
- All code MUST conform to strict continuous delivery standards.
- Test updates are MANDATORY alongside feature code (unit and/or E2E tests).
- Code coverage MUST remain ≥80% for domain logic.
- Documentation (OpenAPI, README, inline comments) MUST be kept in sync with implementation.

**Version**: 1.0.0 | **Ratified**: 2026-03-29 | **Last Amended**: 2026-03-30
