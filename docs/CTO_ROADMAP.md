# AIntranet - CTO Technical Roadmap

> Strategic improvement plan for the AIntranet corporate portal.
> Estimated timeline: 14 weeks | Team size: 2-3 developers

---

## Executive Summary

This roadmap addresses critical technical debt and security vulnerabilities in AIntranet. The plan is organized into 6 phases, prioritized by risk and business impact.

### Current State Assessment

| Area | Status | Risk Level |
|------|--------|------------|
| Security | Multiple vulnerabilities | **CRITICAL** |
| Performance | No connection pooling, N+1 queries | **HIGH** |
| Error Handling | Inconsistent, silent failures | **MEDIUM** |
| Testing | No automated tests | **HIGH** |
| DevOps | No CI/CD, no containerization | **MEDIUM** |
| Documentation | Basic CLAUDE.md exists | **LOW** |

---

## Phase 1: Critical Security Fixes (Week 1-2)

**Goal**: Eliminate critical security vulnerabilities before any production deployment.

### 1.1 Production Configuration
| Task | File | Priority |
|------|------|----------|
| Disable `debug=True` | `app.py:157` | P0 |
| Force `SESSION_COOKIE_SECURE=True` | `config.py:19` | P0 |
| Remove fallback secret key | `config.py:6` | P0 |

```python
# app.py - Fix
if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
```

### 1.2 Authentication Hardening
| Task | Details | Effort |
|------|---------|--------|
| Password policy | Min 12 chars, require uppercase/lowercase/number/special | 2h |
| Brute force protection | Lock account after 5 failed attempts for 30min | 4h |
| Session timeout | Reduce from 30 days to 4 hours | 1h |
| CSRF protection | Implement Flask-WTF on all forms | 4h |

```python
# Example: Brute force protection
class LoginAttemptTracker:
    MAX_ATTEMPTS = 5
    LOCKOUT_DURATION = timedelta(minutes=30)

    @staticmethod
    def check_and_increment(username):
        # Track in Redis or DB
        pass
```

### 1.3 Database Connection Pooling
**Current problem**: New connection per query = ~100ms overhead + connection exhaustion

```python
# database.py - Implement pooling
from dbutils.pooled_db import PooledDB
import mysql.connector

pool = PooledDB(
    creator=mysql.connector,
    maxconnections=20,
    mincached=5,
    maxcached=10,
    host=Config.DB_CONFIG['host'],
    user=Config.DB_CONFIG['user'],
    password=Config.DB_CONFIG['password'],
    database=Config.DB_CONFIG['database'],
    charset='utf8mb4'
)

def get_connection():
    return pool.connection()
```

### 1.4 Rate Limiting
```python
# Install: pip install flask-limiter
from flask_limiter import Limiter

limiter = Limiter(app, key_func=get_remote_address)

@chatbot_bp.route('/chat', methods=['POST'])
@limiter.limit("30/minute")  # 30 requests per minute
def chat():
    pass
```

**Deliverables Phase 1:**
- [ ] Security audit passed
- [ ] Connection pooling active
- [ ] Rate limiting configured
- [ ] CSRF tokens on all forms

---

## Phase 2: Error Handling & Logging (Week 3-4)

**Goal**: Replace print statements with proper logging, implement audit trail.

### 2.1 Logging Framework
```python
# config.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    handler = RotatingFileHandler(
        'logs/aintranet.log',
        maxBytes=10_000_000,  # 10MB
        backupCount=5
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s [%(name)s] %(message)s'
    ))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
```

### 2.2 Audit Logging Schema
```sql
CREATE TABLE audit_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id INT,
    action VARCHAR(50),  -- 'CREATE', 'UPDATE', 'DELETE', 'LOGIN'
    entity_type VARCHAR(50),  -- 'user', 'ticket', 'vacation'
    entity_id INT,
    old_values JSON,
    new_values JSON,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    INDEX idx_user_timestamp (user_id, timestamp),
    INDEX idx_entity (entity_type, entity_id)
);
```

