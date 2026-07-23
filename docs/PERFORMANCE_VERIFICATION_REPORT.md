
======================================================================
  PERFORMANCE METRICS VERIFICATION REPORT
======================================================================
  Host:     DESKTOP-ILL1MMK
  Django:   5.2.7.final.0
  Time:     2026-07-14T08:09:52.905292
  Status:   FAILED
======================================================================

  📋 LOAD CHECKS
  ──────────────────────────────────────────────────────────────────
    ❌ ❌ Locust Available: Locust not installed - cannot run load tests
         └─ Installed: False
    ✅ ✅ Load Test Script: OK
         └─ Exists: True
    ✅ ✅ Test Runner Script: OK
         └─ run_load_tests.sh: True
    ✅ ✅ Auto-Scaler Min Instances: OK
         └─ min_instances=2
    ✅ ✅ Auto-Scaler Max Instances: OK
         └─ max_instances=8
    ✅ ✅ Pool Size vs Expected Load: OK
         └─ DB_POOL_MAX_SIZE=80 (recommended >= 80)
    ✅ ✅ Gunicorn Workers: OK
         └─ Configured in deploy/gunicorn/gunicorn.conf.py
    ℹ️ ℹ️ Theoretical Concurrent Capacity: Theoretical max ~160 concurrent requests (8 instances × 2 workers × 10)
         └─ For 1000+ users, scale to 8+ instances with deploy/scripts/scale_instances.sh

  📋 DATABASE CHECKS
  ──────────────────────────────────────────────────────────────────
    ✅ ✅ Database Engine: OK
         └─ Engine: django.db.backends.postgresql
    ✅ ✅ Connection Max Age: OK
         └─ CONN_MAX_AGE=600s
    ✅ ✅ Connection Health Checks: OK
         └─ CONN_HEALTH_CHECKS=True
    ✅ ✅ Connection Timeout: OK
         └─ connect_timeout=5
    ✅ ✅ Pool Min Size: OK
         └─ DB_POOL_MIN_SIZE=20
    ✅ ✅ Pool Max Size: OK
         └─ DB_POOL_MAX_SIZE=80
    ✅ ✅ Slow Query Threshold: OK
         └─ 500ms
    ✅ ✅ Operation Timeouts: OK
         └─ 6 operations configured
    ✅ ✅ Database Router: OK
         └─ Routers: ['cfbc.db_router.AdaptiveRouter']
    ✅ ✅ DB Monitoring Classes: OK
         └─ ConnectionPoolMonitor and SlowQueryLogger available
    ❌ ❌ Database Connectivity: Cannot connect to database: DatabaseWrapper objects created in a thread can only be used in that same thread. The object with alias 'default' was created in thread id 127442432561280 and this is thread id 127442288406656.

  📋 CACHE CHECKS
  ──────────────────────────────────────────────────────────────────
    ✅ ✅ Redis Cache Configured: OK
         └─ Caches: ['default', 'session', 'staticfiles']
    ✅ ✅ Cache Backend (Redis): OK
         └─ Backend: django_redis.cache.RedisCache
    ✅ ✅ Session Cache Backend (Redis): OK
         └─ Backend: django_redis.cache.RedisCache
    ✅ ✅ Session Engine (Cache): OK
         └─ SESSION_ENGINE=django.contrib.sessions.backends.cache
    ✅ ✅ Redis Connectivity: OK
         └─ Redis connected and responding
    ✅ ✅ Cache P95 Response Time: OK
         └─ P95=0.71ms, Avg=0.49ms, 100 ops
    ❌ ❌ Cache Hit Ratio: Cache hit ratio 0.0% below 80% target
         └─ Hit ratio: 0.0% (0 hits, 0 misses)
    ✅ ✅ Cache Version Groups: OK
         └─ 8 version groups configured: ['noticias', 'categorias', 'comentarios', 'cursos', 'documentos', 'evaluaciones', 'usuarios', 'general']
    ✅ ✅ TTL Configuration: OK
         └─ 5 TTLs configured: {'Static Page': 86400, 'News List': 300, 'Categories': 3600, 'Homepage': 600, 'Header Fragment': 3600}
    ✅ ✅ CacheControl Middleware: OK
         └─ Installed: True

  📋 CELERY CHECKS
  ──────────────────────────────────────────────────────────────────
    ✅ ✅ Celery Broker: OK
         └─ Broker: redis://127.0.0.1:6379/3
    ✅ ✅ Celery Result Backend: OK
         └─ Backend: redis://127.0.0.1:6379/4
    ✅ ✅ Task Queues: OK
         └─ Queues: ['backup', 'default', 'email', 'file_processing', 'maintenance', 'reports']
    ✅ ✅ Worker Concurrency: OK
         └─ Concurrency config: {'email': 4, 'file_processing': 2, 'reports': 1, 'default': 2, 'maintenance': 1, 'backup': 1}
    ✅ ✅ Task Time Limits: OK
         └─ Hard: 1800s, Soft: 1500s
    ✅ ✅ Result Expiry: OK
         └─ Results expire after 86400s (24h)
    ✅ ✅ Task Annotations: OK
         └─ 9 task annotations configured

  📋 MONITORING CHECKS
  ──────────────────────────────────────────────────────────────────
    ✅ ✅ APM Middleware (RequestTiming): OK
         └─ Installed: True
    ✅ ✅ Distributed Tracing (CorrelationId): OK
         └─ Installed: True
    ✅ ✅ Structured Logging: OK
         └─ Installed: True
    ✅ ✅ Security Audit Middleware: OK
         └─ Installed: True
    ✅ ✅ Health Check Endpoint: OK
         └─ URL: /health/
    ✅ ✅ Metrics Endpoints: OK
         └─ URLs: /metrics/, /metrics/summary/
    ✅ ✅ Alerting System: OK
         └─ 3 config keys: ['enabled', 'alert_log_file', 'alert_history_size']
    ✅ ✅ Business Metrics: OK
         └─ Enabled: True
    ✅ ✅ Log Files: OK
         └─ 4/4 log files exist: ['monitoring.log', 'performance.log', 'errors.log', 'alerts.log']
    ✅ ✅ Performance Analyzer: OK
         └─ python manage.py analyze_performance available
    ✅ ✅ Security Audit Command: OK
         └─ python manage.py security_audit available
    ✅ ✅ Performance Regression Tests: OK
         └─ File exists: True
    ✅ ✅ Operations Documentation: OK
         └─ Present: ['ARCHITECTURE.md', 'OPS_RUNBOOK.md', 'TROUBLESHOOTING.md', 'MAINTENANCE.md', 'monitoring_stack.md', 'auto_scaling.md']

  📋 REQUIREMENTS CHECKS
  ──────────────────────────────────────────────────────────────────
    ✅ ✅ SecurityHeaders (Req 8): OK
         └─ Present: True
    ✅ ✅ Rate Limiting (Req 8): OK
         └─ Present: True
    ✅ ✅ Security Audit (Req 8): OK
         └─ Present: True
    ✅ ✅ CSRF Protection: OK
         └─ Present: True
    ✅ ✅ Clickjacking Protection: OK
         └─ Present: True
    ✅ ✅ APM Middleware (Req 5): OK
         └─ Present: True
    ✅ ✅ Health Endpoint (Req 5): OK
         └─ Present: True
    ✅ ✅ Metrics Endpoint (Req 5): OK
         └─ Present: True
    ✅ ✅ Slow Query Logging (Req 5): OK
         └─ Present: True
    ✅ ✅ Redis Cache (Req 2): OK
         └─ Present: True
    ✅ ✅ Celery/Async (Req 3): OK
         └─ Present: True
    ✅ ✅ Database Indexing (Req 1): OK
         └─ Indexes created via migrations


  🎯 SUCCESS CRITERIA VERIFICATION
  ──────────────────────────────────────────────────────────────────
    ⚙️ Criterion 1: P95 page load time < 2s
       Status: configured
       Measured via RequestTimingMiddleware; database P95 verified in this report
       Verify: RequestTimingMiddleware logs + analyze_performance command
    ⚠️ Criterion 2: P95 DB query < 100ms
       Status: degraded
       No measurement available
       Verify: SlowQueryLogger + this report
    • Criterion 3: Cache hit ratio > 80%
       Status: fail
       ❌ Cache Hit Ratio: Cache hit ratio 0.0% below 80% target
       Verify: CacheMetrics.get_hit_ratio() + cache_operations command
    ⚙️ Criterion 4: Background tasks within SLA (email < 30s, reports < 5min)
       Status: configured
       Configured via CELERY_TASK_ANNOTATIONS with appropriate time limits
       Verify: Celery task monitoring in django-celery-results admin
    ⚙️ Criterion 5: Handle 1000+ concurrent users
       Status: configured
       ℹ️ Theoretical Concurrent Capacity: Theoretical max ~160 concurrent requests (8 instances × 2 workers × 10)
       Verify: Run ./run_load_tests.sh peak (locust) to measure actual performance
    ✅ Criterion 6: Monitoring provides actionable insights
       Status: passed
       APM, health checks, metrics, slow query logging, and structured logging all operational
       Verify: Verify /health/, /metrics/, /metrics/summary/ endpoints respond
    ✅ Criterion 7: All requirements implemented and verified
       Status: passed
       Security, monitoring, caching, async, and database requirements verified
       Verify: This verification report + tasks.md checklist

======================================================================
  SUMMARY: 61 checks
    ✅ 57 passed
    ❌ 3 failed
  Overall: FAILED
======================================================================
