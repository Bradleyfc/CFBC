# Comprehensive Monitoring Stack

## Overview

This document describes the comprehensive monitoring stack implemented for the CFBC platform. The stack covers:

1. **APM (Application Performance Monitoring)** - Request timing, DB query tracking
2. **Structured Logging** - JSON-formatted logs with correlation IDs
3. **Health & Metrics Endpoints** - `/health/` and `/metrics/` endpoints
4. **Alerting System** - Threshold-based alerts with multiple channels
5. **Business Metrics** - Domain-specific KPIs tracked in Redis
6. **Log Aggregation** - Preparing logs for ELK/Loki/Grafana

---

## 1. Architecture

```
┌────────────────────────────────────────────────────────┐
│                    Django Application                   │
│                                                        │
│  CorrelationIdMiddleware → RequestTimingMiddleware     │
│                             ↓                          │
│  StructuredLoggingMiddleware                           │
│         ↓                                              │
│  DatabaseMonitoringMiddleware (existing)               │
│         ↓                                              │
│                    Views/APIs                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │
│  │ /health/ │  │ /metrics/│  │ /metrics/summary/ │    │
│  └──────────┘  └──────────┘  └──────────────────┘    │
│                                                        │
│  ┌──────────────┐  ┌───────────────┐  ┌────────────┐ │
│  │ AlertManager │  │ BusinessMetrics│  │ AutoScaler │ │
│  └──────────────┘  └───────────────┘  └────────────┘ │
│         ↓                 ↓                  ↓        │
│  ┌──────────────────────────────────────────────┐    │
│  │              Redis / Logs / Email            │    │
│  └──────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────┘
```

## 2. Middleware Pipeline

The middleware stack (in order):

| Middleware | Purpose | Position |
|---|---|---|
| `SecurityMiddleware` | Django security | 1 |
| `SessionMiddleware` | Session handling | 2 |
| `CommonMiddleware` | URL normalization | 3 |
| `CsrfViewMiddleware` | CSRF protection | 4 |
| `AuthenticationMiddleware` | User auth | 5 |
| `MessageMiddleware` | Messages framework | 6 |
| `XFrameOptionsMiddleware` | Clickjacking protection | 7 |
| **`CorrelationIdMiddleware`** | Distributed tracing | **8** |
| **`RequestTimingMiddleware`** | APM timing & DB metrics | **9** |
| **`StructuredLoggingMiddleware`** | JSON log context | **10** |
| `DatabaseMonitoringMiddleware` | DB pool & timeouts | 11 |

### 2.1 CorrelationIdMiddleware

Adds a unique `X-Request-ID` header to every request/response for distributed tracing.

**Behavior:**
- Reads existing `X-Request-ID` from incoming request (when behind a proxy)
- Generates a new UUID if none exists
- Makes ID available on `request.correlation_id`
- Adds `X-Request-ID` and `X-Response-Time` headers to response

**Usage in views:**
```python
def my_view(request):
    cid = request.correlation_id
    logger.info(f"Processing request {cid}")
```

### 2.2 RequestTimingMiddleware

Tracks per-request APM metrics and stores them in Redis for aggregation.

**Tracked metrics:**
- Total request duration
- Database query count and total time
- Response status code distribution
- Path-normalized request counts

**Redis keys (auto-expire after 1 hour):**
- `cfbc:metrics:requests:{minute}` - Request counts per path
- `cfbc:metrics:duration:{minute}` - Duration sum/count per path
- `cfbc:metrics:status:{minute}` - Status code group counts
- `cfbc:metrics:db:{minute}` - DB query counts and times

**Logs warnings when:**
- Request takes > 2 seconds (`SLOW REQUEST`)
- Request uses > 30 DB queries (`HIGH DB QUERIES`)

### 2.3 StructuredLoggingMiddleware

Adds structured context to every log record within a request.

**Context added to each log record:**
- `correlation_id`
- `user_id` and `username` (if authenticated)
- `path`, `method`
- `client_ip`
- `user_agent` and `referer`
- `status_code`, `duration_ms`, `content_length`

