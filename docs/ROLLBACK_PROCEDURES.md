# Rollback Procedures

**Document Version:** 1.0
**Last Updated:** 2026-07-14
**Applies To:** CFBC Django Educational Platform

---

## Table of Contents

1. [Rollback Decision Matrix](#1-rollback-decision-matrix)
2. [Database Rollback](#2-database-rollback)
   - 2.1 Migration Rollback
   - 2.2 Full Database Restore
   - 2.3 Read Replica Failover
3. [Cache Rollback](#3-cache-rollback)
   - 3.1 Full Cache Flush
   - 3.2 Selective Cache Invalidation
   - 3.3 Version Group Rollback
4. [Configuration Rollback](#4-configuration-rollback)
   - 4.1 Django Settings
   - 4.2 Environment Variables (.env)
   - 4.3 Nginx Configuration
   - 4.4 PgBouncer Configuration
5. [Deployment Rollback](#5-deployment-rollback)
   - 5.1 Code Rollback (Git)
   - 5.2 Docker Rollback
   - 5.3 Gunicorn Rollback
6. [File Storage Rollback](#6-file-storage-rollback)
7. [Rollback Testing Procedures](#7-rollback-testing-procedures)
8. [Contacts and Escalation](#8-contacts-and-escalation)

---

## 1. Rollback Decision Matrix

| Severity | Symptoms | Action | Time Target | Approver |
|----------|----------|--------|-------------|----------|
| **Critical** | Site down, data corruption, security breach | Full rollback to last known good state | < 15 min | Technical Lead |
| **High** | Feature broken for all users, major errors | Rollback affected component(s) | < 30 min | Tech Lead or Senior Dev |
| **Medium** | Feature broken for subset of users, performance degradation | Rollback specific change(s) | < 60 min | On-call Developer |
| **Low** | Cosmetic issues, minor functionality impact | Fix forward in next deployment | < 24 hrs | Developer |

### Rollback Guidelines
- **Always** take a full database backup before any deployment
- **Always** document the current state (git commit hash, migration versions) before starting
- **Always** verify rollback success by checking `/health/` endpoint
- **Never** rollback a database migration that has been running for > 10 minutes (data loss risk)
- **Prefer** fix-forward for non-critical issues

---

## 2. Database Rollback

### 2.1 Migration Rollback

**When to use:** A recently applied migration introduces errors or data corruption.

**Prerequisites:**
- Record the current migration state before deploying
- Ensure the previous migration is reversible (most Django migrations are)

**Rollback steps:**

```bash
# 1. SSH into the application server
ssh deploy@cfbc-server

# 2. Activate virtual environment
cd /var/www/cfbc
source venv/bin/activate

# 3. Check current migration state
python manage.py showmigrations

# 4. Rollback specific app migrations (rollback one at a time)
# Format: python manage.py migrate <app_name> <previous_migration>

# --- Custom apps (rollback targets) ---
python manage.py migrate principal 0025_solicitudinscripcion_curso_academico
python manage.py migrate accounts 0009_registro_foto_carnet_registro_foto_titulo
python manage.py migrate blog 0007_add_indexes_noticia
python manage.py migrate datos_archivados 0011_asistenciaarchivada_semestre_archivado_and_more
python manage.py migrate course_documents 0009_add_performance_indexes
python manage.py migrate historial 0002_historicalclass_historicalclassstudentview
python manage.py migrate evaluaciones 0006_add_todo_o_nada_to_pregunta

# --- Third-party apps (DO NOT rollback these) ---
# admin, auth, contenttypes, sessions, django_celery_beat, django_celery_results

# 5. Verify rollback
python manage.py showmigrations | grep -E "\[X\]|\[ \]"

# 6. Test the application
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health/
# Should return 200
```

**Important Notes:**
- Always rollback **one migration at a time**
- Verify the app works after each rollback
- If a migration is irreversible (missing `migrations.RunPython.noop`), you'll need a full database restore instead
- Squashed migrations must be rolled back as a group

### 2.2 Full Database Restore

**When to use:** Multiple migrations need reversal, data corruption, or migration rollback failed.

```bash
# 1. Stop the application (prevents new writes during restore)
docker compose -f deploy/docker-compose.prod.yml down app

# OR for systemd:
# sudo systemctl stop gunicorn

# 2. Find the latest backup
ls -la /backups/cfbc_*.sql.gz

# 3. Create a backup of current state (just in case)
export PGPASSWORD=${DB_PASSWORD:-admin}
pg_dump -U postgre -h localhost postgre_db > /backups/cfbc_pre_restore_$(date +%Y%m%d_%H%M%S).sql

# 4. Drop and recreate the database
# Option A: Restore to existing database (replace)
gunzip -c /backups/cfbc_20260713.sql.gz | \
  psql -U postgre -h localhost postgre_db

# Option B: Restore to new database (for verification first)
PGPASSWORD=admin createdb -U postgre -h localhost cfbc_restored
gunzip -c /backups/cfbc_20260713.sql.gz | \
  PGPASSWORD=admin psql -U postgre -h localhost cfbc_restored

# 5. Restart the application
docker compose -f deploy/docker-compose.prod.yml up -d app

# OR:
# sudo systemctl start gunicorn

# 6. Verify
python manage.py migrate --check
curl -s http://localhost:8000/health/
python manage.py showmigrations
```

**Restore time estimate:** Depends on database size. For a 1GB database: ~5-10 minutes.

### 2.3 Read Replica Failover

**When to use:** Primary database is unavailable; promote replica to primary.

```bash
# 1. SSH into the replica server
ssh deploy@cfbc-replica

# 2. Verify replica is caught up
sudo -u postgres psql -c "SELECT pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn();"

# 3. Promote replica to primary
sudo -u postgres pg_ctl promote -D /var/lib/postgresql/data

# 4. Verify promotion
sudo -u postgres psql -c "SELECT pg_is_in_recovery();"
# Should return 'f' (false)

# 5. Update application configuration to point to new primary
# Edit .env file:
# DB_HOST=<new_primary_ip>

# 6. Restart application instances
docker compose -f deploy/docker-compose.prod.yml restart app

# 7. Verify application health
curl -s http://localhost:8000/health/
```

---

## 3. Cache Rollback

### 3.1 Full Cache Flush

**When to use:** Stale/corrupted cache data affecting all users, after schema changes.

```bash
# Option A: Flush all Redis databases (WARNING: Flushes everything)
redis-cli -h 127.0.0.1 -p 6379 FLUSHALL

# Option B: Flush specific databases used by the application
redis-cli -h 127.0.0.1 -p 6379 -n 1 FLUSHDB   # General cache (DB 1)
redis-cli -h 127.0.0.1 -p 6379 -n 2 FLUSHDB   # Sessions (DB 2)
```

### 3.2 Selective Cache Invalidation

**When to use:** Only specific cached data is stale; need to preserve session data.

```bash
# Invalidate by key pattern
redis-cli -h 127.0.0.1 -p 6379 -n 1 KEYS 'cfbc_cache:noticia:*' | xargs redis-cli -h 127.0.0.1 -p 6379 -n 1 DEL
redis-cli -h 127.0.0.1 -p 6379 -n 1 KEYS 'cfbc_cache:comentario:*' | xargs redis-cli -h 127.0.0.1 -p 6379 -n 1 DEL
redis-cli -h 127.0.0.1 -p 6379 -n 1 KEYS 'cfbc_cache:curso:*' | xargs redis-cli -h 127.0.0.1 -p 6379 -n 1 DEL
redis-cli -h 127.0.0.1 -p 6379 -n 1 KEYS 'cfbc_cache:documento:*' | xargs redis-cli -h 127.0.0.1 -p 6379 -n 1 DEL
redis-cli -h 127.0.0.1 -p 6379 -n 1 KEYS 'cfbc_cache:evaluacion:*' | xargs redis-cli -h 127.0.0.1 -p 6379 -n 1 DEL

# Via Django management command
python manage.py cache_operations clear --pattern "noticia:*"
python manage.py cache_operations clear --group noticias
python manage.py cache_operations clear --group categorias
```

### 3.3 Version Group Rollback

**When to use:** Cache is serving stale data due to schema changes; increment version to invalidate entire group.

```python
# Via Django shell or management command
python manage.py shell -c "
from cfbc.cache_utils import CacheVersion
# Increment version for specific group (invalidates all cached items in group)
CacheVersion.bump('noticias')      # Invalidates all news cache
CacheVersion.bump('comentarios')   # Invalidates all comment cache
CacheVersion.bump('documentos')    # Invalidates all document cache
print('Cache versions bumped for: noticias, comentarios, documentos')
"
```

**Version groups available:**
| Group | Description | TTL | Impact |
|-------|-------------|-----|--------|
| `noticias` | Blog/news list and detail pages | 5-10 min | All news content |
| `categorias` | Category navigation | 60 min | Category menus |
| `comentarios` | Comments on news | 5 min | All comment sections |
| `cursos` | Course listings and dashboards | 5 min | All course pages |
| `documentos` | Course documents | 5 min | All document lists |
| `evaluaciones` | Evaluation forms and results | 5 min | All evaluation pages |
| `usuarios` | User profiles and settings | 5 min | All user profile pages |
| `general` | General cached content | 10 min | Everything else |

---

## 4. Configuration Rollback

### 4.1 Django Settings

**When to use:** Wrong settings deployed (e.g., ALLOWED_HOSTS, DATABASE config).

```bash
# 1. Settings are version-controlled; revert via git
git checkout HEAD~1 -- cfbc/settings.py

# 2. If settings are in a backup:
tar -xzf /backups/config_$(date +%Y%m%d).tar.gz \
  -C /tmp/config_restore

# 3. Replace broken settings with backup
cp /tmp/config_restore/cfbc/settings.py cfbc/settings.py

# 4. Verify syntax (critical!)
python -c "import ast; ast.parse(open('cfbc/settings.py').read()); print('✅ Valid syntax')"

# 5. Restart application
sudo systemctl restart gunicorn
# OR: docker compose restart app
```

### 4.2 Environment Variables (.env)

**When to use:** Wrong database credentials, API keys, or feature flags deployed.

```bash
# 1. Restore .env from backup
cp /backups/.env.20260713 /var/www/cfbc/.env

# 2. Or restore from archived config
tar -xzf /backups/config_$(date +%Y%m%d).tar.gz \
  -C /var/www/cfbc/ .env

# 3. Verify critical variables are set
grep -E "^(DB_|SECRET|EMAIL|REDIS)" /var/www/cfbc/.env

# 4. Restart application
sudo systemctl restart gunicorn
# OR: docker compose restart app
```

### 4.3 Nginx Configuration

**When to use:** Wrong load balancer, SSL, or routing configuration.

```bash
# 1. Restore from backup
cp /backups/nginx.conf.20260713 /etc/nginx/nginx.conf
cp /backups/ssl.conf.20260713 /etc/nginx/ssl.conf

# 2. Test configuration syntax
sudo nginx -t

# 3. Reload Nginx (graceful, no downtime)
sudo nginx -s reload

# 4. If Nginx config was deployed via version control:
cd /var/www/cfbc
git checkout HEAD~1 -- deploy/nginx/nginx.conf
sudo cp deploy/nginx/nginx.conf /etc/nginx/nginx.conf
sudo nginx -t && sudo nginx -s reload
```

**See also:** `docs/load_balancer.md` (Quick Rollback and Full Rollback sections)

### 4.4 PgBouncer Configuration

**When to use:** Connection pooling causing issues after config change.

```bash
# 1. Restore from backup
cp /backups/pgbouncer.ini.20260713 /etc/pgbouncer/pgbouncer.ini

# 2. Reload PgBouncer (graceful)
sudo systemctl reload pgbouncer
# OR: pgbouncer -R /etc/pgbouncer/pgbouncer.ini

# 3. Verify connections working
psql -h 127.0.0.1 -p 6432 -U postgre -c "SHOW POOLS;"
```

---

## 5. Deployment Rollback

### 5.1 Code Rollback (Git)

**When to use:** Application code introduced bugs or regressions.

```bash
# Quick Rollback (revert the last commit)
cd /var/www/cfbc
source venv/bin/activate

# 1. Revert the last commit
git revert HEAD --no-edit

# 2. Push the revert
git push origin main

# 3. Update dependencies if requirements.txt changed
pip install -r requirements.txt

# 4. Run migrations if any
python manage.py migrate

# 5. Collect static files
python manage.py collectstatic --noinput

# 6. Restart application
sudo systemctl restart gunicorn

# 7. Verify
curl -s http://localhost:8000/health/


# Full Rollback (to a specific tagged version)
cd /var/www/cfbc
source venv/bin/activate

# 1. Check available tags
git tag -l

# 2. Checkout specific tag
git checkout tags/v1.0.0

# 3. Update dependencies
pip install -r requirements.txt

# 4. Run migration check
python manage.py migrate --check

# 5. Collect static files
python manage.py collectstatic --noinput

# 6. Restart application
sudo systemctl restart gunicorn

# 7. Verify
curl -s http://localhost:8000/health/
```

### 5.2 Docker Rollback

**When to use:** Application deployed via Docker and new image has issues.

```bash
# 1. List available application images
docker images cfbc_app

# 2. Revert to previous image version
cd /var/www/cfbc

# Option A: Rollback using docker-compose
docker compose -f deploy/docker-compose.prod.yml down
# Edit deploy/docker-compose.prod.yml to point to previous image tag
docker compose -f deploy/docker-compose.prod.yml up -d

# Option B: Rollback using tag reference
docker tag cfbc_app:previous cfbc_app:latest
docker compose -f deploy/docker-compose.prod.yml up -d

# 3. Verify
curl -s http://localhost:8000/health/
docker logs cfbc_app --tail 20
```

### 5.3 Gunicorn Rollback

**When to use:** Gunicorn configuration change causing workers to fail.

```bash
# 1. Restore gunicorn config from backup
cp /backups/gunicorn.conf.py.20260713 deploy/gunicorn/gunicorn.conf.py

# 2. Verify Gunicorn config
python -c "import ast; ast.parse(open('deploy/gunicorn/gunicorn.conf.py').read()); print('✅ Valid syntax')"

# 3. Restart Gunicorn
sudo systemctl restart gunicorn

# 4. Check status
sudo systemctl status gunicorn
journalctl -u gunicorn --tail 30
```

---

## 6. File Storage Rollback

**When to use:** Corrupted or incorrectly processed uploaded files.

```bash
# 1. Restore media files from backup
tar -xzf /backups/media_20260713.tar.gz -C /var/www/cfbc/

# 2. Fix file permissions
find /var/www/cfbc/media -type f -exec chmod 644 {} \;
find /var/www/cfbc/media -type d -exec chmod 755 {} \;

# 3. Verify critical files exist (e.g., default images)
ls -la /var/www/cfbc/media/default/
```

---

## 7. Rollback Testing Procedures

### Testing Schedule

| Rollback Type | Frequency | Environment | Test Method |
|---------------|-----------|-------------|-------------|
| Migration rollback | Per deployment (manual) | Staging | Apply + rollback + verify |
| Database restore | Monthly | Staging | Restore from latest backup |
| Cache flush | Quarterly | Staging | Flush + verify app works |
| Code rollback | Per deployment (scripted) | Staging | Deploy → rollback → verify |
| Docker rollback | Quarterly | Staging | Deploy new image → rollback |
| Nginx rollback | Quarterly | Staging | Change config → rollback |
| Failover drill | Quarterly | Staging | Primary → replica promotion |

### Per-Deployment Test Script

```bash
#!/bin/bash
# save as: scripts/test_rollback.sh

set -e

echo "🚦 Testing Rollback Procedures"
echo "=============================="

# 1. Record current state
echo "📝 Recording current migration state..."
python manage.py showmigrations > /tmp/pre_rollback_migrations.txt
CURRENT_COMMIT=$(git rev-parse HEAD)
echo "Current commit: $CURRENT_COMMIT"

# 2. Apply test migration
echo "🔄 Applying migration..."
python manage.py migrate 2>&1 | tail -5

# 3. Rollback migration
echo "↩️  Rolling back migration..."
python manage.py migrate principal 0025_solicitudinscripcion_curso_academico

# 4. Verify state restored
echo "✅ Verifying migration state restored..."
python manage.py showmigrations > /tmp/post_rollback_migrations.txt
diff /tmp/pre_rollback_migrations.txt /tmp/post_rollback_migrations.txt

# 5. Re-apply latest migration
echo "🔄 Re-applying latest migration..."
python manage.py migrate

# 6. Test health endpoint
echo "🏥 Testing health endpoint..."
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8000/health/

echo "✅ Rollback test complete"
```

### Success Criteria

| Test | Expected Result | How to Verify |
|------|----------------|---------------|
| Migration rollback | Same state as before | `diff pre/post_rollback_migrations.txt` |
| Database restore | All data present | Row count comparison |
| Cache flush | App works without cached data | `curl /health/` returns 200 |
| Code rollback | Previous features work | Run regression test suite |
| Docker rollback | Application starts | `curl /health/` returns 200 |
| Nginx rollback | Routing works | `curl -I https://cfbc.edu.ni` |
| Failover | Application uses new primary | `curl /health/` returns 200, check DB host |

---

## 8. Contacts and Escalation

### Primary Contacts

| Role | Name | Contact | Backup |
|------|------|---------|--------|
| Technical Lead | _TBD_ | _TBD_ | _TBD_ |
| DevOps Engineer | _TBD_ | _TBD_ | _TBD_ |
| Database Admin | _TBD_ | _TBD_ | _TBD_ |
| Security Officer | _TBD_ | _TBD_ | _TBD_ |

### Escalation Matrix

| Level | When | Contact | Response Time |
|-------|------|---------|---------------|
| L1 | Business hours, non-critical | Dev On-call | < 1 hour |
| L2 | After hours, medium severity | Tech Lead | < 30 min |
| L3 | Any time, critical/catastrophic | Technical Lead + DevOps | < 15 min |

### Communication

1. **During rollback:** Post status to `#incidents` channel
2. **After rollback:** Update incident ticket with:
   - What was rolled back
   - Why it was rolled back
   - Current state (migration versions, git commit, etc.)
   - Verification results
   - Root cause analysis reference

---

## Quick Reference Card

```bash
# === QUICK REFERENCE: Common Rollback Commands ===

# Migration rollback (one at a time)
python manage.py migrate principal 0025_solicitudinscripcion_curso_academico

# Full database restore from latest backup
gunzip -c /backups/cfbc_latest.sql.gz | psql -U postgre -h localhost postgre_db

# Cache flush (preserves sessions)
redis-cli -n 1 FLUSHDB

# Code rollback (quick revert)
git revert HEAD --no-edit && git push origin main

# Nginx rollback
sudo nginx -t && sudo cp deploy/nginx/nginx.conf /etc/nginx/ && sudo nginx -s reload

# Verify health
curl -s http://localhost:8000/health/

# Check current state
git log --oneline -3
python manage.py showmigrations | tail -20
```
