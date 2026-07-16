# Troubleshooting Guide

## Quick Diagnosis

Run these commands in order when investigating an issue:

```bash
# 1. Check overall health
curl -s http://localhost:8000/health/ | python -m json.tool

# 2. Check performance metrics
curl -s http://localhost:8000/metrics/summary/ | python -m json.tool

# 3. Run performance analysis
python manage.py analyze_performance

# 4. Run security audit
python manage.py security_audit

# 5. Check error logs
tail -100 logs/errors.log | grep -E "CRITICAL|ERROR"
```

---

## 1. Application Issues

### 1.1 Django Returns 500 Error

**Symptoms:** Users see "500 Internal Server Error", health check fails.

**Possible Causes & Solutions:**

| Cause | Check | Solution |
|---|---|---|
| Database connection failed | `logs/errors.log` for OperationalError | Check PostgreSQL is running: `pg_isready` |
| Redis connection failed | `logs/errors.log` for ConnectionError | Restart Redis: `sudo systemctl restart redis-server` |
| Missing migration | `python manage.py showmigrations` | Run: `python manage.py migrate` |
| File permission issue | `logs/errors.log` for PermissionError | Check media/static file permissions: `chown -R www-data:www-data media/` |
| Code exception | `logs/errors.log` for traceback | Fix the code or rollback deployment |

**Diagnostic Steps:**
```bash
# Get the actual error
tail -50 logs/errors.log

# Check if DEBUG mode is on (should be False in production)
python manage.py shell -c "from django.conf import settings; print(settings.DEBUG)"

# Test database connectivity
python manage.py dbshell -c "SELECT 1;"

# Test cache connectivity
python manage.py shell -c "from django.core.cache import cache; cache.set('test','ok'); print(cache.get('test'))"
```

### 1.2 Django Returns 404

**Symptoms:** Users see "Page Not Found" on valid URLs.

**Possible Causes:**
- **Missing URL configuration**: Check `cfbc/urls.py` for the correct path
- **Static files not collected**: Run `python manage.py collectstatic`
- **DEBUG=False without ALLOWED_HOSTS**: Ensure ALLOWED_HOSTS includes the domain

**Diagnostic Steps:**
```bash
# Check ALLOWED_HOSTS
python manage.py shell -c "from django.conf import settings; print(settings.ALLOWED_HOSTS)"

# Check available URLs
python manage.py show_urls 2>/dev/null | grep -i <path>
```

### 1.3 Slow Page Loads

**Symptoms:** Pages take > 2 seconds to load, users complain about performance.

**Diagnostic Steps:**
```bash
# 1. Check performance analysis
python manage.py analyze_performance

# 2. Check slow queries in database
python manage.py shell -c "
from cfbc.db_monitoring import slow_query_logger
queries = slow_query_logger.get_recent_slow_queries(20)
for q in queries:
    print(f\"{q['duration_ms']}ms: {q['sql'][:100]}\")
"

# 3. Check cache hit ratio
python manage.py shell -c "
from cfbc.cache_utils import CacheMetrics
print(CacheMetrics.get_stats())
"

# 4. Check database connections
python manage.py shell -c "
from cfbc.db_monitoring import ConnectionPoolMonitor
print(ConnectionPoolMonitor.get_all_connections_summary())
"
```

**Solutions:**
1. Run cache warming: `python manage.py cache_operations --warm`
2. Increase DB pool size if pool utilization > 80%
3. Scale up instances if CPU/memory > 70%
4. Check for N+1 queries in views
5. Verify DB indexes are being used

---

## 2. Database Issues

### 2.1 "Too Many Connections" Error

**Symptoms:** `OperationalError: FATAL: too many connections for database`.

**Immediate Fix:**
```bash
# Kill idle connections
sudo -u postgres psql -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
  AND state_change < now() - interval '10 minutes'
  AND pid <> pg_backend_pid();
"

# Check current count
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"
```

**Permanent Fix:**
```bash
# Increase max_connections in postgresql.conf
# Edit /etc/postgresql/16/main/postgresql.conf:
#   max_connections = 200

# Or adjust connection pooling in pgbouncer.ini:
#   default_pool_size = 50
#   max_client_conn = 200
```

### 2.2 Slow Queries

