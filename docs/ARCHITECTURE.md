# CFBC System Architecture

## Overview

The CFBC (Centro Fray Bartolomé de las Casas) platform is a Django-based educational management system designed to handle **1000+ concurrent users**. It provides course management, document sharing, blog/publishing, evaluations, and administrative tools for an educational institution.

## Technology Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Web Framework** | Django | 5.2.7 | Full-stack web framework |
| **Database** | PostgreSQL | 16 | Primary data store |
| **Cache & Sessions** | Redis | 7 | Caching, sessions, Celery broker |
| **Task Queue** | Celery | 5.4+ | Async/background task processing |
| **WSGI Server** | Gunicorn | 22+ | Production WSGI server |
| **Load Balancer** | Nginx | 1.25 | Reverse proxy, SSL, rate limiting |
| **Frontend** | Tailwind CSS | 3.x | Utility-first CSS framework |
| **Message Broker** | Redis | 7 | Celery broker + result backend |
| **CI/CD Quality** | pre-commit | 5.x | Security scanning, linting |

## Architecture Diagram

```
                         ┌──────────────────────────────────────┐
                         │          Users / Clients             │
                         └────────────────┬─────────────────────┘
                                          │
                                  HTTPS :443
                                          │
                    ┌─────────────────────▼─────────────────────┐
                    │         Nginx (Load Balancer)             │
                    │                                           │
                    │  • SSL Termination (TLSv1.2/1.3)           │
                    │  • Rate Limiting (100r/s general, 5r/m    │
                    │    login, 30r/m API)                      │
                    │  • Static Files Cache (30d immutable)     │
                    │  • Media Files Cache (7d)                 │
                    │  • Passive Health Checks (max_fails=3)    │
                    │  • ip_hash Session Affinity               │
                    │  • Security Headers (HSTS, CSP, X-Frame)  │
                    └──┬──────┬──────┬──────┬───────────────────┘
                       │      │      │      │
                  :8001│  :8002│  :8003│  :8004│
             ┌─────────┐┌────────┐┌────────┐┌────────┐
             │Gunicorn ││Gunicorn││Gunicorn││Gunicorn│
             │ Inst 1  ││ Inst 2 ││ Inst 3 ││ Inst 4 │
             │ (4 work)││ (4 work)││ (4 work)││ (4 work)│
             └─────────┘└────────┘└────────┘└────────┘
                       │      │      │      │
                       └──────┴──────┴──────┘
                                  │
                    ┌─────────────▼───────────────────────────┐
                    │         Shared Resources                │
                    │                                         │
                    │  ┌──────────┐   ┌──────────────────┐   │
                    │  │PostgreSQL│   │    Redis 7        │   │
                    │  │ Primary  │   │  • DB 1: Cache    │   │
                    │  │ (r/w)    │   │  • DB 2: Sessions  │   │
                    │  │ ──────── │   │  • DB 3: Celery    │   │
                    │  │ Replica  │   │  • DB 4: Results   │   │
                    │  │ (read)   │   └──────────────────┘   │
                    │  └──────────┘                          │
                    │                                         │
                    │  ┌─────────────┐  ┌────────────────┐   │
                    │  │  Celery     │  │  Celery Beat   │   │
                    │  │  Workers    │  │  (Scheduler)   │   │
                    │  │  (5 queues) │  │  (Periodic)    │   │
                    │  └─────────────┘  └────────────────┘   │
                    └─────────────────────────────────────────┘
```

## Application Layer

### Middleware Pipeline (Execution Order)

```
 1. SecurityMiddleware           → Django security (HSTS, SSL redirect)
 2. SessionMiddleware             → Redis-backed session management
 3. CommonMiddleware              → URL normalization, redirects
 4. CsrfViewMiddleware            → CSRF token validation
 5. AuthenticationMiddleware      → User authentication
 6. MessageMiddleware             → Django messages framework
 7. XFrameOptionsMiddleware        → Clickjacking protection
 ─────────────────────────────────────────────────────
 8. SecurityHeadersMiddleware     → CSP, HSTS, X-Frame-Options, etc.
 9. RateLimitMiddleware           → IP-based rate limiting (login, API)
10. SecurityAuditMiddleware       → Security event logging & sanitization
11. CacheControlMiddleware        → Browser caching headers optimization
12. CorrelationIdMiddleware       → Distributed tracing (X-Request-ID)
13. RequestTimingMiddleware       → APM: request timing, DB metrics
14. StructuredLoggingMiddleware   → JSON structured log context
15. DatabaseMonitoringMiddleware  → Query timeout, pool monitoring
```

### Django Applications (INSTALLED_APPS)

