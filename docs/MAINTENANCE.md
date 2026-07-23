# Maintenance Schedule

## Overview

This document defines the maintenance schedule and procedures for the CFBC platform.
Following these procedures ensures system reliability, security, and performance.

**Responsibility**: System Administrator / DevOps Team

---

## Daily Tasks

### □ Check System Health

```bash
curl -s http://localhost:8000/health/ | python -m json.tool
```

Verify: `status: "healthy"`, all checks pass.

### □ Review Error Logs

```bash
tail -50 logs/errors.log | grep -E "CRITICAL|ERROR"
```

Verify: No new critical errors since last check.

### □ Check Disk Space

```bash
df -h / | tail -1
```

Verify: Usage < 80%. If > 80%, plan cleanup.

**Estimated time**: 5 minutes

---

## Weekly Tasks

### □ Run Performance Analysis

```bash
python manage.py analyze_performance
```

Check:
- P95 response times < 2s
- Error rate < 1%
- Cache hit ratio > 60%
- No critical or warning issues

### □ Review Slow Queries

```bash
python manage.py shell -c "
from cfbc.db_monitoring import slow_query_logger
queries = slow_query_logger.get_recent_slow_queries(20)
for q in queries:
    print(f\"[{q['duration_ms']}ms] {q['sql'][:100]}\")
"
```

Verify: No new slow queries > 1s without known cause.

### □ Check Database Connections

```bash
python manage.py shell -c "
from cfbc.db_monitoring import ConnectionPoolMonitor
stats = ConnectionPoolMonitor.get_all_connections_summary()
for alias, info in stats.items():
    print(f'{alias}: {info}')
"
```

Verify: Pool utilization < 80%.

### □ Check Replication Status

```bash
sudo -u postgres psql -c "
SELECT client_addr, state,
  pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lag) AS bytes_behind
FROM pg_stat_replication;
"
```

Verify: Replication lag < 10MB (or configured threshold).

### □ Check Redis Memory

```bash
redis-cli INFO memory | grep -E "used_memory_human|maxmemory"
```

Verify: Used memory < 80% of maxmemory.

**Estimated time**: 15 minutes

---

## Monthly Tasks

### □ Run Security Audit

```bash
python manage.py security_audit --output /backups/security_audit_$(date +%Y%m).txt
```

Verify: No critical security issues.

### □ Database VACUUM ANALYZE

```bash
# Check if vacuum is needed
sudo -u postgres psql -c "
SELECT schemaname, tablename, n_dead_tup, n_live_tup,
  round(100 * n_dead_tup / GREATEST(n_live_tup + n_dead_tup, 1), 1) AS dead_pct
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC;
"

# Run VACUUM ANALYZE on tables with > 20% dead rows
sudo -u postgres psql -c "VACUUM ANALYZE;"
```

### □ Review and Optimize Indexes

```bash
# Check unused indexes
sudo -u postgres psql -c "
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY tablename;
"

# Check index usage
sudo -u postgres psql -c "
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan ASC;
"
```

### □ Review Cache Performance

```bash
python manage.py shell -c "
from cfbc.cache_utils import CacheMetrics, CacheVersion
stats = CacheMetrics.get_stats()
print(f'Hits: {stats[\"hits\"]}')
print(f'Misses: {stats[\"misses\"]}')
print(f'Hit ratio: {stats[\"hit_ratio\"]*100:.1f}%')
print(f'Versions: {stats[\"versions\"]}')
"

# Reset metrics for next month
python manage.py shell -c "
from cfbc.cache_utils import CacheMetrics
CacheMetrics.reset_metrics()
print('Cache metrics reset')
"
```

### □ Review Auto-Scaler Configuration

```bash
python manage.py autoscale --status
```

Verify:
- Min/max instances are appropriate for current traffic
- Thresholds are balanced
- No excessive scaling events in logs

### □ Check Celery Queue Health

```bash
# Check queue lengths
python manage.py shell -c "
from redis import Redis
from django.conf import settings
r = Redis.from_url(settings.CELERY_BROKER_URL)
for q in ['email', 'file_processing', 'reports', 'default', 'maintenance', 'backup']:
    l = r.llen(q)
    print(f'{q}: {l} tasks')
"

# Check worker stats
celery -A cfbc inspect stats 2>/dev/null || echo "Workers not running"
```

### □ Backup Configuration Files

```bash
tar -czf /backups/config_$(date +%Y%m%d).tar.gz \
  /var/www/cfbc/.env \
  /etc/nginx/nginx.conf \
  /etc/nginx/ssl.conf \
  /etc/postgresql/16/main/postgresql.conf \
  /etc/redis/redis.conf
```