**Symptoms:** Database query time > 500ms, general application slowness.

**Diagnostic:**
```bash
# Check slow query log
python manage.py shell -c "
from cfbc.db_monitoring import slow_query_logger
for q in slow_query_logger.get_recent_slow_queries(10):
    print(f\"[{q['duration_ms']}ms] {q['sql'][:200]}\")
"

# Check query execution plan (EXPLAIN ANALYZE)
python manage.py dbshell -c "
EXPLAIN ANALYZE SELECT * FROM blog_noticia WHERE estado = 'publicado' ORDER BY fecha_publicacion DESC LIMIT 20;
"

# Check for missing indexes
python manage.py dbshell -c "
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY tablename;
"
```

**Solutions:**
1. Add missing indexes based on analysis
2. Use `select_related`/`prefetch_related` for N+1 queries
3. Implement pagination for large result sets
4. Consider materialized views for complex aggregations

### 2.3 Replication Lag

**Symptoms:** Data inconsistency between primary and read replicas.

**Check:**
```bash
# Check lag on primary
sudo -u postgres psql -c "
SELECT client_addr, state,
  pg_wal_lsn_diff(pg_current_wal_lsn(), write_lsn) AS write_lag_bytes,
  pg_wal_lsn_diff(pg_current_wal_lsn(), flush_lag) AS flush_lag_bytes,
  pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lag) AS replay_lag_bytes
FROM pg_stat_replication;
"

# Check lag on replica (in seconds)
sudo -u postgres psql -c "
SELECT now() - pg_last_xact_replay_timestamp() AS replication_lag;
"
```

**Resolution:**
- If lag > 30s: Check network, disk I/O on replica
- If persistent: Add more replicas to distribute load

---

## 3. Cache Issues

### 3.1 Redis Connection Failed

**Symptoms:** `ConnectionError: Connection refused` in logs.

**Check:**
```bash
# Is Redis running?
ps aux | grep redis-server
sudo systemctl status redis-server

# Check Redis port
redis-cli -h 127.0.0.1 -p 6379 ping
```

**Fix:**
```bash
# Start Redis
sudo systemctl start redis-server

# Check Redis logs
sudo tail -50 /var/log/redis/redis-server.log

# If out of memory, restart
sudo systemctl restart redis-server
```

### 3.2 Cache Corruption

**Symptoms:** Inconsistent data, old data being served.

**Fix:**
```bash
# Clear entire cache
python manage.py cache_operations --clear

# Warm it back up
python manage.py cache_operations --warm

# Or use versioning to invalidate specific groups
python manage.py shell -c "
from cfbc.cache_utils import CacheVersion
CacheVersion.increment('noticias')
CacheVersion.increment('categorias')
"
```

### 3.3 Low Cache Hit Ratio

**Symptoms:** Cache hit ratio < 60%, high database load.

**Check:**
```bash
# Current hit ratio
python manage.py shell -c "
from cfbc.cache_utils import CacheMetrics
print(f'Hits: {CacheMetrics.get_stats()[\"hits\"]}')
print(f'Misses: {CacheMetrics.get_stats()[\"misses\"]}')
print(f'Hit Ratio: {CacheMetrics.get_hit_ratio()*100:.1f}%')
"
```

**Solutions:**
1. Increase TTLs for frequently accessed content
2. Implement cache warming for predictable loads
3. Check that cache invalidation isn't too aggressive
4. Verify Redis has enough memory (`maxmemory` in redis.conf)

---

## 4. Celery Issues

### 4.1 Tasks Not Processing

**Symptoms:** Tasks remain in PENDING state, queues grow.

**Check:**
```bash
# Are workers running?
celery -A cfbc inspect ping

# Are there active workers?
celery -A cfbc inspect active

# Check queue lengths
python manage.py shell -c "
from redis import Redis
from django.conf import settings
r = Redis.from_url(settings.CELERY_BROKER_URL)
for q in ['email', 'file_processing', 'reports', 'default', 'maintenance']:
    l = r.llen(q)
    if l > 0:
        print(f'{q}: {l} tasks waiting')
"
```