| App | Purpose | Key Models |
|---|---|---|
| `principal` | Core courses, enrollments, users | `Curso`, `Matriculas`, `CursoAcademico` |
| `accounts` | User profiles, roles, registration | `Registro` (extends User) |
| `blog` | News/publishing system | `Noticia`, `Comentario`, `Categoria` |
| `course_documents` | Document management | `CourseDocument`, `DocumentFolder` |
| `evaluaciones` | Student evaluations | `Evaluacion`, `Pregunta` |
| `historial` | Academic history | Archived records |
| `datos_archivados` | Data archiving system | Archived course data |
| `task_management` | Task management UI | Task tracking |

## Database Architecture

### Connection Flow

```
Django App
    │
    ├── Primary (default) → Write operations, critical reads
    │   ├── CONN_MAX_AGE = 600s (10 min)
    │   ├── CONN_HEALTH_CHECKS = True
    │   ├── connect_timeout = 5s
    │   └── Pool: min=20, max=80 connections
    │
    └── Read Replica (read_replica) → Read-only queries
        ├── CONN_MAX_AGE = 600s
        ├── connect_timeout = 10s
        └── Enabled via USE_READ_REPLICA=True in .env
```

### Database Router Logic (`cfbc/db_router.py`)

- **`AdaptiveRouter`**: Routes reads to replica when healthy, falls back to primary
- **Write-through models**: `AuditLog`, `DocumentAccess`, `Calificaciones`, `Asistencia`, `Matriculas` always use primary
- **PgBouncer**: Optional connection pooling via `USE_PGBOUNCER=True`

### Query Timeouts

| Operation | Timeout | Description |
|---|---|---|
| List views | 10s | Blog listing, course lists |
| Detail views | 5s | Single item views |
| Search | 15s | Full-text search queries |
| Reports | 60s | Analytics and report generation |
| Exports | 120s | Data export operations |
| Health checks | 2s | `/health/` endpoint queries |

## Caching Architecture

### Cache Layers

```
Layer 1: Browser Cache (CacheControlMiddleware)
├── Static files: 30 days (public, immutable)
├── Public HTML: 10 min (public, max-age=600)
├── Dynamic content: 5 min (public, max-age=300)
└── User-specific: No cache (private, no-store)

Layer 2: Redis Cache (django-redis)
├── DB 1: General cache (default TTL: 5 min)
│   ├── Blog posts: 5 min
│   ├── Categories: 1 hour
│   ├── Homepage: 10 min
│   └── Static pages: 24 hours
├── DB 2: Sessions (24 hour TTL)
└── DB 4: Celery results (24 hour TTL)

Layer 3: Template Fragment Cache (cache_fragment tag)
├── Header: 1 hour
├── Footer: 24 hours
├── Sidebar: 10 min
└── News list: 5 min

Layer 4: PostgreSQL Shared Buffers
└── Cache hit ratio target: > 95%
```

### Cache Features

| Feature | Implementation | Description |
|---|---|---|
| Versioning | `CacheVersion` class | 8 groups (noticias, categorias, cursos, etc.) |
| Stampede Protection | `stampede_protect` decorator | Distributed lock for cache regeneration |
| Cache Warming | Celery task (every 30 min) | Pre-loads frequent queries |
| Health Check | Celery task (every 5 min) | Tests set/get/delete operations |
| Metrics | `CacheMetrics` class | Tracks hit/miss ratio |

## Async Processing (Celery)

### Queue Architecture

```
         ┌──────────┐
         │  Tasks   │
         └────┬─────┘
              │
    ┌─────────┴──────────────────┐
    │    Celery Router           │
    │    (by task name)          │
    └────┬────┬────┬────┬───────┘
         │    │    │    │
    ┌────▼┐┌──▼──┐┌▼───┐┌▼───────┐
    │Email││File ││Rpt ││Default │
    │  4w ││  2w ││ 1w ││  2w    │
    └─────┘└─────┘└────┘└────────┘
```

| Queue | Priority | Workers | Tasks | Max Time |
|---|---|---|---|---|
| `email` | 8 (high) | 4 | `send_welcome_email`, `send_comment_notification` | 30s |
| `file_processing` | 6 (med-high) | 2 | `process_uploaded_document` | 5 min |
| `reports` | 3-5 (medium) | 1 | `generate_folder_report`, `generate_performance_report` | 10-15 min |
| `default` | 5 (medium) | 2 | Mixed workload | 30 min |
| `maintenance` | 1 (low) | 1 | `cleanup_old_documents` | 30 min |
| `backup` | 2 (low) | 1 | `backup_document_metadata` | 30 min |

## Security Architecture

### Defense in Depth

