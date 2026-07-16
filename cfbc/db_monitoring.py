"""
Database connection pool monitoring and query timeout configuration.

Provides utilities for:
- Monitoring connection pool usage
- Tracking query execution times
- Configuring query timeouts at various levels
- Exposing metrics for Prometheus/Grafana
"""

import time
import logging
import threading
from contextlib import contextmanager
from collections import defaultdict
from datetime import datetime, timedelta
from django.conf import settings
from django.db import connections

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Query Timeout Configuration
# ─────────────────────────────────────────────────────────────────────────────

class QueryTimeoutConfig:
    """
    Centralized query timeout configuration.

    Timeouts can be configured per database alias, per operation type,
    and with different levels of strictness (statement_timeout vs lock_timeout).
    """

    # Default timeouts in milliseconds (PostgreSQL uses ms)
    DEFAULTS = {
        'default': {
            'statement_timeout': 30000,   # 30 seconds
            'lock_timeout': 10000,         # 10 seconds
        },
        'read_replica': {
            'statement_timeout': 60000,   # 60 seconds (replicas can be slower)
            'lock_timeout': 15000,         # 15 seconds
        },
    }

    # Per-operation type overrides (in milliseconds)
    OPERATION_TIMEOUTS = {
        'list': 10000,       # 10s for list views
        'detail': 5000,      # 5s for detail views
        'search': 15000,     # 15s for search queries
        'report': 60000,     # 60s for report generation
        'export': 120000,    # 120s for data exports
        'health_check': 2000, # 2s for health check queries
    }

    @classmethod
    def get_timeout(cls, db_alias='default', operation=None):
        """
        Get the appropriate timeout for a database and operation.

        Args:
            db_alias: Database alias ('default' or 'read_replica')
            operation: Optional operation type for granular control

        Returns:
            Dict with 'statement_timeout' and 'lock_timeout' in milliseconds
        """
        config = cls.DEFAULTS.get(db_alias, cls.DEFAULTS['default']).copy()

        if operation and operation in cls.OPERATION_TIMEOUTS:
            config['statement_timeout'] = min(
                config['statement_timeout'],
                cls.OPERATION_TIMEOUTS[operation]
            )

        return config

    @classmethod
    def set_query_timeouts(cls, using='default', operation=None):
        """
        Set PostgreSQL timeouts for the current connection.

        This should be called at the beginning of a request or
        before executing a specific query.
        """
        from django.db import connections

        config = cls.get_timeout(using, operation)
        conn = connections[using]

        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"SET statement_timeout = {config['statement_timeout']}"
                )
                cursor.execute(
                    f"SET lock_timeout = {config['lock_timeout']}"
                )
        except Exception as e:
            logger.warning(f"Failed to set timeouts for '{using}': {e}")


@contextmanager
def query_timeout(seconds=30, using='default'):
    """
    Context manager to set a temporary query timeout.

    Usage:
        with query_timeout(seconds=10):
            results = MyModel.objects.all()

    The original timeout is restored after the block exits.
    """
    from django.db import connections

    conn = connections[using]
    original_timeout = None

    try:
        with conn.cursor() as cursor:
            cursor.execute("SHOW statement_timeout")
            original_timeout = cursor.fetchone()[0]
            cursor.execute(
                f"SET statement_timeout = {seconds * 1000}"
            )
        yield
    finally:
        if original_timeout is not None:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        f"SET statement_timeout = {original_timeout}"
                    )
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────────────────────
# Connection Pool Monitoring
# ─────────────────────────────────────────────────────────────────────────────