**Log levels by status code:**
- 5xx → `error()`
- 4xx → `warning()`
- 2xx/3xx → `info()`

---

## 3. Endpoints

### 3.1 `/health/` - Health Check

```bash
curl http://localhost:8000/health/
```

**Response:**
```json
{
  "status": "healthy",
  "instance_id": "app-1",
  "timestamp": "2026-07-13T12:00:00Z",
  "checks": {
    "database": { "status": "ok" },
    "cache": { "status": "ok" }
  }
}
```

- Returns **200 OK** if all critical services are healthy
- Returns **503 Service Unavailable** if database is down
- Includes disk space and Celery checks when `HEALTH_CHECK_INCLUDE_DETAILS=True`

### 3.2 `/metrics/` - Prometheus Metrics

```bash
curl http://localhost:8000/metrics/
```

Returns metrics in Prometheus text format:
```
# HELP cfbc_health Django application health status
# TYPE cfbc_health gauge
cfbc_health{instance="app-1"} 1
# HELP cfbc_requests_total Total requests per endpoint
# TYPE cfbc_requests_total counter
cfbc_requests_total{path="/noticias/"} 42
cfbc_requests_total{path="/health/"} 150
# HELP cfbc_http_requests_total HTTP status codes
# TYPE cfbc_http_requests_total counter
cfbc_http_requests_total{status="2xx"} 180
cfbc_http_requests_total{status="5xx"} 2
```

**Prometheus integration:**
- Install `django-prometheus` for full Prometheus support
- Add to `INSTALLED_APPS` and `MIDDLEWARE`
- Use Prometheus + Grafana for dashboards

### 3.3 `/metrics/summary/` - JSON Summary

```bash
curl http://localhost:8000/metrics/summary/
```

Returns a JSON object with:
- Per-endpoint request counts (last minute)
- Average response times per endpoint
- Status code distribution
- Database connection count and size
- System load averages

---

## 4. Alerting System

### 4.1 Alert Rules

The `AlertManager` in `cfbc/alerting.py` comes with 16 pre-configured alert rules:

| Rule | Metric | Severity | Threshold | Channel |
|---|---|---|---|---|
| `high_cpu` | cpu_usage | warning | > 80% | log, file |
| `critical_cpu` | cpu_usage | critical | > 90% | log, file |
| `high_memory` | memory_usage | warning | > 85% | log, file |
| `critical_memory` | memory_usage | critical | > 95% | log, file, **email** |
| `slow_response_time` | avg_response_time | warning | > 2s | log, file |
| `critical_response_time` | avg_response_time | critical | > 5s | log, file, **email** |
| `high_error_rate` | error_rate | warning | > 5% | log, file |
| `critical_error_rate` | error_rate | critical | > 10% | log, file, **email** |
| `disk_space_warning` | disk_free_percent | warning | < 10% | log, file |
| `disk_space_critical` | disk_free_percent | critical | < 5% | log, file, **email** |
| `celery_queue_backlog` | celery_queue_depth | warning | > 100 | log, file |
| `celery_worker_down` | celery_workers | critical | < 1 | log, file, **email** |
| `high_db_connections` | db_connections | warning | > 80% | log, file |
| `critical_db_connections` | db_connections | critical | > 95% | log, file, **email** |
| `high_request_rate` | request_rate | warning | > 100 rps | log, file |

### 4.2 Alert Channels

| Channel | Description | Configuration |
|---|---|---|
| `log` | Logs at appropriate level (info/warning/critical) | Automatic |
| `file` | Writes JSON to `logs/alerts.log` | `ALERT_LOG_FILE` env var |
| `email` | Sends email for critical alerts | `ALERT_EMAIL_RECIPIENTS` env var |

### 4.3 Alert Features

