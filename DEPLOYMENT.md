# Deployment Guide

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Setup](#docker-setup)
3. [AWS ECS Deployment](#aws-ecs-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Database Migrations](#database-migrations)
6. [Health Checks & Monitoring](#health-checks--monitoring)
7. [Scaling & Performance](#scaling--performance)
8. [Troubleshooting](#troubleshooting)

---

## Local Development

### Prerequisites

- Python 3.9+
- PostgreSQL 14+ (or use Docker)
- Redis 7+ (or use Docker)
- Docker & Docker Compose
- Git

### Quick Start with Docker Compose

```bash
# 1. Clone repository
git clone https://github.com/yourusername/seguros_api.git
cd seguros_api

# 2. Create environment file
cp .env.example .env

# 3. Start services (PostgreSQL + Redis + FastAPI)
docker-compose up -d

# 4. Run database migrations
docker-compose exec api python -m alembic upgrade head

# 5. Verify deployment
curl http://localhost:8000/health
# Expected: {"status": "ok"}

# 6. Access API documentation
# Open browser: http://localhost:8000/api/docs
```

### Pure Local Setup (without Docker)

```bash
# 1. Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start PostgreSQL (locally or Docker)
# Option A: Docker PostgreSQL only
docker run -d \
  --name postgres14 \
  -e POSTGRES_USER=seguros_user \
  -e POSTGRES_PASSWORD=seguros_pass \
  -e POSTGRES_DB=seguros_api \
  -p 5432:5432 \
  postgres:14

# Option B: Use local PostgreSQL
# Create database and user manually

# 4. Configure environment
cat > .env << EOF
DATABASE_URL=postgresql://seguros_user:seguros_pass@localhost:5432/seguros_api
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-min-32-chars-long
DEBUG=False
EOF

# 5. Run migrations
python -m alembic upgrade head

# 6. Start FastAPI server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# 7. Visit http://localhost:8000/api/docs
```

### Development Workflow

```bash
# Run tests locally
pytest tests/unit -v              # Unit tests only
pytest tests/integration -v       # Integration tests (requires DB)
pytest tests -v --cov=src        # Full coverage report
pytest tests -v -k "test_create" # Single test pattern

# Apply code formatting
black src tests

# Check type hints
mypy src --ignore-missing-imports

# Lint code
flake8 src tests

# Watch for changes during development
pytest-watch tests/unit
```

---

## Docker Setup

### Docker Compose Architecture

**File**: `docker-compose.yml`

```yaml
Services:
  - postgres:14 (port 5432)
  - redis:7 (port 6379)
  - api (port 8000)
```

### Building Docker Image

```bash
# Build image locally
docker build -t seguros-api:latest .

# Build for specific platform (ARM64 for Apple Silicon)
docker build --platform linux/arm64 -t seguros-api:latest .

# Verify image
docker image inspect seguros-api:latest
```

### Running with Docker Compose

```bash
# Start all services in background
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Remove volumes (careful - deletes data!)
docker-compose down -v

# Rebuild after code changes
docker-compose up -d --build
```

### Health Check

```bash
# Check API health
docker-compose exec api curl http://localhost:8000/health

# Check PostgreSQL
docker-compose exec postgres pg_isready -U seguros_user

# Check Redis
docker-compose exec redis redis-cli ping
```

---

## AWS ECS Deployment

### Architecture Overview

```
Application Load Balancer (ALB)
  ↓ (port 443 → 8000)
ECS Cluster
  ├─ Task 1: FastAPI (Desired count: 2)
  ├─ Task 2: FastAPI
  └─ Task N: FastAPI
    ↓
RDS PostgreSQL (Multi-AZ, backup enabled)
ElastiCache Redis (Cluster mode, auto-failover)
```

### Prerequisites

- AWS Account with appropriate permissions
- AWS CLI v2 configured
- ECR repository created: `seguros-api`
- RDS PostgreSQL instance (Postgres 14)
- ElastiCache cluster (Redis 7)
- ECS Cluster (Fargate or EC2)
- Application Load Balancer

### Step-by-Step Deployment

#### 1. Push Docker Image to ECR

```bash
# Login to ECR
aws_account_id=123456789012
aws_region=us-east-1
aws ecr get-login-password --region $aws_region | \
  docker login --username AWS --password-stdin $aws_account_id.dkr.ecr.$aws_region.amazonaws.com

# Tag image
docker tag seguros-api:latest $aws_account_id.dkr.ecr.$aws_region.amazonaws.com/seguros-api:latest

# Push to ECR
docker push $aws_account_id.dkr.ecr.$aws_region.amazonaws.com/seguros-api:latest
```

#### 2. Create ECS Task Definition

```bash
# Create task definition JSON (task-definition.json)
# Set:
#  - Image: $aws_account_id.dkr.ecr.$aws_region.amazonaws.com/seguros-api:latest
#  - CPU: 256
#  - Memory: 512
#  - Port mappings: 8000
#  - Environment variables: DATABASE_URL, REDIS_URL, SECRET_KEY

aws ecs register-task-definition \
  --cli-input-json file://task-definition.json
```

#### 3. Create or Update ECS Service

```bash
# Create service
aws ecs create-service \
  --cluster seguros-cluster \
  --service-name seguros-api-service \
  --task-definition seguros-api:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=DISABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=api,containerPort=8000"

# Or update existing service
aws ecs update-service \
  --cluster seguros-cluster \
  --service seguros-api-service \
  --task-definition seguros-api:2 \
  --desired-count 3
```

#### 4. Configure Auto-Scaling

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/seguros-cluster/seguros-api-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

# Create scaling policy (CPU-based)
aws application-autoscaling put-scaling-policy \
  --policy-name scale-cpu \
  --service-namespace ecs \
  --resource-id service/seguros-cluster/seguros-api-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    }
  }'
```

#### 5. Verify Deployment

```bash
# Check service status
aws ecs describe-services \
  --cluster seguros-cluster \
  --services seguros-api-service

# View logs (CloudWatch)
aws logs tail /ecs/seguros-api --follow

# Test via load balancer
curl https://api.seguros.example.com/health
# Expected: {"status": "ok"}
```

### Blue-Green Deployment

```bash
# 1. Create new task definition (v2)
aws ecs register-task-definition --cli-input-json file://task-definition-v2.json

# 2. Create green service (running new version)
aws ecs create-service \
  --cluster seguros-cluster \
  --service-name seguros-api-service-green \
  --task-definition seguros-api:2 \
  --desired-count 2 \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:.../green,..."

# 3. Test green service
curl https://green.seguros.example.com/health

# 4. Switch load balancer traffic to green
aws elbv2 modify-rule \
  --rule-arn arn:aws:elasticloadbalancing:... \
  --conditions Field=host-header,Values=api.seguros.example.com \
  --actions Type=forward,TargetGroupArn=green-target-group

# 5. Delete blue service
aws ecs delete-service \
  --cluster seguros-cluster \
  --service seguros-api-service \
  --force
```

---

## Environment Configuration

### Environment Variables

Create `.env` file from `.env.example`:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/seguros_api
# Format: postgresql://[user[:password]@][netloc][:port][/dbname][?param1=value1&...]

# Redis
REDIS_URL=redis://localhost:6379
# Optional: redis://[:password]@host:port/db

# Security
SECRET_KEY=generate-a-random-32-char-string-use-secrets-token_urlsafe
# Minimum 32 characters for HS256
# Generate: python -c "import secrets; print(secrets.token_urlsafe(32))"

# Rates (optional, defaults to 0.045 and 0.15)
PREMIUM_RATE=0.045
BROKERAGE_RATE=0.15

# FastAPI
DEBUG=False  # Set True only in development
ENV=production  # or development, testing

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

### AWS Secrets Manager (Recommended)

```bash
# Store secret in AWS Secrets Manager
aws secretsmanager create-secret \
  --name /prod/seguros-api/database-url \
  --secret-string "postgresql://user:pass@rds.amazon.com:5432/seguros_api"

# Reference in ECS task definition:
# "environment": [
#   {
#     "name": "DATABASE_URL",
#     "valueFrom": "arn:aws:secretsmanager:region:account:secret:..."
#   }
# ]
```

---

## Database Migrations

### Running Migrations

```bash
# Upgrade to latest migration
python -m alembic upgrade head

# Upgrade to specific revision
python -m alembic upgrade abc1234

# Downgrade one version
python -m alembic downgrade -1

# View migration history
python -m alembic history

# Check current revision
python -m alembic current
```

### Creating New Migrations

```bash
# Auto-generate migration (detects schema changes)
python -m alembic revision --autogenerate -m "Add user_email column"

# Manual migration
python -m alembic revision -m "Custom migration description"

# Edit migration file in alembic/versions/
# Then apply:
python -m alembic upgrade head
```

### Database Backup Strategy

```bash
# Backup PostgreSQL (local)
pg_dump -h localhost -U seguros_user seguros_api > backup.sql

# Restore from backup
psql -h localhost -U seguros_user seguros_api < backup.sql

# AWS RDS automatic backup
# - Enable automated backups (7-35 day retention)
# - Enable copy to different region for disaster recovery
# - Test restore procedures regularly
```

---

## Health Checks & Monitoring

### Application Health Check

```bash
# Simple health check
GET /health
Response: {"status": "ok"}

# Should return 200 OK within 1 second
# Used by: ALB health checks, Kubernetes liveness probes
```

### ECS Task Health Check

```yaml
# In docker-compose.yml or task definition:
healthCheck:
  command: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
  interval: 30s        # Check every 30 seconds
  timeout: 5s          # Timeout after 5 seconds
  retries: 3           # Mark unhealthy after 3 failures
  startPeriod: 60s     # Wait 60s before checking (for startup)
```

### CloudWatch Monitoring

```bash
# Create custom metric
aws cloudwatch put-metric-data \
  --namespace seguros-api \
  --metric-name QuotesCreated \
  --value 1

# View metrics in AWS Console
# CloudWatch → Metrics → Custom namespaces → seguros-api
```

### Log Aggregation

```bash
# View recent logs
docker-compose logs -f api

# Search logs
docker-compose logs api | grep "error"

# ECS logs (CloudWatch)
aws logs tail /ecs/seguros-api --follow --since 10m
```

---

## Scaling & Performance

### Horizontal Scaling (Add More Tasks)

```bash
# Scale to 5 tasks
aws ecs update-service \
  --cluster seguros-cluster \
  --service seguros-api-service \
  --desired-count 5

# Monitor task count
aws ecs describe-services \
  --cluster seguros-cluster \
  --services seguros-api-service \
  --query 'services[0].desiredCount,services[0].runningCount'
```

### Vertical Scaling (Increase Resources per Task)

```bash
# Update task definition with more CPU/Memory
# Edit task-definition.json:
# - CPU: 256 → 512
# - Memory: 512 → 1024

aws ecs register-task-definition --cli-input-json file://task-definition.json
aws ecs update-service \
  --cluster seguros-cluster \
  --service seguros-api-service \
  --task-definition seguros-api:2
```

### Database Performance

```sql
-- Check slow queries (PostgreSQL)
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Create missing indexes
CREATE INDEX idx_quotes_org_status ON quotes(organization_id, status);
CREATE INDEX idx_quotes_created_at ON quotes(created_at DESC);

-- Analyze query plan
EXPLAIN ANALYZE
SELECT COUNT(*) FROM quotes
WHERE organization_id = '123e4567-e89b-12d3-a456-426614174000'
AND status = 'active';
```

### Redis Caching

```bash
# Monitor Redis memory usage
redis-cli info memory | grep used_memory_human

# Flush cache if needed
redis-cli FLUSHALL

# Monitor hits/misses
redis-cli info stats | grep hits
redis-cli info stats | grep misses
```

---

## Troubleshooting

### Container Won't Start

```bash
# View logs
docker-compose logs api

# Common issues:
# 1. Port 8000 already in use
kill $(lsof -t -i :8000)
# Or use different port: docker-compose -e API_PORT=8001

# 2. Database connection failed
docker-compose logs postgres

# 3. Out of disk space
docker system prune -a
```

### Database Migration Errors

```bash
# View alembic logs
python -m alembic current

# If migration failed, check history
python -m alembic history

# Downgrade and re-run
python -m alembic downgrade -1
python -m alembic upgrade head
```

### API Returns 500 Error

```bash
# Check application logs
docker-compose logs api | grep ERROR

# Validate database connectivity
docker-compose exec api python -c "
from config.settings import get_settings
settings = get_settings()
print(f'DB URL: {settings.database_url}')
"

# Test migrations ran correctly
docker-compose exec api python -m alembic current
```

### JWT Token Issues

```bash
# Verify token signature
python -c "
import jwt
token = 'your-token-here'
payload = jwt.decode(token, options={'verify_signature': False})
print(payload)
"

# Check token expiration
python -c "
from datetime import datetime
import jwt
token = 'your-token'
payload = jwt.decode(token, options={'verify_signature': False})
exp = datetime.fromtimestamp(payload['exp'])
print(f'Expires: {exp}')
"
```

### High API Latency

```bash
# Check database query time
docker-compose logs postgres | grep duration

# Profile Python code
python -m cProfile -s cumulative -m pytest tests/ > profile.txt

# Check Docker resource usage
docker stats
```

---

## Rollback Procedures

### Rollback ECS Deployment

```bash
# Revert to previous task definition
aws ecs describe-task-definition --task-definition seguros-api:1

# Update service to use old version
aws ecs update-service \
  --cluster seguros-cluster \
  --service seguros-api-service \
  --task-definition seguros-api:1

# Monitor rollback
aws ecs describe-services \
  --cluster seguros-cluster \
  --services seguros-api-service \
  --query 'services[0].deployments'
```

### Rollback Database Migration

```bash
# Downgrade to previous migration
python -m alembic downgrade -1

# Or specific revision
python -m alembic downgrade 2021_11_15_12_34_56
```

---

## Disaster Recovery

### Backup & Restore

```bash
# Daily backup to S3
aws s3 sync /var/lib/postgresql s3://backup-bucket/seguros-api/$(date +%Y%m%d)/

# Test restore procedure monthly
aws s3 cp s3://backup-bucket/seguros-api/latest/ ./ --recursive
# Restore into test database to verify
```

### Multi-Region Setup (Future)

```bash
# Replicate RDS to secondary region
aws rds create-db-instance-read-replica \
  --db-instance-identifier seguros-api-replica \
  --source-db-instance-identifier seguros-api \
  --source-region us-east-1 \
  --destination-region us-west-2

# Promote replica in case of primary region failure
aws rds promote-read-replica \
  --db-instance-identifier seguros-api-replica
```

---

## References

- [Docker Documentation](https://docs.docker.com/)
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [PostgreSQL Deployment](https://www.postgresql.org/docs/14/runtime.html)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/concepts/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)