class ConnectionPoolMonitor:
    """
    Monitor database connection pool usage and health.

    Tracks:
    - Active connections per database
    - Connection acquisition times
    - Pool utilization (used vs available)
    - Connection errors and timeouts

    Works with both Django's internal connection pooling (CONN_MAX_AGE)
    and PgBouncer-managed pools.
    """

    _lock = threading.Lock()
    _metrics = defaultdict(lambda: {
        'total_connections': 0,
        'active_connections': 0,
        'connection_errors': 0,
        'timeouts': 0,
        'avg_acquire_time': 0.0,
        'peak_connections': 0,
        'last_reset': datetime.now(),
    })

    @classmethod
    def get_connection_stats(cls, db_alias='default'):
        """
        Get current connection statistics for a specific database.

        Returns a dict with connection pool metrics or None if unavailable.
        """
        try:
            conn = connections[db_alias]
            stats = {
                'db_alias': db_alias,
                'is_available': True,
                'is_usable': conn.is_usable() if hasattr(conn, 'is_usable') else True,
                'closed': conn.closed if hasattr(conn, 'closed') else False,
                'in_atomic_block': conn.in_atomic_block if hasattr(conn, 'in_atomic_block') else False,
                'settings': settings.DATABASES.get(db_alias, {}),
            }

            # Get actual connection info from PostgreSQL
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT
                            count(*) as total_connections,
                            count(*) FILTER (WHERE state = 'active') as active,
                            count(*) FILTER (WHERE state = 'idle') as idle,
                            count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction
                        FROM pg_stat_activity
                        WHERE datname = current_database()
                    """)
                    row = cursor.fetchone()
                    if row:
                        stats.update({
                            'total_connections': row[0],
                            'active': row[1],
                            'idle': row[2],
                            'idle_in_transaction': row[3],
                        })
            except Exception:
                pass

            # PgBouncer-specific stats (if using PgBouncer)
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SHOW POOLS")
                    pools = cursor.fetchall()
                    if pools:
                        stats['pgbouncer_pools'] = [
                            {
                                'database': p[0],
                                'user': p[1],
                                'cl_active': int(p[2]),
                                'cl_waiting': int(p[3]),
                                'sv_active': int(p[4]),
                                'sv_idle': int(p[5]),
                                'sv_used': int(p[6]),
                                'sv_tested': int(p[7]),
                                'sv_login': int(p[8]),
                                'maxwait': float(p[9]),
                            }
                            for p in pools
                        ]
            except Exception:
                pass

            return stats

        except Exception as e:
            return {
                'db_alias': db_alias,
                'error': str(e),
                'is_available': False,
            }

    @classmethod
    def get_all_connections_summary(cls):
        """
        Get a summary of all database connections across all configured databases.
        """
        summary = {}
        for alias in connections:
            summary[alias] = cls.get_connection_stats(alias)
        return summary

    @classmethod
    def track_query_execution(cls, db_alias='default', duration_ms=0):
        """
        Track a query execution for metrics collection.

        This is called by middleware to record query performance.
        """
        with cls._lock:
            metrics = cls._metrics[db_alias]
            metrics['total_connections'] += 1

            # Update moving average of acquire time
            if duration_ms > 0:
                prev_avg = metrics['avg_acquire_time']
                count = metrics['total_connections']
                metrics['avg_acquire_time'] = (
                    (prev_avg * (count - 1) + duration_ms) / count
                )

            if duration_ms > 1000:  # Slow query threshold (>1s)
                metrics['timeouts'] += 1

    @classmethod
    def get_metrics_report(cls, db_alias='default'):
        """
        Get a formatted report of connection pool metrics.
        """
        metrics = cls._metrics.get(db_alias, {})
        return {
            'db_alias': db_alias,
            'total_queries': metrics.get('total_connections', 0),
            'connection_errors': metrics.get('connection_errors', 0),
            'slow_queries': metrics.get('timeouts', 0),
            'avg_query_time_ms': round(metrics.get('avg_acquire_time', 0.0), 2),
            'peak_connections': metrics.get('peak_connections', 0),
            'period': f"Since {metrics.get('last_reset', datetime.now())}",
        }

    @classmethod
    def reset_metrics(cls, db_alias=None):
        """
        Reset metrics for a specific database or all databases.
        """
        with cls._lock:
            if db_alias:
                cls._metrics[db_alias] = {
                    'total_connections': 0,
                    'active_connections': 0,
                    'connection_errors': 0,
                    'timeouts': 0,
                    'avg_acquire_time': 0.0,
                    'peak_connections': 0,
                    'last_reset': datetime.now(),
                }
            else:
                for alias in cls._metrics:
                    cls._metrics[alias] = {
                        'total_connections': 0,
                        'active_connections': 0,
                        'connection_errors': 0,
                        'timeouts': 0,
                        'avg_acquire_time': 0.0,
                        'peak_connections': 0,
                        'last_reset': datetime.now(),
                    }


# ─────────────────────────────────────────────────────────────────────────────
# Slow Query Logging
# ─────────────────────────────────────────────────────────────────────────────

class SlowQueryLogger:
    """
    Logs database queries that exceed a configurable threshold.

    Integrates with Django's query logging to capture and report
    slow queries for performance analysis.

    Note: This is a best-effort monitoring utility. Under extreme
    concurrent load, some slow queries may not be captured due to
    the non-blocking lock acquisition strategy.
    """

    def __init__(self, threshold_ms=500):
        """
        Initialize the slow query logger.

        Args:
            threshold_ms: Queries exceeding this duration (ms) are logged
        """
        self.threshold_ms = threshold_ms
        self.slow_queries = []
        self._lock = threading.Lock()

    def process_query(self, query_info):
        """
        Process a database query and log if it exceeds the threshold.

        Args:
            query_info: Dict with 'sql', 'time', 'alias', and 'stacktrace'
        """
        duration_ms = query_info.get('time', 0) * 1000  # Convert seconds to ms

        if duration_ms >= self.threshold_ms:
            with self._lock:
                self.slow_queries.append({
                    'sql': query_info.get('sql', '')[:500],  # Truncate long SQL
                    'duration_ms': round(duration_ms, 2),
                    'alias': query_info.get('alias', 'default'),
                    'timestamp': datetime.now(),
                })

            if duration_ms >= 1000:  # Critical: >1s
                logger.warning(
                    f"SLOW QUERY ({duration_ms:.0f}ms) on {query_info.get('alias', 'default')}: "
                    f"{query_info.get('sql', '')[:200]}"
                )

    def get_recent_slow_queries(self, limit=20):
        """
        Get the most recent slow queries.
        """
        with self._lock:
            sorted_queries = sorted(
                self.slow_queries,
                key=lambda q: q['timestamp'],
                reverse=True
            )[:limit]
        return sorted_queries

    def clear(self):
        """Clear the slow query log."""
        with self._lock:
            self.slow_queries = []


# Global instance for use across the application
slow_query_logger = SlowQueryLogger()


# ─────────────────────────────────────────────────────────────────────────────
# Middleware for query timeout and monitoring
# ─────────────────────────────────────────────────────────────────────────────

class DatabaseMonitoringMiddleware:
    """
    Django middleware for database monitoring and timeout management.

    Sets appropriate query timeouts at the start of each request
    and logs slow queries for performance analysis.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Set query timeouts at the start of each request
        self._apply_timeouts(request)

        # Process the request
        response = self.get_response(request)

        return response

    def _apply_timeouts(self, request):
        """
        Apply appropriate timeouts based on the request type.
        """
        # Determine operation type from URL path
        path = request.path.lower()
        if '/admin/' in path:
            operation = 'report'
        elif any(p in path for p in ['/search', '/buscar']):
            operation = 'search'
        elif any(p in path for p in ['/export', '/report']):
            operation = 'export'
        elif '/health/' in path:
            operation = 'health_check'
        else:
            operation = 'detail'

        # Apply timeouts for all configured databases
        for alias in connections:
            try:
                QueryTimeoutConfig.set_query_timeouts(
                    using=alias,
                    operation=operation
                )
            except Exception as e:
                logger.debug(f"Could not set timeouts for '{alias}': {e}")
