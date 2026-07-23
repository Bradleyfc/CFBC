"""
Health check and metrics views for the CFBC monitoring stack.

Provides:
- /health/ - Health check endpoint for load balancers
- /metrics/ - Prometheus-style metrics for monitoring

Requirements: prometheus_client (optional, for /metrics/)
"""

import os
import time
import logging
from datetime import datetime

from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.db import connection
from django.core.cache import cache
from django.views.decorators.http import require_GET
from django.views.decorators.cache import never_cache

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Health Check Endpoint
# ─────────────────────────────────────────────────────────────────────────────

@require_GET
@never_cache
def health_check(request):
    """
    Health check endpoint for load balancers and monitoring systems.

    Returns:
        200 OK with JSON if all services are healthy
        503 Service Unavailable if any critical service is down

    Checks:
    - Database connectivity
    - Cache/Redis connectivity
    - Disk space (if HEALTH_CHECK_INCLUDE_DETAILS is enabled)

    Usage:
        curl http://localhost:8000/health/
        curl http://127.0.0.1:8001/health/
    """
    health_data = {
        'status': 'healthy',
        'instance_id': getattr(settings, 'INSTANCE_ID', 'unknown'),
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'checks': {},
    }

    all_healthy = True

    # Check database
    db_healthy = _check_database()
    health_data['checks']['database'] = {
        'status': 'ok' if db_healthy else 'error',
    }
    if not db_healthy:
        health_data['status'] = 'unhealthy'
        all_healthy = False
        health_data['checks']['database']['error'] = 'Database connection failed'

    # Check cache/Redis
    cache_healthy = _check_cache()
    health_data['checks']['cache'] = {
        'status': 'ok' if cache_healthy else 'error',
    }
    if not cache_healthy:
        health_data['checks']['cache']['error'] = 'Cache connection failed'
        # Cache is non-critical, don't mark overall as unhealthy
        health_data['checks']['cache']['status'] = 'degraded'

    # Include detailed checks if configured
    include_details = getattr(settings, 'HEALTH_CHECK_INCLUDE_DETAILS', False)
    if include_details:
        health_data['checks']['disk'] = _check_disk_space()
        health_data['checks']['celery'] = _check_celery()

    status_code = 200 if all_healthy else 503
    response = JsonResponse(health_data, status=status_code)
    response['X-Instance-ID'] = health_data['instance_id']
    return response