**Fix:**
```bash
# Start workers (if not running)
celery -A cfbc worker -l info -Q email,default --concurrency=4

# Restart workers (if stuck)
docker compose -f deploy/docker-compose.prod.yml restart celery-worker

# Purge stuck tasks (caution!)
celery -A cfbc purge
```

### 4.2 Tasks Timing Out

**Symptoms:** Tasks show as STARTED for long periods, then FAILURE.

**Check:**
```bash
# Check task time limits
python manage.py shell -c "
from django.conf import settings
print(f'Time limit: {settings.CELERY_TASK_TIME_LIMIT}s')
print(f'Soft limit: {settings.CELERY_TASK_SOFT_TIME_LIMIT}s')
"

# Check Redis for stuck tasks
redis-cli -n 3 LLEN celery
```

**Fix:**
- Increase time limits for long-running tasks
- Break large tasks into smaller chunks
- Reduce worker concurrency for CPU-bound tasks

### 4.3 Celery Beat Not Running

**Symptoms:** Scheduled tasks (backup, cleanup, cache warming) not executing.

**Check:**
```bash
# Is Celery Beat running?
ps aux | grep celery | grep beat

# Check beat schedule
celery -A cfbc inspect scheduled
```

**Fix:**
```bash
# Start Celery Beat
celery -A cfbc beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Or via Docker
docker compose -f deploy/docker-compose.prod.yml restart celery-beat
```

---

## 5. Nginx Issues

### 5.1 502 Bad Gateway

**Symptoms:** Nginx returns 502, but Django is running.

**Check:**
```bash
# Are Gunicorn instances running?
curl -s http://127.0.0.1:8001/health/
curl -s http://127.0.0.1:8002/health/

# Check Nginx upstream status
curl -s http://127.0.0.1:8080/nginx_status 2>/dev/null

# Check Nginx error log
tail -50 /var/log/nginx/error.log
```

**Fix:**
```bash
# Restart failing app instances
docker compose -f deploy/docker-compose.prod.yml restart app-1

# Reload Nginx
sudo nginx -s reload
```

### 5.2 504 Gateway Timeout

**Symptoms:** Nginx times out waiting for Django response.

**Check:**
```bash
# Check slow endpoints
curl -s -o /dev/null -w "%{time_total}s\n" http://localhost/slow-page/

# Check if request takes > timeout
python manage.py shell -c "
from django.conf import settings
# Check Gunicorn timeout
print(f'Gunicorn timeout: check deploy/gunicorn/gunicorn.conf.py')
# Check proxy timeouts in nginx.conf
"
```

**Fix:**
```bash
# Increase proxy timeout in nginx.conf:
# proxy_read_timeout 120s;
sudo nginx -s reload
```

### 5.3 SSL Certificate Expired

**Symptoms:** Browser shows security warning, HTTPS connections fail.

**Check:**
```bash
# Check cert expiry
openssl x509 -in /etc/ssl/cfbc/cfbc.crt -noout -dates

# Verify certificate
openssl verify -CAfile /etc/ssl/certs/ca-certificates.crt /etc/ssl/cfbc/cfbc.crt
```

**Fix:**
```bash
# Renew with Let's Encrypt
sudo certbot renew

# Force renewal
sudo certbot renew --force-renewal

# Reload Nginx after renewal
sudo nginx -s reload
```

---

## 6. Auto-Scaling Issues

### 6.1 Not Scaling Up Under Load

**Symptoms:** High CPU/memory but no new instances.

**Check:**
```bash
# Check auto-scaler status
python manage.py autoscale --status

# Check if cooldown is preventing scaling
# Look for: "Can scale up: False"

# Check metrics being collected
python manage.py shell -c "
from cfbc.autoscaler import create_default_scaler
scaler = create_default_scaler()
metrics = scaler.metrics_collector.collect()
print(f'CPU: {metrics.cpu_percent}%, Mem: {metrics.memory_percent}%')
print(f'Req/s: {metrics.request_rate}, P95: {metrics.p95_response_time}s')
"
```

**Fix:**
```bash
# Force scale manually
./deploy/scripts/scale_instances.sh docker set 6

# Restart auto-scaler
pkill -f "manage.py autoscale"
python manage.py autoscale --interval 60 &

# Or run a single evaluation
python manage.py autoscale --once
```

### 6.2 Scaling Too Frequently (Flapping)