```
Layer 1: Network (Nginx)
├── SSL/TLS (TLSv1.2/1.3, strong ciphers)
├── Rate limiting (100r/s general, 5r/m login)
├── Security headers (HSTS, CSP, X-Frame-Options)
├── Request size limits (60MB max upload)
└── Block hidden/sensitive file access

Layer 2: Django Application
├── SecurityHeadersMiddleware (CSP, HSTS, X-Frame)
├── RateLimitMiddleware (login 5/m, API 30/m, upload 10/m)
├── SecurityAuditMiddleware (event logging + sanitization)
├── CSRF protection (CsrfViewMiddleware)
├── XSS protection (template auto-escaping)
└── Session security (Redis-backed, HttpOnly cookies)

Layer 3: File Storage (course_documents)
├── FileSecurityMiddleware (upload validation)
├── SecurityService (MIME/extension validation)
├── Dangerous file type blocking
└── File size limits (50MB max)

Layer 4: Monitoring & Detection
├── SecurityAuditMiddleware (probe scan detection)
├── AlertManager (16 alert rules, 3 channels)
├── Structured logging with correlation IDs
└── Pre-commit hooks (Bandit, detect-secrets)
```

## Monitoring Stack

### Components

| Component | Purpose | Endpoint/File |
|---|---|---|
| Health Checks | Service availability | GET `/health/` |
| Prometheus Metrics | Performance metrics | GET `/metrics/` |
| JSON Summary | Aggregated metrics | GET `/metrics/summary/` |
| APM Middleware | Request timing, DB tracking | `RequestTimingMiddleware` |
| Structured Logging | JSON logs with correlation IDs | `logs/*.log` |
| Alerting System | Threshold-based alerts | `AlertManager` (16 rules) |
| Business Metrics | Domain KPIs in Redis | `cfbc.business_metrics` |
| Performance Analysis | Bottleneck detection | `python manage.py analyze_performance` |
| Security Audit | Security configuration check | `python manage.py security_audit` |

### Log Files

| File | Content | Retention |
|---|---|---|
| `logs/monitoring.log` | General application logs (INFO+) | 5 × 10MB rotations |
| `logs/performance.log` | Slow queries, performance warnings | 5 × 10MB rotations |
| `logs/errors.log` | ERROR+ level logs | 10 × 10MB rotations |
| `logs/alerts.log` | Alert events | 10 × 10MB rotations |
| `logs/autoscale.log` | Auto-scaling events | N/A |

## Scalability & Performance

### Auto-Scaling

| Metric | Scale Up Trigger | Scale Down Trigger |
|---|---|---|
| CPU Usage | > 70% | < 30% |
| Memory Usage | > 75% | < 40% |
| Request Rate | > 50 req/s per instance | < 10 req/s |
| P95 Response Time | > 1 second | < 0.3 seconds |
| Queue Depth | > 10 waiting | < 3 waiting |

- **Decision**: Weighted majority (3/5 metrics must agree)
- **Cooldown**: 120s up, 300s down
- **Instances**: 2 min, 8 max (configurable)

### Performance Targets

| Metric | Target | Measured By |
|---|---|---|
| P95 Page Load | < 2s | RequestTimingMiddleware |
| P95 DB Query | < 100ms | SlowQueryLogger |
| Cache Hit Ratio | > 80% | CacheMetrics |
| Throughput | > 100 req/s | RequestTimingMiddleware |
| Error Rate | < 1% | RequestTimingMiddleware |

## Deployment

### Docker Compose (Production)

```bash
# Full stack deployment
docker compose -f deploy/docker-compose.prod.yml up -d

# Services:
#   - nginx (load balancer, SSL)
#   - app-1..app-4 (Gunicorn/Django instances)
#   - postgres (PostgreSQL 16)
#   - redis (Redis 7)
#   - celery-worker (general tasks)
#   - celery-file-worker (file processing)
#   - celery-beat (scheduler)
```

### Systemd (Bare Metal)

```bash
# Gunicorn instances on ports 8001-8004
# Nginx reverse proxy on ports 80/443
# Managed via systemd services
```

## Related Documentation

| Document | Location | Description |
|---|---|---|
| Monitoring Stack | `docs/monitoring_stack.md` | APM, logging, alerting details |
| Auto-Scaling | `docs/auto_scaling.md` | Auto-scaling configuration and runbooks |
| Database Scaling | `docs/database_scaling.md` | Database clustering and failover |
| Celery Setup | `docs/celery_setup.md` | Async task processing setup |
| Load Balancer | `docs/load_balancer.md` | Nginx load balancer configuration |
| Operations Runbook | `docs/OPS_RUNBOOK.md` | Operational procedures |
| Troubleshooting | `docs/TROUBLESHOOTING.md` | Problem diagnosis guides |
| Maintenance | `docs/MAINTENANCE.md` | Maintenance schedule |
| Performance Tests | `cfbc/tests_performance_regression.py` | 24 regression tests |
| Load Tests | `locustfile.py` | Locust load test scenarios |
