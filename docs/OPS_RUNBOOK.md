# Operations Runbook

## Overview

This runbook contains standardized operational procedures for the CFBC platform.
It covers routine operations, incident response, and recovery procedures.

**Target Audience:** System administrators and operations team

## Table of Contents

1. [Service Management](#1-service-management)
2. [Deployment Procedures](#2-deployment-procedures)
3. [Backup and Recovery](#3-backup-and-recovery)
4. [Incident Response](#4-incident-response)
5. [Monitoring Alerts](#5-monitoring-alerts)
6. [Database Operations](#6-database-operations)
7. [Cache Operations](#7-cache-operations)
8. [Celery Operations](#8-celery-operations)
9. [Security Incidents](#9-security-incidents)

---

## 1. Service Management

### 1.1 Check System Status

```bash
# Overall application health
curl -s http://localhost:8000/health/ | python -m json.tool

# Performance metrics summary
curl -s http://localhost:8000/metrics/summary/ | python -m json.tool

# Full performance analysis
source venv/bin/activate
python manage.py analyze_performance

# Security audit
python manage.py security_audit

# Auto-scaler status
python manage.py autoscale --status
```

### 1.2 Start/Stop Services

**Docker deployment:**
```bash
# View all services
docker compose -f deploy/docker-compose.prod.yml ps

# Start all services
docker compose -f deploy/docker-compose.prod.yml up -d

# Stop all services
docker compose -f deploy/docker-compose.prod.yml down

# Restart a specific service
docker compose -f deploy/docker-compose.prod.yml restart app-1
docker compose -f deploy/docker-compose.prod.yml restart nginx
docker compose -f deploy/docker-compose.prod.yml restart celery-worker

# View logs
docker compose -f deploy/docker-compose.prod.yml logs -f --tail=100 app-1
docker compose -f deploy/docker-compose.prod.yml logs -f nginx
```

**Systemd deployment:**
```bash
# View service status
sudo systemctl status cfbc@8001
sudo systemctl status nginx
sudo systemctl status redis-server
sudo systemctl status postgresql

# Start/Stop individual instance
sudo systemctl start cfbc@8001
sudo systemctl stop cfbc@8001
sudo systemctl restart cfbc@8001

# Start/Stop all instances
for port in 8001 8002 8003 8004; do
  sudo systemctl restart cfbc@$port
done

# Nginx
sudo systemctl reload nginx    # Graceful (zero downtime)
sudo systemctl restart nginx   # Full restart
```

### 1.3 Scale Instances

```bash
# Manual scale up (add one instance)
./deploy/scripts/scale_instances.sh docker up

# Manual scale down (remove one instance)
./deploy/scripts/scale_instances.sh docker down

# Set specific count
./deploy/scripts/scale_instances.sh docker set 6

# Verify status
./deploy/scripts/scale_instances.sh docker status

# Start auto-scaler
python manage.py autoscale --interval 60
```

---

## 2. Deployment Procedures

### 2.1 Standard Deployment

```bash
# 1. Pull latest code
cd /var/www/cfbc
git pull origin main

# 2. Activate virtual environment
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run database migrations
python manage.py migrate

# 5. Collect static files
python manage.py collectstatic --noinput

# 6. Run tests
python manage.py test --exclude-tag=slow

# 7. Restart application
docker compose -f deploy/docker-compose.prod.yml restart app
# OR (systemd):
for port in 8001 8002 8003 8004; do
  sudo systemctl restart cfbc@$port
  sleep 5
done
```

### 2.2 Rolling Restart (Zero Downtime)

```bash
# Docker: restart one instance at a time
for i in 1 2 3 4; do
  echo "Restarting app-$i..."
  docker compose -f deploy/docker-compose.prod.yml restart app-$i
  sleep 10
  curl -sf http://localhost:8000/health/ > /dev/null && \
    echo "app-$i healthy" || echo "app-$i FAILED"
done

# Systemd: restart one at a time
for port in 8001 8002 8003 8004; do
  echo "Restarting cfbc@$port..."
  sudo systemctl restart cfbc@$port
  sleep 10
  curl -sf http://127.0.0.1:$port/health/ > /dev/null && \
    echo "Instance $port healthy" || echo "Instance $port FAILED"
done
```

### 2.3 Rollback

```bash
# Quick rollback (revert code)
git revert HEAD --no-edit
git push origin main

# Full rollback to previous tag
git checkout tags/v1.0.0
pip install -r requirements.txt
python manage.py migrate
docker compose -f deploy/docker-compose.prod.yml up -d --force-recreate
```

---

## 3. Backup and Recovery

### 3.1 Database Backup

```bash
# Full database backup
PGPASSWORD=admin pg_dump -U postgre -h localhost postgre_db \
  > /backups/cfbc_$(date +%Y%m%d_%H%M%S).sql

# Backup with compression
PGPASSWORD=admin pg_dump -U postgre -h localhost postgre_db | gzip \
  > /backups/cfbc_$(date +%Y%m%d).sql.gz

# Automated backup (crontab: daily at 2 AM)
0 2 * * * PGPASSWORD=admin pg_dump -U postgre -h localhost postgre_db | \
  gzip > /backups/cfbc_$(date +\\%Y\\%m\\%d).sql.gz
```

### 3.2 Database Restore

```bash
# Restore from backup
gunzip -c /backups/cfbc_20260713.sql.gz | \
  PGPASSWORD=admin psql -U postgre -h localhost postgre_db

# Create database first if needed
PGPASSWORD=admin createdb -U postgre -h localhost cfbc_restored
gunzip -c /backups/cfbc_20260713.sql.gz | \
  PGPASSWORD=admin psql -U postgre -h localhost cfbc_restored
```

### 3.3 Media Files Backup

```bash
# Backup media directory
tar -czf /backups/media_$(date +%Y%m%d).tar.gz /var/www/cfbc/media/

# Restore media files
tar -xzf /backups/media_20260713.tar.gz -C /var/www/cfbc/
```

### 3.4 Configuration Backup

```bash
# Backup environment and config files
tar -czf /backups/config_$(date +%Y%m%d).tar.gz \
  /var/www/cfbc/.env \
  /var/www/cfbc/pgbouncer.ini \
  /etc/nginx/nginx.conf \
  /etc/nginx/ssl.conf
```

---

## 4. Incident Response

### 4.1 Application Down

**Symptoms:** Users cannot access the site, health check returns 503.

**Checklist:**
```
□ Check if Nginx is running:
  docker compose ps | grep nginx
  sudo systemctl status nginx

□ Check if app instances are running:
  docker compose ps | grep app
  curl http://127.0.0.1:8001/health/

□ Check PostgreSQL:
  docker compose ps | grep postgres
  pg_isready -h localhost -p 5432

□ Check Redis:
  redis-cli ping

□ Check application logs for errors:
  docker compose logs --tail=50 app-1
  tail -100 logs/errors.log

□ Verify disk space:
  df -h
```

**Resolution:**
1. Restart the failing service
2. If database is down, follow [Database Failover](docs/database_scaling.md#scenario-1-primary-database-failure)
3. If all instances fail, check for recent deployments and rollback if needed

### 4.2 Slow Performance

**Symptoms:** High response times, users reporting slowness.

**Checklist:**
```
□ Check current performance metrics:
  curl http://localhost:8000/metrics/summary/
  python manage.py analyze_performance

□ Check database connections:
  python manage.py shell -c "from cfbc.db_monitoring import ConnectionPoolMonitor; print(ConnectionPoolMonitor.get_all_connections_summary())"

□ Check slow queries:
  python manage.py shell -c "from cfbc.db_monitoring import slow_query_logger; print(slow_query_logger.get_recent_slow_queries(20))"

□ Check cache hit ratio:
  python manage.py shell -c "from cfbc.cache_utils import CacheMetrics; print(CacheMetrics.get_stats())"

□ Check Celery queue:
  python manage.py shell -c "
from redis import Redis
from django.conf import settings
r = Redis.from_url(settings.CELERY_BROKER_URL)
for q in ['email','file_processing','reports','default','maintenance']:
    print(f'{q}: {r.llen(q)}')
"

□ Check system resources:
  ps aux --sort=-%cpu | head -10
  free -m
  df -h
```

**Resolution:**
1. If DB pool high: increase pool size or add replicas
2. If cache hit ratio low: warm cache or adjust TTLs
3. If Celery queue backlog: increase worker concurrency
4. If CPU/memory high: scale up instances
5. Run `python manage.py analyze_performance` for detailed analysis

### 4.3 Database Connection Exhaustion

**Symptoms:** "too many connections" errors in logs.

**Checklist:**
```bash
# Check current connections
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"
sudo -u postgres psql -c "SELECT state, count(*) FROM pg_stat_activity GROUP BY state;"

# Check long-running queries
sudo -u postgres psql -c "
SELECT pid, now() - query_start AS duration, query, state
FROM pg_stat_activity
WHERE state = 'active' AND query_start < now() - interval '5 minutes'
ORDER BY duration DESC;"
```

**Resolution:**
1. Kill long-running queries: `SELECT pg_cancel_backend(<pid>);`
2. Increase pool limits temporarily in `pgbouncer.ini`
3. Restart idle connections

### 4.4 Redis/Cache Failure

**Symptoms:** Cache-dependent features slow or failing.

**Checklist:**
```bash
# Test Redis connectivity
redis-cli ping

# Check Redis memory
redis-cli info memory | grep -E "used_memory_human|maxmemory"

# Check cache health via Django
curl http://localhost:8000/health/ | python -m json.tool
```

**Resolution:**
1. Restart Redis: `sudo systemctl restart redis-server`
2. Clear cache if corrupted: `python manage.py cache_operations --clear`
3. Warm up cache: `python manage.py cache_operations --warm`

---

## 5. Monitoring Alerts

### 5.1 Alert: High CPU Usage (>80%)

**Action:** Scale up app instances
```bash
python manage.py autoscale --once
./deploy/scripts/scale_instances.sh docker up
```

### 5.2 Alert: High Memory Usage (>85%)

**Action:** Check for memory leak, restart instances
```bash
for port in 8001 8002 8003 8004; do
  sudo systemctl restart cfbc@$port
  sleep 10
done
```

### 5.3 Alert: Slow Response Time (>2s)

**Action:** Run performance analysis
```bash
python manage.py analyze_performance
# Check slow queries and optimize
```

### 5.4 Alert: High Error Rate (>5%)

**Action:** Check error logs and diagnose
```bash
tail -100 logs/errors.log | grep -E "CRITICAL|ERROR" | head -20
docker compose logs --tail=50 app-1
```

### 5.5 Alert: Celery Queue Backlog (>100)

**Action:** Check workers and restart if needed
```bash
celery -A cfbc inspect active
docker compose restart celery-worker
```

### 5.6 Alert: Disk Space Low (<10%)

**Action:** Clean up old logs and backups
```bash
# Clean old log files
find logs/ -name "*.log.*" -mtime +7 -delete

# Clean old backups
find /backups/ -name "*.sql.gz" -mtime +30 -delete

# Clean Docker build cache
docker system prune -f

# Check largest directories
du -sh /var/www/cfbc/* | sort -rh | head -10
```

---

## 6. Database Operations

### 6.1 Run Migrations

```bash
source venv/bin/activate
python manage.py migrate --plan   # Preview
python manage.py migrate           # Execute
python manage.py migrate --fake    # Mark as applied (emergency only)
```

### 6.2 Check Replication Status

```bash
# On primary
sudo -u postgres psql -c "SELECT client_addr, state, write_lag, flush_lag, replay_lag FROM pg_stat_replication;"

# On replica
sudo -u postgres psql -c "SELECT pg_is_in_recovery(), pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn();"
```

### 6.3 Manual VACUUM

```bash
# Analyze table statistics
sudo -u postgres psql -c "VACUUM ANALYZE;"

# Analyze specific table
sudo -u postgres psql -c "VACUUM ANALYZE blog_noticia;"

# Check table bloat
sudo -u postgres psql -c "
SELECT schemaname, tablename, n_dead_tup, n_live_tup,
  round(100 * n_dead_tup / GREATEST(n_live_tup + n_dead_tup, 1), 1) AS dead_pct
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC;"
```

---

## 7. Cache Operations

### 7.1 View Cache Status

```bash
# Check cache metrics
python manage.py shell -c "
from cfbc.cache_utils import CacheMetrics, CacheVersion
print('Hit ratio:', CacheMetrics.get_hit_ratio())
print('Versions:', CacheVersion.all_groups())
"

# Redis info
redis-cli info stats | grep -E "keyspace_hits|keyspace_misses|evicted_keys"
```

### 7.2 Clear Cache

```bash
# Clear entire cache
python manage.py cache_operations --clear

# Clear specific version group
python manage.py shell -c "
from cfbc.cache_utils import CacheVersion
CacheVersion.increment('noticias')
print('Noticias cache invalidated')
"

# Clear all Redis databases
redis-cli FLUSHALL
```

### 7.3 Warm Cache

```bash
# Manual cache warming
python manage.py cache_operations --warm

# Or via shell
python manage.py shell -c "
from cfbc.cache_signals import warm_cache
results = warm_cache()
print(results)
"
```

---

## 8. Celery Operations

### 8.1 Check Worker Status

```bash
# List active workers
celery -A cfbc inspect active

# List registered tasks
celery -A cfbc inspect registered

# Check worker stats
celery -A cfbc inspect stats

# Ping all workers
celery -A cfbc inspect ping
```

### 8.2 Manage Tasks

```bash
# Revoke a specific task
celery -A cfbc control revoke <task_id>

# Purge all pending tasks (caution!)
celery -A cfbc purge

# View task result
celery -A cfbc result <task_id>
```

### 8.3 Restart Workers

```bash
# Docker
docker compose -f deploy/docker-compose.prod.yml restart celery-worker
docker compose -f deploy/docker-compose.prod.yml restart celery-beat

# Systemd
sudo systemctl restart celery
sudo systemctl restart celery-beat
```

---

## 9. Security Incidents

### 9.1 Suspicious Activity Detected

**Symptoms:** Security audit logs show probe scans or unauthorized access.

**Checklist:**
```bash
# Check security audit logs
grep "SECURITY_AUDIT" logs/monitoring.log | grep "probe_scan" | tail -20

# Check failed logins
grep "SECURITY_AUDIT" logs/monitoring.log | grep "login_failure" | tail -20

# Check rate limiting events
grep "Rate limit exceeded" logs/monitoring.log | tail -10

# Check recent 403/401 responses
tail -1000 logs/monitoring.log | grep '"status": 403' | wc -l
```

**Resolution:**
1. Block offending IPs at Nginx level
2. Review and tighten rate limiting if needed
3. Rotate credentials if compromise is suspected
4. Run `python manage.py security_audit` to verify configuration

### 9.2 Block an IP Address

```bash
# At Nginx level (in server block)
# Add to nginx.conf:
# deny <offending_ip>;
# Then reload:
sudo nginx -s reload

# At firewall level
sudo ufw deny from <offending_ip>
sudo iptables -A INPUT -s <offending_ip> -j DROP
```

### 9.3 Review Security Configuration

```bash
# Comprehensive security audit
python manage.py security_audit

# Check running services for vulnerabilities
# (requires bandit)
bandit -r cfbc/ -x venv, migrations -ll
```

---

## Quick Reference Card

| Task | Command |
|---|---|
| Health check | `curl localhost:8000/health/` |
| View metrics | `curl localhost:8000/metrics/summary/` |
| Performance analysis | `python manage.py analyze_performance` |
| Security audit | `python manage.py security_audit` |
| Auto-scaler status | `python manage.py autoscale --status` |
| Start auto-scaler | `python manage.py autoscale --interval 60` |
| Scale up | `./deploy/scripts/scale_instances.sh docker up` |
| Scale down | `./deploy/scripts/scale_instances.sh docker down` |
| Run migrations | `python manage.py migrate` |
| Check DB connections | ConnectionPoolMonitor (shell) |
| View slow queries | `slow_query_logger.get_recent_slow_queries(10)` (shell) |
| Warm cache | `python manage.py cache_operations --warm` |
| Clear cache | `python manage.py cache_operations --clear` |
| Load test (baseline) | `./run_load_tests.sh baseline` |
| Load test (peak) | `./run_load_tests.sh peak` |
| Check Celery workers | `celery -A cfbc inspect active` |
| View app logs | `docker compose logs -f app-1` |
| View Nginx logs | `docker compose logs -f nginx` |