**Symptoms:** Instances being added and removed repeatedly.

**Check:**
```bash
# Check scaling event log
tail -50 logs/autoscale.log

# Check if cooldown periods are effective
python manage.py shell -c "
from django.conf import settings
config = settings.AUTOSCALER_CONFIG
print(f'Scale-up cooldown: {config.get(\"cooldown_period_scale_up\", 120)}s')
print(f'Scale-down cooldown: {config.get(\"cooldown_period_scale_down\", 300)}s')
"
```

**Fix:**
- Increase cooldown periods
- Adjust thresholds to be less sensitive
- Reduce scale-up/down step size

---

## 7. Security Issues

### 7.1 Brute Force Attack on Login

**Symptoms:** Multiple failed login attempts from same IP.

**Check:**
```bash
# Check recent login failures
grep "login_failure" logs/monitoring.log | tail -20

# Check rate limiting events
grep "Rate limit exceeded" logs/monitoring.log | tail -10
```

**Response:**
```bash
# Block IP at Nginx level
# Add to nginx.conf:
#   location /accounts/login/ {
#       deny <offending_ip>;
#       ...
#   }
sudo nginx -s reload

# Or use iptables
sudo iptables -A INPUT -s <offending_ip> -j DROP
```

### 7.2 Suspicious File Upload

**Symptoms:** Malicious file detected by `SecurityService`.

**Check:**
```bash
# Check security audit logs
grep "SECURITY_AUDIT" logs/monitoring.log | grep "file_upload" | tail -20

# Check file security logs
grep "Archivo rechazado" logs/monitoring.log | tail -10
```

**Response:**
- Review the uploaded file
- Check user's activity history
- Adjust file validation rules if needed in `course_documents/security_service.py`

---

## 8. Deployment Issues

### 8.1 Migration Fails

**Symptoms:** `python manage.py migrate` fails with errors.

**Check:**
```bash
# See what migrations will be applied
python manage.py migrate --plan

# Check migration status
python manage.py showmigrations

# Get detailed error output
python manage.py migrate --verbosity=3 2>&1 | tail -50
```

**Fix:**
```bash
# Rollback last migration (replace with app name + migration number)
python manage.py migrate <app_name> <previous_migration>

# Fake a migration (if manually applied)
python manage.py migrate --fake <app_name> <migration_number>

# Create a new migration to fix issues
python manage.py makemigrations
```

### 8.2 Static Files Not Loading

**Symptoms:** CSS/JS missing, site looks unstyled.

**Check:**
```bash
# Check if static files are collected
ls -la staticfiles/css/styles.css

# Check Nginx static file configuration
service nginx configtest

# Check collectstatic output
python manage.py collectstatic --dry-run | head -20
```

**Fix:**
```bash
# Collect static files
python manage.py collectstatic --noinput

# Verify Nginx configuration
sudo nginx -t
sudo nginx -s reload
```

---

## Error Code Reference

| HTTP Status | Meaning | Common Cause |
|---|---|---|
| 200 | OK | Normal response |
| 301/302 | Redirect | Login redirect, URL change |
| 400 | Bad Request | Invalid form data |
| 403 | Forbidden | Permission denied |
| 404 | Not Found | Missing URL or file |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Application exception |
| 502 | Bad Gateway | Gunicorn not responding |
| 503 | Service Unavailable | Database down, maintenance |
| 504 | Gateway Timeout | Request took too long |

---

## Log File Locations

| Log | Location | When to Check |
|---|---|---|
| Application errors | `logs/errors.log` | 500 errors, exceptions |
| Performance issues | `logs/performance.log` | Slow queries, slow requests |
| General monitoring | `logs/monitoring.log` | All application events |
| Alert events | `logs/alerts.log` | Alert triggers |
| Auto-scaling | `logs/autoscale.log` | Scaling events |
| Nginx access | `/var/log/nginx/access.log` | Request traffic |
| Nginx error | `/var/log/nginx/error.log` | Nginx-level errors |
| Nginx health | `/var/log/nginx/health.log` | Health check results |
| Celery worker | `celery_worker.log` | Task processing logs |
| PostgreSQL | `/var/log/postgresql/` | Database errors |
| Redis | `/var/log/redis/redis-server.log` | Cache issues |
