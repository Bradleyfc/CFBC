# Database Scaling and Failover Procedures

## Overview

This document outlines the database scaling architecture, failover procedures,
and operational runbooks for the CFBC Django application.

## Architecture

### Database Cluster Layout

```
                     ┌─────────────────────┐
                     │   Load Balancer     │
                     │   (Nginx/Haproxy)   │
                     └──────────┬──────────┘
                                │
                   ┌────────────┴────────────┐
                   │                         │
          ┌────────┴────────┐      ┌─────────┴────────┐
          │  PgBouncer      │      │  PgBouncer       │
          │  (Connection    │      │  (Connection     │
          │   Pooler)       │      │   Pooler)        │
          └────────┬────────┘      └────────┬─────────┘
                   │                         │
          ┌────────┴────────┐      ┌─────────┴────────┐
          │  PostgreSQL     │      │  PostgreSQL      │
          │  Primary        │◄────►│  Read Replica 1  │
          │  (Read/Write)   │      │  (Read Only)     │
          └─────────────────┘      └──────────────────┘
                                           │
                                   ┌───────┴───────┐
                                   │  PostgreSQL   │
                                   │  Read Replica 2│
                                   │  (Read Only)  │
                                   └───────────────┘
```

### Connection Flow

1. **Application → PgBouncer**: Django connects to PgBouncer (port 6432)
2. **PgBouncer → PostgreSQL**: PgBouncer pools connections to PostgreSQL
3. **Read/Write Splitting**: Django's `AdaptiveRouter` routes queries:
   - Write queries → Primary database
   - Read queries → Read replica (or primary if replica unavailable)

## Configuration

### Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DB_NAME` | Database name | `postgre_db` |
| `DB_USER` | Database user | `postgre` |
| `DB_PASSWORD` | Database password | `admin` |
| `DB_HOST` | Primary database host | `localhost` |
| `DB_PORT` | Primary database port | `5432` |
| `DB_CONN_MAX_AGE` | Connection max age (seconds) | `600` |
| `DB_CONNECT_TIMEOUT` | Connection timeout (seconds) | `5` |
| `USE_READ_REPLICA` | Enable read replicas | `False` |
| `READ_REPLICA_HOST` | Read replica host | `localhost` |
| `READ_REPLICA_PORT` | Read replica port | `5433` |
| `USE_PGBOUNCER` | Enable PgBouncer pooling | `False` |
| `PGBOUNCER_HOST` | PgBouncer host | `127.0.0.1` |
| `PGBOUNCER_PORT` | PgBouncer port | `6432` |

### Django Settings

The database configuration is in `cfbc/settings.py` under the `DATABASES` section.

### PgBouncer Configuration

PgBouncer configuration file: `pgbouncer.ini`

## Monitoring

### Database Health Checks

Accessible via Django management commands and the monitoring service:

```bash
# Check all database connections
python manage.py shell -c "from cfbc.db_monitoring import ConnectionPoolMonitor; print(ConnectionPoolMonitor.get_all_connections_summary())"

# Check replica health
python manage.py shell -c "from cfbc.db_router import ReplicaHealthCheck; print(ReplicaHealthCheck.get_health_summary())"

# View slow query log
python manage.py shell -c "from cfbc.db_monitoring import slow_query_logger; print(slow_query_logger.get_recent_slow_queries(10))"
```

### Prometheus/Grafana Metrics

The following metrics are exposed for monitoring:

- **Connection pool utilization**: Active vs idle connections per database
- **Query execution times**: Average and 95th percentile query duration
- **Slow query count**: Number of queries exceeding the threshold
- **Replica health**: Status of read replicas (0 = down, 1 = healthy)

### Logging

Slow queries are logged at WARNING level:
```
SLOW QUERY (1500ms) on default: SELECT ... FROM noticia WHERE ...
```

## Failover Procedures

### Scenario 1: Primary Database Failure

**Symptoms:**
- Write operations fail with `OperationalError`
- Health check endpoint returns `503 Service Unavailable`
- Monitoring alerts: "Primary database is DOWN"

**Immediate Actions:**

1. **Verify the failure:**
   ```bash
   # Check if primary is accessible
   pg_isready -h localhost -p 5432
   
   # Check PostgreSQL logs
   sudo tail -100 /var/log/postgresql/postgresql-*.log
   ```

2. **Promote a read replica to primary:**
   ```bash
   # On the replica server
   sudo -u postgres pg_ctl promote -D /var/lib/postgresql/*/main
   
   # Or using Patroni (if using Patroni for HA)
   patronictl list
   patronictl failover --master <current_primary> --candidate <replica_to_promote>
   ```

3. **Update application configuration:**
   ```bash
   # Temporarily point to the promoted replica
   export DB_HOST=<promoted_replica_ip>
   export DB_PORT=5432
   
   # Restart application servers
   systemctl restart gunicorn
   ```

4. **Verify application functionality:**
   ```bash
   # Test database connectivity
   python manage.py check --database default
   
   # Test basic operations
   python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT 1'); print(cursor.fetchone())"
   ```

5. **Disable read replicas temporarily:**
   ```bash
   export USE_READ_REPLICA=False
   ```

**Recovery Actions:**

1. **Diagnose and fix the original primary**
2. **Re-establish replication from the new primary**
3. **Rebuild the original primary as a replica**
4. **Restore read replica configuration**
5. **Monitor replication lag for 24 hours**

### Scenario 2: Read Replica Failure

**Symptoms:**
- Read operations may be slow
- `ReplicaHealthCheck` reports replica as unhealthy
- Monitoring alerts: "Read replica is DOWN"