### 2.3 JSON Schema Validation for Tools
```python
# modules/chatbot/tool_schemas.py
from jsonschema import validate, ValidationError

REQUEST_VACATION_SCHEMA = {
    "type": "object",
    "properties": {
        "fecha_inicio": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
        "fecha_fin": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
        "tipo": {"type": "string", "enum": ["vacaciones", "permiso", "licencia_medica", "otro"]},
        "motivo": {"type": "string", "maxLength": 500}
    },
    "required": ["fecha_inicio", "fecha_fin", "tipo"]
}

def validate_tool_args(tool_name, args):
    schemas = {"request_vacation": REQUEST_VACATION_SCHEMA, ...}
    validate(instance=args, schema=schemas.get(tool_name, {}))
```

### 2.4 Database Transactions
```python
# database.py
from contextlib import contextmanager

@contextmanager
def transaction():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# Usage:
with transaction() as conn:
    user_id = User.create(conn, ...)
    Employee.create_from_user(conn, user_id, ...)
```

**Deliverables Phase 2:**
- [ ] All print() replaced with logging
- [ ] Audit log capturing all mutations
- [ ] Tool arguments validated
- [ ] Transactions for multi-step operations

---

## Phase 3: Performance & Scalability (Week 5-6)

**Goal**: Support 500+ concurrent users without degradation.

### 3.1 Pagination
```python
# models.py
class PaginatedResult:
    def __init__(self, items, total, page, per_page):
        self.items = items
        self.total = total
        self.page = page
        self.per_page = per_page
        self.pages = (total + per_page - 1) // per_page

@staticmethod
def get_all_paginated(page=1, per_page=20):
    offset = (page - 1) * per_page
    query = "SELECT * FROM empleados WHERE activo = TRUE LIMIT %s OFFSET %s"
    items = execute_query(query, (per_page, offset), fetch=True)

    count_query = "SELECT COUNT(*) as total FROM empleados WHERE activo = TRUE"
    total = execute_query(count_query, fetch=True)[0]['total']

    return PaginatedResult(items, total, page, per_page)
```

### 3.2 Database Indexes
```sql
-- Add to sql/migrations/002_add_indexes.sql
CREATE INDEX idx_chatbot_messages_session ON chatbot_messages(session_id);
CREATE INDEX idx_vacaciones_empleado ON vacaciones(empleado_id);
CREATE INDEX idx_vacaciones_estado ON vacaciones(estado);
CREATE INDEX idx_tickets_solicitante ON tickets(solicitante_id);
CREATE INDEX idx_tickets_estado ON tickets(estado);
CREATE INDEX idx_facturas_cliente ON facturas(cliente_id);
CREATE INDEX idx_facturas_vencimiento ON facturas(fecha_vencimiento);
CREATE INDEX idx_empleados_usuario ON empleados(usuario_id);
CREATE INDEX idx_usuarios_username ON usuarios(username);
CREATE INDEX idx_usuarios_email ON usuarios(email);
```

### 3.3 Query Optimization (N+1 fixes)
```python
# Before (6 queries):
employees = Employee.get_all()
documents = Document.get_all()
tickets = Ticket.get_all()
...

# After (1 query with dashboard stats):
@staticmethod
def get_dashboard_stats():
    query = """
    SELECT
        (SELECT COUNT(*) FROM empleados WHERE activo = TRUE) as total_empleados,
        (SELECT COUNT(*) FROM documentos WHERE activo = TRUE) as total_documentos,
        (SELECT COUNT(*) FROM tickets WHERE estado IN ('abierto', 'en_proceso')) as tickets_abiertos,
        (SELECT COUNT(*) FROM vacaciones WHERE estado = 'pendiente') as vacaciones_pendientes,
        (SELECT COUNT(*) FROM anuncios WHERE activo = TRUE) as anuncios_activos
    """
    return execute_query(query, fetch=True)[0]
```