**Estimated time**: 30-45 minutes

---

## Quarterly Tasks

### □ Full Load Test

```bash
# Baseline test
./run_load_tests.sh baseline

# Peak test
./run_load_tests.sh peak
```

Verify against success criteria:
- [ ] P95 response time < 2s
- [ ] Error rate < 1%
- [ ] Throughput > 100 req/s
- [ ] Reports saved to `reports/` directory

### □ Failover Drill

Test database failover in staging environment:

1. **Primary failover**:
   - Simulate primary database failure
   - Promote replica to primary
   - Verify application still works
   - Fail back to original primary

2. **Replica failover**:
   - Take replica offline
   - Verify automatic fallback to primary
   - Restore replica

3. **Application instance failover**:
   - Take one app instance offline
   - Verify Nginx routes around it
   - Restore instance

Document results in `/backups/failover_drill_$(date +%Y%m%d).log`

### □ Review and Update Thresholds

- Review auto-scaling thresholds based on last 3 months of data
- Review alerting thresholds to reduce false positives
- Update database pool sizes based on peak usage

### □ Performance Optimization Review

1. Run full performance analysis:
   ```bash
   python manage.py analyze_performance --minutes 10080  # Last 7 days
   ```

2. Review slow query log for patterns
3. Identify frequently accessed but uncached data
4. Plan optimizations for next quarter

### □ Dependency Updates

```bash
# List outdated packages
pip list --outdated

# Update requirements files
pip install -r requirements.txt --upgrade
```

### □ Security Review

1. Run security audit:
   ```bash
   python manage.py security_audit
   ```

2. Review recent security advisories for Django and dependencies
3. Update SSL certificates if needed (Let's Encrypt: every 90 days)
4. Rotate database passwords if policy requires
5. Review access logs for suspicious activity

### □ Capacity Planning

1. Review usage trends (users, courses, documents)
2. Project growth for next quarter
3. Plan infrastructure scaling if needed
4. Review cloud/infrastructure costs

**Estimated time**: 2-4 hours

---

## Annual Tasks

### □ Full Disaster Recovery Drill

1. Restore from backup to clean environment
2. Verify all services work
3. Measure recovery time
4. Document lessons learned

### □ Architecture Review

1. Review current architecture against requirements
2. Identify technical debt
3. Plan major upgrades
4. Update architecture documentation

### □ Major Version Upgrades

- Django LTS upgrade (if applicable)
- PostgreSQL major version upgrade
- Redis major version upgrade
- Server OS upgrade

### □ Security Audit (External)

- Engage external security firm (if budget allows)
- Penetration testing
- Vulnerability assessment
- Compliance review

---

## Maintenance Checklist Template

### Daily Checklist
```
Date: _______________
Performed by: _______________

□ Health check passed
□ No critical errors in logs
□ Disk space OK (< 80%)
Notes: ________________________________________________
```

### Weekly Checklist
```
Date: _______________
Performed by: _______________

□ Performance analysis passed
□ No new slow queries
□ Database pool utilization < 80%
□ Replication lag normal
□ Redis memory OK
Notes: ________________________________________________
```

### Monthly Checklist
```
Date: _______________
Performed by: _______________

□ Security audit - no critical issues
□ VACUUM ANALYZE completed
□ Indexes reviewed
□ Cache performance reviewed
□ Auto-scaler config reviewed
□ Celery health checked
□ Config files backed up
Notes: ________________________________________________
```

### Quarterly Checklist
```
Date: _______________
Performed by: _______________

□ Load test completed (baseline + peak)
□ Failover drill completed
□ Thresholds reviewed
□ Dependencies updated
□ Security review completed
□ Capacity review completed
Notes: ________________________________________________
```

---

## Escalation Contacts

| Role | Contact | Response Time |
|---|---|---|
| System Administrator | ops@cfbc.edu.ni | 1 hour (business hours) |
| Lead Developer | dev@cfbc.edu.ni | 4 hours |
| Database Administrator | dba@cfbc.edu.ni | 2 hours |
| Security Officer | security@cfbc.edu.ni | 1 hour (critical) |

---

## Related Documents

- `docs/OPS_RUNBOOK.md` - Detailed operational procedures
- `docs/TROUBLESHOOTING.md` - Problem diagnosis and resolution
- `docs/monitoring_stack.md` - Monitoring and alerting details
- `docs/database_scaling.md` - Database backup and failover
- `docs/ARCHITECTURE.md` - System architecture overview