**Immediate Actions:**

1. **The system automatically handles this:**
   - `AdaptiveRouter` falls back to primary for reads
   - No user impact expected

2. **Verify the fallback is working:**
   ```bash
   python manage.py shell -c "from cfbc.db_router import ReplicaHealthCheck; print(ReplicaHealthCheck.is_replica_healthy('read_replica'))"
   ```

3. **Investigate and fix the replica:**
   ```bash
   # Check replication status on primary
   sudo -u postgres psql -c "SELECT * FROM pg_stat_replication;"
   
   # Check replica status
   sudo -u postgres psql -c "SELECT * FROM pg_stat_wal_receiver;"
   ```

**Recovery Actions:**

1. **Restart PostgreSQL on the replica:**
   ```bash
   sudo systemctl restart postgresql
   ```
2. **Verify replication is working:**
   ```bash
   sudo -u postgres psql -c "SELECT pg_is_in_recovery();"
   ```
3. **Resume normal operations (automatic)**

### Scenario 3: Connection Pool Exhaustion

**Symptoms:**
- New connections fail with `too many connections` error
- `ConnectionPoolMonitor` shows high pool utilization
- Application logs show connection timeouts

**Immediate Actions:**

1. **Check current connection count:**
   ```bash
   sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"
   sudo -u postgres psql -c "SELECT state, count(*) FROM pg_stat_activity GROUP BY state;"
   ```

2. **Identify problematic connections:**
   ```bash
   sudo -u postgres psql -c "SELECT pid, state, query_start, query FROM pg_stat_activity WHERE state = 'active' AND query_start < now() - interval '5 minutes';"
   ```

3. **Terminate long-running queries (if needed):**
   ```bash
   # Cancel a specific query (pid from above)
   sudo -u postgres psql -c "SELECT pg_cancel_backend(<pid>);"
   
   # Terminate a connection (more aggressive)
   sudo -u postgres psql -c "SELECT pg_terminate_backend(<pid>);"
   ```

4. **Increase pool limits temporarily:**
   - Edit `pgbouncer.ini` and increase `default_pool_size`
   - Reload PgBouncer: `sudo systemctl reload pgbouncer`

**Prevention:**

1. **Review connection pool settings:**
   - Ensure `CONN_MAX_AGE` is set appropriately
   - Verify PgBouncer pool sizes match expected load

2. **Monitor pool utilization trends:**
   - Set up alerts when pool utilization exceeds 80%
   - Review and tune pool sizes quarterly

### Scenario 4: Replication Lag

**Symptoms:**
- Stale data appearing in read replicas
- `ReplicaHealthCheck` reports high lag

**Monitoring:**
```bash
# Check replication lag on primary
sudo -u postgres psql -c "SELECT client_addr, state, write_lag, flush_lag, replay_lag FROM pg_stat_replication;"

# Check lag on replica
sudo -u postgres psql -c "SELECT pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn(), pg_last_xact_replay_timestamp();"
```

**Actions:**

1. **If lag > 30 seconds:**
   - `AdaptiveRouter` automatically routes reads to primary
   - Investigate network/disk I/O issues on replica

2. **If persistent lag:**
   - Check replica resource usage (CPU, disk I/O)
   - Consider adding more replicas for read load
   - Tune PostgreSQL replication parameters

## Regular Maintenance

### Daily

- Check replication status
- Review slow query log
- Monitor connection pool utilization

### Weekly

- Review database performance metrics
- Analyze slow queries for optimization opportunities
- Check disk usage on all database servers

### Monthly

- Run VACUUM ANALYZE on all tables
- Review and optimize indexes
- Update connection pool settings based on usage patterns

### Quarterly

- Review database configuration parameters
- Perform failover drill in staging
- Update scaling capacity projections

## Scaling Guidelines

### When to Add Read Replicas

- Read query response time > 100ms at 95th percentile
- Connection pool utilization > 80% consistently
- CPU usage on primary > 70% during peak hours

### When to Increase Pool Sizes

- Client wait time in PgBouncer > 10ms average
- `maxwait` in PgBouncer SHOW POOLS > 100ms
- Connection timeouts in application logs

### When to Upgrade Database Hardware

- Disk I/O wait > 20%
- Memory usage > 85%
- Query execution times increasing despite optimization

## Database Router Logic

The `AdaptiveRouter` in `cfbc/db_router.py` handles read/write splitting:

```
┌──────────────────────┐
│   Incoming Query     │
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│  Is it a write op?    │
│  → Default (Primary)  │
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│  Is it a write-through │
│  model? (AuditLog,    │
│  DocumentAccess, etc) │
│  → Default (Primary)  │
└──────────┬───────────┘
           │
┌──────────▼───────────┐
│  Is read replica      │
│  configured & healthy?│
│  → Read Replica       │
│  → Default (Fallback) │
└───────────────────────┘
```

### Write-Through Models

The following models always use the primary database for reads to ensure
immediate consistency:

- `AuditLog`
- `DocumentAccess`
- `Calificaciones`
- `Asistencia`
- `Matriculas`

## Verification Checklist

Use this checklist after deploying database scaling changes:

- [ ] Primary database is accessible
- [ ] Read replicas are configured (if enabled)
- [ ] Replication is working and lag is acceptable
- [ ] Database router is routing queries correctly
- [ ] Connection pooling is configured correctly
- [ ] Query timeouts are applied
- [ ] Slow query logging is operational
- [ ] Monitoring dashboards show correct metrics
- [ ] Failover procedures are documented and tested
- [ ] All team members are aware of the failover procedures