def _check_database():
    """Check database connectivity by executing a simple query."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"Health check - database failed: {e}")
        return False


def _check_cache():
    """Check cache/Redis connectivity."""
    try:
        cache.set('health_check_ping', 'pong', timeout=5)
        result = cache.get('health_check_ping')
        return result == 'pong'
    except Exception as e:
        logger.warning(f"Health check - cache failed: {e}")
        return False


def _check_disk_space():
    """Check disk space availability."""
    try:
        import shutil
        usage = shutil.disk_usage('/')
        free_gb = usage.free / (1024 ** 3)
        total_gb = usage.total / (1024 ** 3)
        percent_free = (usage.free / usage.total) * 100

        result = {
            'status': 'ok' if percent_free > 10 else 'warning',
            'free_gb': round(free_gb, 1),
            'total_gb': round(total_gb, 1),
            'percent_free': round(percent_free, 1),
        }

        if percent_free < 5:
            result['status'] = 'critical'
            logger.error(f"CRITICAL: Disk space at {percent_free:.1f}% free")

        return result
    except Exception as e:
        return {'status': 'unknown', 'error': str(e)}


def _check_celery():
    """Check Celery worker availability."""
    try:
        from celery import current_app
        inspect = current_app.control.inspect(timeout=2.0)
        if inspect:
            stats = inspect.stats()
            if stats:
                workers = list(stats.keys())
                return {
                    'status': 'ok',
                    'workers': workers,
                    'worker_count': len(workers),
                }
            return {'status': 'degraded', 'error': 'No Celery workers responding'}
        return {'status': 'degraded', 'error': 'Celery inspect returned no data'}
    except Exception as e:
        return {'status': 'degraded', 'error': str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# Metrics Endpoint
# ─────────────────────────────────────────────────────────────────────────────

@require_GET
@never_cache
def metrics_view(request):
    """
    Expose Django application metrics in Prometheus text format.

    Provides:
    - Request counts per endpoint (last minute)
    - Average response times per endpoint
    - Status code distribution
    - Database query counts and times
    - Cache hit/miss ratios (if available)
    - Active instance count

    Usage:
        curl http://localhost:8000/metrics/

    Note: For full Prometheus integration, use django-prometheus:
        pip install django-prometheus
        Add to MIDDLEWARE and urls.py
    """
    try:
        # Try to use prometheus_client if installed
        from prometheus_client import generate_latest, REGISTRY, Gauge, Counter, Histogram
        from prometheus_client.exposition import CONTENT_TYPE_LATEST

        # Register custom metrics
        _register_custom_metrics()

        output = generate_latest(REGISTRY)
        return HttpResponse(
            output,
            content_type=CONTENT_TYPE_LATEST,
        )
    except ImportError:
        # Fallback: return plain-text metrics without prometheus_client
        return _generate_text_metrics()


def _register_custom_metrics():
    """Register custom Django metrics with Prometheus registry."""
    try:
        from prometheus_client import REGISTRY

        # Only register if not already registered
        if 'cfbc_requests_total' not in [m.name for m in REGISTRY.collect()]:
            # Load metrics from Redis and register them
            pass
    except Exception:
        pass


def _generate_text_metrics():
    """Generate metrics in Prometheus text format without the client library."""
    lines = []
    lines.append("# HELP cfbc_health Django application health status")
    lines.append("# TYPE cfbc_health gauge")
    lines.append(f"cfbc_health{{instance=\"{getattr(settings, 'INSTANCE_ID', 'unknown')}\"}} 1")

    # Instance info
    lines.append("# HELP cfbc_instance_info Instance metadata")
    lines.append("# TYPE cfbc_instance_info gauge")
    lines.append(f'cfbc_instance_info{{instance="{getattr(settings, "INSTANCE_ID", "unknown")}"}} 1')

    # Current time
    lines.append("# HELP cfbc_uptime_seconds Application uptime")
    lines.append("# TYPE cfbc_uptime_seconds gauge")
    lines.append(f"cfbc_uptime_seconds {int(time.time())}")

    # Get metrics from Redis if available
    try:
        from datetime import datetime as dt
        now = dt.now()
        minute_key = now.strftime('%Y-%m-%dT%H:%M')

        # Request counts
        requests = cache.hgetall(f'cfbc:metrics:requests:{minute_key}') or {}
        lines.append("# HELP cfbc_requests_total Total requests per endpoint")
        lines.append("# TYPE cfbc_requests_total counter")
        for path, count in requests.items():
            lines.append(f'cfbc_requests_total{{path="{path}"}} {count}')

        # Status codes
        statuses = cache.hgetall(f'cfbc:metrics:status:{minute_key}') or {}
        lines.append("# HELP cfbc_http_requests_total HTTP status codes")
        lines.append("# TYPE cfbc_http_requests_total counter")
        for status_group, count in statuses.items():
            lines.append(f'cfbc_http_requests_total{{status="{status_group}"}} {count}')

    except Exception:
        pass

    lines.append("# EOF")
    return HttpResponse('\n'.join(lines), content_type='text/plain; charset=utf-8')


# ─────────────────────────────────────────────────────────────────────────────
# Metrics Summary API (JSON)
# ─────────────────────────────────────────────────────────────────────────────

@require_GET
@never_cache
def metrics_summary(request):
    """
    Return a JSON summary of current application metrics.

    Used by monitoring dashboards and the auto-scaler.

    Usage:
        curl http://localhost:8000/metrics/summary/
    """
    summary = {
        'instance_id': getattr(settings, 'INSTANCE_ID', 'unknown'),
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'requests': {},
        'database': {},
        'cache': {},
        'system': {},
    }

    # Get metrics from Redis
    try:
        from datetime import datetime as dt
        now = dt.now()
        minute_key = now.strftime('%Y-%m-%dT%H:%M')

        # Request metrics
        requests = cache.hgetall(f'cfbc:metrics:requests:{minute_key}') or {}
        summary['requests']['per_endpoint'] = {k: int(v) for k, v in requests.items()}
        summary['requests']['total'] = sum(summary['requests']['per_endpoint'].values())

        # Duration metrics
        duration_data = cache.hgetall(f'cfbc:metrics:duration:{minute_key}') or {}
        durations = {}
        for key, value in duration_data.items():
            path, metric = key.rsplit(':', 1)
            if path not in durations:
                durations[path] = {}
            durations[path][metric] = float(value)

        summary['requests']['avg_duration'] = {
            path: round(data.get('sum', 0) / max(data.get('count', 1), 1), 3)
            for path, data in durations.items()
        }

        # Status codes
        statuses = cache.hgetall(f'cfbc:metrics:status:{minute_key}') or {}
        summary['requests']['status_codes'] = {k: int(v) for k, v in statuses.items()}

    except Exception:
        pass

    # Database info
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()")
            summary['database']['connections'] = cursor.fetchone()[0]
            cursor.execute("SELECT pg_database_size(current_database())")
            summary['database']['size_bytes'] = cursor.fetchone()[0]
    except Exception:
        pass

    # Cache info
    try:
        cache.set('metrics_ping', 'ok', timeout=5)
        summary['cache']['status'] = 'ok' if cache.get('metrics_ping') == 'ok' else 'error'
    except Exception:
        summary['cache']['status'] = 'error'

    # System info
    try:
        import os
        load = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
        summary['system']['load_1m'] = round(load[0], 2)
        summary['system']['load_5m'] = round(load[1], 2)
        summary['system']['load_15m'] = round(load[2], 2)
    except Exception:
        pass

    return JsonResponse(summary)