- **Deduplication**: Configurable cooldown per rule (default 5 min)
- **Duration-based**: Alerts only fire when condition persists for N seconds
- **Escalation**: Critical alerts that remain unacknowledged for 15 minutes escalate
- **Acknowledgment**: Alerts can be acknowledged via `AlertManager.acknowledge_alert()`
- **History**: Last 1000 alerts stored in memory, queryable via `get_alert_history()`

### 4.4 Usage

```python
from cfbc.alerting import get_alert_manager

manager = get_alert_manager()

# Check a metric value against all rules
events = manager.check_and_alert(
    metric_name='cpu_usage',
    value=85.0,
    instance_id='app-1',
)

# Get active (unacknowledged) alerts
active = manager.get_active_alerts()

# Get alert history
history = manager.get_alert_history(limit=50)
```

### 4.5 Alerting Endpoint

A management command to view alerts:
```bash
python manage.py autoscale --alerts
```

---

## 5. Business Metrics

### 5.1 Tracked KPIs

The `cfbc/business_metrics.py` module tracks:

| Domain | Metrics |
|---|---|
| **Users** | Total users, by role (estudiante/profesor/admin), active today |
| **Courses** | Active courses, total courses, archived courses, enrollments |
| **Documents** | Total documents, folders, storage size (bytes/MB), recent uploads (7d) |
| **Blog** | Total posts, published posts, total comments |
| **Evaluations** | Total evaluations, total questions |
| **Registrations** | Today, this week, this month (from Redis) |

### 5.2 Recording Events

```python
from cfbc.business_metrics import (
    record_user_registration,
    record_document_upload,
    record_document_download,
    record_evaluation_response,
    record_blog_comment,
)

# In your views/signals:
record_user_registration(rol='estudiante')
record_document_upload(curso_id=1, file_size=1024000)
record_document_download(curso_id=1, student_id=42)
```

### 5.3 Redis Storage

Business metrics are stored in Redis with automatic TTLs:
- Minutely data: 1 hour (for real-time dashboards)
- Hourly data: 7 days (for trends)
- Daily data: 90 days (for historical analysis)

Keys follow the pattern: `cfbc:biz:{metric_name}:{period}:{date}`

---

## 6. Log Aggregation

### 6.1 Structured JSON Logging

All logs are written in JSON format when `LOG_STRUCTURED_TO_FILE=True` (default).

**Log files:**

| File | Purpose | Retention |
|---|---|---|
| `logs/monitoring.log` | General application logs (INFO+) | 5 rotations × 10MB |
| `logs/performance.log` | Slow queries and performance warnings | 5 rotations × 10MB |
| `logs/errors.log` | ERROR+ level logs | 10 rotations × 10MB |
| `logs/alerts.log` | Alert events (WARNING+) | 10 rotations × 10MB |

**JSON log format:**
```json
{
  "timestamp": "2026-07-13T12:00:00.000Z",
  "level": "INFO",
  "logger": "cfbc.middleware",
  "module": "middleware",
  "function": "__call__",
  "line": 123,
  "message": "Request completed",
  "correlation_id": "a1b2c3d4-...",
  "user_id": 42,
  "username": "jdoe",
  "path": "/noticias/",
  "method": "GET",
  "status_code": 200,
  "duration_ms": 150.2
}
```

### 6.2 ELK/Loki Stack Setup

To set up log aggregation with ELK or Loki+Grafana:

1. **Ensure logs directory exists:**
   ```bash
   mkdir -p logs
   ```

2. For **ELK Stack (Elasticsearch + Logstash + Kibana)**:
   - Configure Filebeat to tail `logs/*.log`
   - Use JSON codec in Logstash
   - Create Kibana index pattern for `cfbc-*`

3. For **Loki + Grafana**:
   - Install Promtail
   - Configure Promtail to scrape `logs/*.log`
   - Use `--json` pipeline stage in Promtail config

4. For **Sentry** (error tracking):
   ```bash
   pip install sentry-sdk
   ```
   Configure in `settings.py`:
   ```python
   import sentry_sdk
   sentry_sdk.init(
       dsn=os.getenv('SENTRY_DSN'),
       integrations=[DjangoIntegration()],
       traces_sample_rate=0.5,
       environment=os.getenv('ENVIRONMENT', 'production'),
   )
   ```