### 3.4 Background Jobs (Celery)
```python
# tasks.py
from celery import Celery

celery = Celery('aintranet', broker='redis://localhost:6379/0')

@celery.task
def cleanup_old_sessions():
    """Run daily to clean old chatbot sessions"""
    ChatbotSession.cleanup_old_sessions(days=30)

@celery.task
def send_vacation_notification(vacation_id):
    """Async email notification"""
    pass
```

**Deliverables Phase 3:**
- [ ] All list endpoints paginated
- [ ] Database indexes added
- [ ] Dashboard loads in <500ms
- [ ] Background job infrastructure ready

---

## Phase 4: Code Quality & Testing (Week 7-8)

**Goal**: Establish testing culture, improve maintainability.

### 4.1 Type Hints
```python
# models.py with type hints
from typing import Optional, List, Dict, Any

class User:
    @staticmethod
    def get_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM usuarios WHERE id = %s"
        result = execute_query(query, (user_id,), fetch=True)
        return result[0] if result else None

    @staticmethod
    def create(
        username: str,
        password: str,
        email: str,
        nombre_completo: str,
        rol: str
    ) -> Optional[int]:
        ...
```

### 4.2 Test Structure
```
tests/
├── conftest.py              # Pytest fixtures
├── test_models.py           # Unit tests for models
├── test_auth.py             # Auth route tests
├── test_chatbot.py          # Chatbot tests
├── test_chatbot_tools.py    # Tool execution tests
└── integration/
    └── test_api.py          # Full API integration tests
```

### 4.3 Example Tests
```python
# tests/test_models.py
import pytest
from models import User, Employee

class TestUser:
    def test_create_user(self, db_session):
        user_id = User.create(
            username="testuser",
            password="SecurePass123!",
            email="test@example.com",
            nombre_completo="Test User",
            rol="empleado"
        )
        assert user_id is not None

        user = User.get_by_id(user_id)
        assert user['username'] == "testuser"
        assert user['email'] == "test@example.com"

    def test_password_validation(self):
        with pytest.raises(ValueError):
            User.validate_password("weak")  # Too short
```

### 4.4 CI/CD Pipeline
```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      mysql:
        image: mysql:5.7
        env:
          MYSQL_ROOT_PASSWORD: test
          MYSQL_DATABASE: test_db
        ports:
          - 3306:3306

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov flake8 mypy

      - name: Lint
        run: flake8 . --max-line-length=120

      - name: Type check
        run: mypy . --ignore-missing-imports

      - name: Test
        run: pytest --cov=. --cov-report=xml
        env:
          DB_HOST: localhost
          DB_USER: root
          DB_PASSWORD: test
          DB_NAME: test_db
```

### 4.5 Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        language_version: python3.10

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=120]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
```

**Deliverables Phase 4:**
- [ ] 80%+ test coverage on models
- [ ] CI pipeline passing
- [ ] Type hints on all public methods
- [ ] Pre-commit hooks configured

---

## Phase 5: Features & UX (Week 9-12)

**Goal**: Complete enterprise-ready feature set.

### 5.1 Two-Factor Authentication (2FA)
```python
# modules/auth/totp.py
import pyotp
import qrcode
from io import BytesIO

class TOTPManager:
    @staticmethod
    def generate_secret() -> str:
        return pyotp.random_base32()

    @staticmethod
    def get_qr_code(username: str, secret: str) -> bytes:
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(username, issuer_name="AIntranet")

        qr = qrcode.make(uri)
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        return buffer.getvalue()

    @staticmethod
    def verify(secret: str, code: str) -> bool:
        totp = pyotp.TOTP(secret)
        return totp.verify(code)
```

### 5.2 Password Reset
```python
# Flow:
# 1. User requests reset → generate token, store in DB
# 2. Send email with reset link
# 3. User clicks link → verify token, show reset form
# 4. User submits new password → update, invalidate token

class PasswordReset:
    TOKEN_EXPIRY = timedelta(hours=1)

    @staticmethod
    def create_token(user_id: int) -> str:
        token = secrets.token_urlsafe(32)
        expiry = datetime.now() + PasswordReset.TOKEN_EXPIRY
        query = """
            INSERT INTO password_resets (user_id, token, expires_at)
            VALUES (%s, %s, %s)
        """
        execute_query(query, (user_id, token, expiry))
        return token