---

## 7. Grafana Dashboard Recommendations

### 7.1 Application Overview Dashboard

Panels:
- **Request Rate** (QPS) - Last 1 hour (graph)
- **P95 Response Time** - Last 1 hour (graph)
- **Error Rate (%)** - Last 1 hour (graph)
- **Active Users** - Gauge
- **Status Code Distribution** - Pie chart
- **Slowest Endpoints** - Table (top 10)

### 7.2 Business KPIs Dashboard

Panels:
- **User Growth** - Cumulative graph (30d)
- **Course Enrollment Trends** - Bar chart (30d)
- **Document Uploads** - Graph (7d)
- **Storage Usage** - Gauge / Area graph
- **Active Courses** - Stat
- **Blog Activity** - Bar chart (posts + comments)

### 7.3 System Health Dashboard

Panels:
- **CPU Usage** - Graph (all instances)
- **Memory Usage** - Graph (all instances)
- **DB Connections** - Graph
- **Celery Queue Depth** - Graph
- **Disk Space** - Gauge
- **Alert History** - Table (last 50 events)

### 7.4 Prometheus Queries

```promql
# Request rate
rate(cfbc_requests_total[5m])

# P95 response time (requires histograms)
histogram_quantile(0.95, rate(cfbc_request_duration_seconds_bucket[5m]))

# Error rate
rate(cfbc_http_requests_total{status=~"5xx"}[5m]) / rate(cfbc_requests_total[5m]) * 100

# Active users
cfbc_users_active_today

# Storage growth
rate(cfbc_documents_storage_bytes[7d])

# Database connections
cfbc_db_connections_active
```

---

## 8. Environment Variables

| Variable | Default | Description |
|---|---|---|
| `LOG_STRUCTURED_TO_FILE` | `True` | Enable structured JSON logging |
| `BUSINESS_METRICS_ENABLED` | `True` | Enable business metrics recording |
| `ALERT_LOG_FILE` | `logs/alerts.log` | Alert log file path |
| `ALERT_HISTORY_SIZE` | `1000` | Max alert history entries |
| `ALERT_EMAIL_RECIPIENTS` | `admin@cfbc.edu.ni` | Comma-separated email recipients |
| `HEALTH_CHECK_INCLUDE_DETAILS` | `False` | Include disk/Celery in health check |
| `PERFORMANCE_LOG_FILE` | `logs/performance.log` | Performance log file path |
| `MONITORING_LOG_FILE` | `logs/monitoring.log` | Monitoring log file path |
| `ERROR_LOG_FILE` | `logs/errors.log` | Error log file path |

---

## 9. Quick Start

```bash
# 1. Ensure logs directory exists
mkdir -p logs

# 2. Verify monitoring endpoints
curl http://localhost:8000/health/
curl http://localhost:8000/metrics/
curl http://localhost:8000/metrics/summary/

# 3. Check alert status
python manage.py autoscale --alerts

# 4. Install Prometheus (optional)
pip install django-prometheus

# 5. Set up Grafana (optional)
# Add Prometheus data source pointing to Django /metrics/
# Import dashboard JSON from docs/grafana/ (see Grafana section)
```

---

## 10. Verification Checklist

- [ ] `/health/` returns 200 with `status: "healthy"`
- [ ] `/metrics/` returns Prometheus-formatted metrics
- [ ] `/metrics/summary/` returns JSON with request counts
- [ ] Correlation IDs (`X-Request-ID`) present in response headers
- [ ] Response time headers (`X-Response-Time`) present
- [ ] JSON logs written to `logs/monitoring.log`
- [ ] Performance logs written to `logs/performance.log` for slow queries
- [ ] Error logs written to `logs/errors.log` for 5xx responses
- [ ] Business metrics stored in Redis (`cfbc:biz:*`)
- [ ] Alerting rules configured and ready
- [ ] Log rotation configured for all log files