```

### 5.3 Granular RBAC
```python
# models.py - New permission system
class Permission:
    VIEW_EMPLOYEES = 'view_employees'
    EDIT_EMPLOYEES = 'edit_employees'
    VIEW_VACATIONS = 'view_vacations'
    APPROVE_VACATIONS = 'approve_vacations'
    VIEW_TICKETS = 'view_tickets'
    MANAGE_TICKETS = 'manage_tickets'
    VIEW_COBRANZAS = 'view_cobranzas'
    ADMIN_USERS = 'admin_users'

ROLE_PERMISSIONS = {
    'admin': [Permission.VIEW_EMPLOYEES, Permission.EDIT_EMPLOYEES, ...],  # All
    'rrhh': [Permission.VIEW_EMPLOYEES, Permission.VIEW_VACATIONS, Permission.APPROVE_VACATIONS],
    'soporte': [Permission.VIEW_TICKETS, Permission.MANAGE_TICKETS],
    'empleado': [Permission.VIEW_EMPLOYEES, Permission.VIEW_VACATIONS],  # Own only
}

def has_permission(user_role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(user_role, [])
```

### 5.4 API Authentication (JWT)
```python
# modules/api/__init__.py
from flask_jwt_extended import JWTManager, create_access_token, jwt_required

jwt = JWTManager(app)

@api_bp.route('/auth/token', methods=['POST'])
def get_token():
    username = request.json.get('username')
    password = request.json.get('password')

    user = User.verify_credentials(username, password)
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    token = create_access_token(identity=user['id'])
    return jsonify({'access_token': token})

@api_bp.route('/employees')
@jwt_required()
def api_employees():
    return jsonify(Employee.get_all_paginated())
```

### 5.5 Webhook System
```python
# modules/webhooks/models.py
class Webhook:
    EVENTS = ['ticket.created', 'vacation.approved', 'user.created']

    @staticmethod
    def trigger(event: str, payload: dict):
        webhooks = Webhook.get_by_event(event)
        for webhook in webhooks:
            # Queue async HTTP POST
            send_webhook.delay(webhook['url'], payload, webhook['secret'])

# Usage in routes:
def create_ticket():
    ticket_id = Ticket.create(...)
    Webhook.trigger('ticket.created', {'ticket_id': ticket_id, ...})
```

### 5.6 OpenAPI Documentation
```python
# Using Flask-RESTX or flasgger
from flasgger import Swagger

swagger_config = {
    "headers": [],
    "specs": [{
        "endpoint": 'apispec',
        "route": '/apispec.json',
    }],
    "title": "AIntranet API",
    "version": "1.0.0",
}

swagger = Swagger(app, config=swagger_config)
```

**Deliverables Phase 5:**
- [ ] 2FA enrollment flow working
- [ ] Password reset via email working
- [ ] JWT API authentication
- [ ] Swagger docs at /api/docs

---

## Phase 6: DevOps & Monitoring (Week 13-14)

**Goal**: Production-ready infrastructure.

### 6.1 Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DB_HOST=db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  db:
    image: mysql:5.7
    volumes:
      - mysql_data:/var/lib/mysql
    environment:
      - MYSQL_ROOT_PASSWORD=${DB_PASSWORD}
      - MYSQL_DATABASE=${DB_NAME}

  redis:
    image: redis:alpine

  celery:
    build: .
    command: celery -A tasks worker --loglevel=info
    depends_on:
      - redis

volumes:
  mysql_data:
```

### 6.2 Health Checks
```python
# app.py
@app.route('/health')
def health_check():
    """Kubernetes liveness probe"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/ready')
def readiness_check():
    """Kubernetes readiness probe - checks dependencies"""
    checks = {
        'database': check_db_connection(),
        'redis': check_redis_connection(),
    }

    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503

    return jsonify({
        'status': 'ready' if all_healthy else 'not ready',
        'checks': checks
    }), status_code
```

### 6.3 Prometheus Metrics
```python
# metrics.py
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

LLM_TOKENS_USED = Counter(
    'llm_tokens_total',
    'Total LLM tokens consumed',
    ['model', 'type']  # type: prompt or completion
)

@app.route('/metrics')
def metrics():
    return generate_latest()
```

### 6.4 Alembic Migrations
```bash
# Setup
pip install alembic
alembic init migrations
```

```python
# migrations/env.py
from config import Config
config.set_main_option('sqlalchemy.url',
    f"mysql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}/{Config.DB_NAME}")
```

```bash
# Create migration
alembic revision --autogenerate -m "add_audit_log_table"

# Run migrations
alembic upgrade head
```

### 6.5 Backup Strategy
```bash
#!/bin/bash
# scripts/backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/backups

# Database backup
mysqldump -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Upload to S3
aws s3 cp $BACKUP_DIR/db_$DATE.sql.gz s3://aintranet-backups/

# Keep only last 30 days locally
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

### 6.6 LLM Cost Tracking
```python
# modules/chatbot/cost_tracker.py
class LLMCostTracker:
    # GPT-5.1 pricing (example)
    COST_PER_1K_TOKENS = {
        'gpt-5.1': {'input': 0.01, 'output': 0.03},
        'gpt-4o': {'input': 0.005, 'output': 0.015},
    }

    @staticmethod
    def track_usage(model: str, input_tokens: int, output_tokens: int, user_id: int):
        cost = (
            (input_tokens / 1000) * LLMCostTracker.COST_PER_1K_TOKENS[model]['input'] +
            (output_tokens / 1000) * LLMCostTracker.COST_PER_1K_TOKENS[model]['output']
        )

        query = """
            INSERT INTO llm_usage (user_id, model, input_tokens, output_tokens, cost, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """
        execute_query(query, (user_id, model, input_tokens, output_tokens, cost))

        # Alert if daily cost exceeds threshold
        daily_cost = LLMCostTracker.get_daily_cost()
        if daily_cost > 100:  # $100/day threshold
            send_alert(f"LLM daily cost alert: ${daily_cost:.2f}")
```

**Deliverables Phase 6:**
- [ ] Docker images building
- [ ] Health checks passing
- [ ] Prometheus metrics exposed
- [ ] Alembic migrations working
- [ ] Automated backups running
- [ ] LLM cost dashboard

---

## Success Metrics

| Metric | Current | Target | Timeline |
|--------|---------|--------|----------|
| Security vulnerabilities | 8 critical | 0 | Week 2 |
| Response time (p95) | Unknown | <500ms | Week 6 |
| Test coverage | 0% | 80% | Week 8 |
| Uptime | Unknown | 99.9% | Week 14 |
| Concurrent users | ~50 | 500+ | Week 6 |

---

## Resource Requirements

### Team
- 1 Senior Backend Developer (full-time)
- 1 Mid-level Developer (full-time)
- 1 DevOps Engineer (part-time, Phases 1 & 6)

### Infrastructure
- CI/CD: GitHub Actions (free tier)
- Monitoring: Prometheus + Grafana (self-hosted)
- Background jobs: Redis + Celery
- Backups: S3 or equivalent

### Budget Estimate
| Item | Monthly Cost |
|------|--------------|
| Additional cloud resources | $50-100 |
| Monitoring tools | $0 (self-hosted) |
| LLM API (with limits) | $200-500 |
| **Total** | **$250-600/month** |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Security breach before fixes | Phase 1 is non-negotiable, block production deploy |
| Performance degradation during migration | Implement feature flags, gradual rollout |
| Test suite slowing development | Focus on critical paths first, expand gradually |
| LLM costs spike | Implement hard limits, user quotas in Phase 6 |

---

## Next Steps

1. **This week**: Begin Phase 1 immediately
2. **Review**: Weekly progress meetings
3. **Documentation**: Update CLAUDE.md as changes are made
4. **Communication**: Share roadmap with stakeholders

---

*Document version: 1.0*
*Last updated: 2026-02-05*
*Author: CTO (AI-assisted analysis)*
