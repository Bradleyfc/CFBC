"""
Management command to analyze production performance metrics.

Collects and analyzes performance data from:
- Redis metrics (request counts, durations, DB query counts)
- Log files (slow queries, slow requests, errors)
- Database statistics (connection pool, query performance)
- Cache metrics (hit/miss ratios)

Generates a comprehensive performance report with:
- Bottleneck identification
- Optimization recommendations
- Trend analysis (if historical data available)

Usage:
    # Run full performance analysis
    python manage.py analyze_performance

    # Analyze specific area only
    python manage.py analyze_performance --area database
    python manage.py analyze_performance --area cache
    python manage.py analyze_performance --area requests

    # Output in JSON format (for programmatic consumption)
    python manage.py analyze_performance --format json

    # Analyze last N minutes instead of default 60
    python manage.py analyze_performance --minutes 15

    # Continuous monitoring mode (every 5 minutes)
    python manage.py analyze_performance --watch
"""

import os
import re
import json
import time
import glob
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connection, connections
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Analyze production performance metrics and generate optimization report'

    def add_arguments(self, parser):
        parser.add_argument(
            '--area', '-a',
            type=str,
            choices=['all', 'database', 'cache', 'requests', 'system', 'celery'],
            default='all',
            help='Performance area to analyze (default: all)'
        )
        parser.add_argument(
            '--format', '-f',
            type=str,
            choices=['text', 'json'],
            default='text',
            help='Output format (default: text)'
        )
        parser.add_argument(
            '--minutes', '-m',
            type=int,
            default=60,
            help='Number of minutes of data to analyze (default: 60)'
        )
        parser.add_argument(
            '--watch', '-w',
            action='store_true',
            help='Continuous monitoring mode (reports every 5 minutes)'
        )
        parser.add_argument(
            '--log-dir',
            type=str,
            default='logs',
            help='Directory containing log files (default: logs/)'
        )

    def handle(self, *args, **options):
        self.area = options['area']
        self.output_format = options['format']
        self.minutes = options['minutes']
        self.watch_mode = options['watch']
        self.log_dir = options['log_dir']

        if self.watch_mode:
            self._run_watch_mode()
        else:
            report = self._generate_report()
            self._output_report(report)

    def _run_watch_mode(self):
        """Run in continuous monitoring mode."""
        self.stdout.write(self.style.WARNING(
            "Performance Monitor - Watching every 5 minutes..."
        ))
        self.stdout.write("Press Ctrl+C to stop.\n")

        try:
            while True:
                report = self._generate_report()
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.stdout.write(f"\n{'='*60}")
                self.stdout.write(f"Performance Report - {timestamp}")
                self.stdout.write('=' * 60)
                self._output_report(report)
                time.sleep(300)  # 5 minutes
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS("\nMonitoring stopped."))

    def _generate_report(self):
        """Generate a comprehensive performance analysis report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'analysis_period_minutes': self.minutes,
            'summary': {'overall_health': 'unknown', 'issues_found': 0},
        }

        issues = []

        if self.area in ('all', 'database'):
            db_report = self._analyze_database()
            report['database'] = db_report
            if db_report.get('issues'):
                issues.extend(db_report['issues'])

        if self.area in ('all', 'cache'):
            cache_report = self._analyze_cache()
            report['cache'] = cache_report
            if cache_report.get('issues'):
                issues.extend(cache_report['issues'])

        if self.area in ('all', 'requests'):
            requests_report = self._analyze_requests()
            report['requests'] = requests_report
            if requests_report.get('issues'):
                issues.extend(requests_report['issues'])

        if self.area in ('all', 'system'):
            system_report = self._analyze_system()
            report['system'] = system_report
            if system_report.get('issues'):
                issues.extend(system_report['issues'])

        if self.area in ('all', 'celery'):
            celery_report = self._analyze_celery()
            report['celery'] = celery_report
            if celery_report.get('issues'):
                issues.extend(celery_report['issues'])

        # Analyze log files for slow queries and errors
        log_analysis = self._analyze_logs()
        report['logs'] = log_analysis

        # Compile summary
        all_issues = issues + log_analysis.get('issues', [])
        report['summary'] = {
            'overall_health': self._assess_health(all_issues),
            'issues_found': len(all_issues),
            'critical_issues': sum(1 for i in all_issues if i.get('severity') == 'critical'),
            'warning_issues': sum(1 for i in all_issues if i.get('severity') == 'warning'),
            'info_issues': sum(1 for i in all_issues if i.get('severity') == 'info'),
            'recommendations': self._generate_recommendations(all_issues),
        }

        return report

    # ── Database Analysis ────────────────────────────────────────────────

    def _analyze_database(self):
        """Analyze database performance metrics."""
        result = {'status': 'ok', 'metrics': {}, 'issues': []}

        try:
            with connection.cursor() as cursor:
                # Active connections
                cursor.execute("""
                    SELECT count(*) as total,
                           count(*) FILTER (WHERE state = 'active') as active,
                           count(*) FILTER (WHERE state = 'idle') as idle,
                           count(*) FILTER (WHERE wait_event IS NOT NULL) as waiting
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                """)
                conn_stats = cursor.fetchone()
                result['metrics']['connections'] = {
                    'total': conn_stats[0],
                    'active': conn_stats[1],
                    'idle': conn_stats[2],
                    'waiting': conn_stats[3],
                }

                # Connection utilization
                pool_max = getattr(settings, 'DB_POOL_MAX_SIZE', 80)
                util_pct = (conn_stats[0] / pool_max * 100) if pool_max > 0 else 0
                result['metrics']['pool_utilization_percent'] = round(util_pct, 1)

                if util_pct > 80:
                    result['issues'].append({
                        'severity': 'warning',
                        'area': 'database',
                        'message': f'Database connection pool at {util_pct:.0f}% utilization ({conn_stats[0]}/{pool_max})',
                        'recommendation': 'Increase DB_POOL_MAX_SIZE or add more app instances',
                    })

                # Long-running queries
                cursor.execute("""
                    SELECT pid, now() - pg_stat_activity.query_start AS duration,
                           query, state
                    FROM pg_stat_activity
                    WHERE state = 'active'
                      AND query NOT LIKE '%pg_stat_activity%'
                      AND query_start < now() - interval '5 seconds'
                    ORDER BY duration DESC
                    LIMIT 10
                """)
                long_queries = cursor.fetchall()
                if long_queries:
                    result['metrics']['long_running_queries'] = [
                        {
                            'pid': q[0],
                            'duration_seconds': round(q[1].total_seconds(), 1) if q[1] else 0,
                            'query': q[2][:200],
                            'state': q[3],
                        }
                        for q in long_queries
                    ]
                    result['issues'].append({
                        'severity': 'warning' if len(long_queries) > 3 else 'info',
                        'area': 'database',
                        'message': f'{len(long_queries)} long-running queries detected (>5s)',
                        'recommendation': 'Check for missing indexes or inefficient queries',
                    })

                # Database size
                cursor.execute("SELECT pg_database_size(current_database())")
                db_size = cursor.fetchone()[0]
                result['metrics']['database_size_bytes'] = db_size
                result['metrics']['database_size_mb'] = round(db_size / (1024 * 1024), 1)
                result['metrics']['database_size_gb'] = round(db_size / (1024 ** 3), 2)

                # Cache hit ratio (PostgreSQL shared buffers)
                cursor.execute("""
                    SELECT
                        sum(blks_hit)::numeric / (sum(blks_hit) + sum(blks_read))::numeric
                        AS cache_hit_ratio
                    FROM pg_stat_database
                    WHERE datname = current_database()
                """)
                hit_ratio = cursor.fetchone()[0]
                if hit_ratio:
                    result['metrics']['pg_cache_hit_ratio'] = round(float(hit_ratio) * 100, 2)
                    if float(hit_ratio) < 0.95:
                        result['issues'].append({
                            'severity': 'warning',
                            'area': 'database',
                            'message': f'PostgreSQL cache hit ratio is {float(hit_ratio)*100:.1f}% (< 95%)',
                            'recommendation': 'Increase shared_buffers in PostgreSQL configuration',
                        })

                # Index usage statistics
                cursor.execute("""
                    SELECT
                        schemaname, tablename, indexname,
                        idx_scan, idx_tup_read, idx_tup_fetch
                    FROM pg_stat_user_indexes
                    WHERE idx_scan = 0
                      AND schemaname = 'public'
                    ORDER BY tablename
                    LIMIT 20
                """)
                unused_indexes = cursor.fetchall()
                if unused_indexes:
                    result['metrics']['unused_indexes'] = [
                        {'table': idx[1], 'index': idx[2]}
                        for idx in unused_indexes
                    ]
                    result['issues'].append({
                        'severity': 'info',
                        'area': 'database',
                        'message': f'{len(unused_indexes)} unused indexes found',
                        'recommendation': 'Consider removing unused indexes to improve write performance',
                    })

                # Table size statistics
                cursor.execute("""
                    SELECT
                        relname as table_name,
                        pg_size_pretty(pg_total_relation_size(relid)) as total_size,
                        n_live_tup as row_count,
                        n_dead_tup as dead_rows,
                        round(100 * n_dead_tup / GREATEST(n_live_tup + n_dead_tup, 1), 1) as dead_pct
                    FROM pg_stat_user_tables
                    WHERE n_dead_tup > 1000
                    ORDER BY n_dead_tup DESC
                    LIMIT 10
                """)
                table_stats = cursor.fetchall()
                if table_stats:
                    result['metrics']['tables_needing_vacuum'] = [
                        {
                            'table': t[0],
                            'size': t[1],
                            'live_rows': t[2],
                            'dead_rows': t[3],
                            'dead_percent': t[4],
                        }
                        for t in table_stats
                        if t[4] > 20  # Only flag if > 20% dead rows
                    ]

        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            result['issues'].append({
                'severity': 'critical',
                'area': 'database',
                'message': f'Failed to analyze database: {e}',
                'recommendation': 'Check database connectivity and permissions',
            })

        return result

    # ── Cache Analysis ───────────────────────────────────────────────────

    def _analyze_cache(self):
        """Analyze Redis/cache performance metrics."""
        result = {'status': 'ok', 'metrics': {}, 'issues': []}

        try:
            # Check cache connectivity
            cache.set('perf_analysis_ping', 'pong', timeout=5)
            ping_result = cache.get('perf_analysis_ping')
            if ping_result != 'pong':
                result['status'] = 'error'
                result['issues'].append({
                    'severity': 'critical',
                    'area': 'cache',
                    'message': 'Cache (Redis) is not responding correctly',
                    'recommendation': 'Check Redis server status and connectivity',
                })
                return result

            # Get cache metrics
            from cfbc.cache_utils import CacheMetrics, CacheVersion
            cache_stats = CacheMetrics.get_stats()
            result['metrics']['hit_ratio'] = round(cache_stats.get('hit_ratio', 0) * 100, 2)
            result['metrics']['hits'] = cache_stats.get('hits', 0)
            result['metrics']['misses'] = cache_stats.get('misses', 0)
            result['metrics']['versions'] = cache_stats.get('versions', {})

            # Analyze cache hit ratio
            hit_ratio = result['metrics']['hit_ratio']
            if hit_ratio < 60:
                result['issues'].append({
                    'severity': 'warning',
                    'area': 'cache',
                    'message': f'Low cache hit ratio: {hit_ratio:.1f}% (< 60%)',
                    'recommendation': 'Increase cache TTLs or add cache warming for frequent queries',
                })
            elif hit_ratio < 80:
                result['issues'].append({
                    'severity': 'info',
                    'area': 'cache',
                    'message': f'Moderate cache hit ratio: {hit_ratio:.1f}% (< 80%)',
                    'recommendation': 'Consider adding cache warming for top-N most accessed pages',
                })

            # Get Redis INFO stats via raw connection
            try:
                client = cache.client.get_client()
                info = client.info()
                result['metrics']['redis'] = {
                    'used_memory_human': info.get('used_memory_human', 'N/A'),
                    'used_memory_peak_human': info.get('used_memory_peak_human', 'N/A'),
                    'total_connections_received': info.get('total_connections_received', 0),
                    'connected_clients': info.get('connected_clients', 0),
                    'uptime_in_days': info.get('uptime_in_days', 0),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0),
                    'expired_keys': info.get('expired_keys', 0),
                    'evicted_keys': info.get('evicted_keys', 0),
                }

                # Check for evictions
                evicted = info.get('evicted_keys', 0)
                if evicted > 1000:
                    result['issues'].append({
                        'severity': 'warning',
                        'area': 'cache',
                        'message': f'Redis has evicted {evicted} keys - memory may be insufficient',
                        'recommendation': 'Increase Redis maxmemory or reduce cache TTLs',
                    })

            except Exception:
                pass

        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            result['issues'].append({
                'severity': 'critical',
                'area': 'cache',
                'message': f'Failed to analyze cache: {e}',
                'recommendation': 'Check Redis configuration and connectivity',
            })

        return result

    # ── Request Analysis ─────────────────────────────────────────────────

    def _analyze_requests(self):
        """Analyze request metrics from Redis."""
        result = {'status': 'ok', 'metrics': {}, 'issues': []}

        try:
            # Get request metrics from last N minutes
            now = datetime.now()
            total_requests = 0
            slow_requests = 0
            error_requests = 0
            path_stats = defaultdict(lambda: {'count': 0, 'total_time': 0.0, 'errors': 0})

            for minute_offset in range(self.minutes):
                minute_key = (now - timedelta(minutes=minute_offset)).strftime('%Y-%m-%dT%H:%M')

                # Request counts per path
                requests_data = cache.hgetall(f'cfbc:metrics:requests:{minute_key}')
                if requests_data:
                    for path, count in requests_data.items():
                        path_str = path.decode('utf-8') if isinstance(path, bytes) else path
                        count_int = int(count.decode('utf-8') if isinstance(count, bytes) else count)
                        path_stats[path_str]['count'] += count_int
                        total_requests += count_int

                # Duration data
                duration_data = cache.hgetall(f'cfbc:metrics:duration:{minute_key}')
                if duration_data:
                    for key_value_pair, value in duration_data.items():
                        try:
                            kv = key_value_pair.decode('utf-8') if isinstance(key_value_pair, bytes) else key_value_pair
                            val = float(value.decode('utf-8') if isinstance(value, bytes) else value)
                            path_part, metric_type = kv.rsplit(':', 1)
                            if metric_type == 'sum':
                                path_stats[path_part]['total_time'] += val
                        except (ValueError, UnicodeDecodeError):
                            pass

                # Status codes (errors = 5xx)
                status_data = cache.hgetall(f'cfbc:metrics:status:{minute_key}')
                if status_data:
                    for status_group, count in status_data.items():
                        sg = status_group.decode('utf-8') if isinstance(status_group, bytes) else status_group
                        cnt = int(count.decode('utf-8') if isinstance(count, bytes) else count)
                        if sg == '5xx':
                            error_requests += cnt

            # Compile request metrics
            if total_requests > 0:
                result['metrics']['total_requests'] = total_requests
                result['metrics']['avg_minute_rate'] = round(total_requests / max(self.minutes, 1), 1)
                result['metrics']['error_rate_percent'] = round(
                    (error_requests / total_requests) * 100, 2
                )
                result['metrics']['error_count'] = error_requests

                # Top 10 most requested paths
                sorted_paths = sorted(
                    path_stats.items(),
                    key=lambda x: x[1]['count'],
                    reverse=True
                )[:10]
                result['metrics']['top_paths'] = [
                    {
                        'path': path,
                        'requests': stats['count'],
                        'avg_duration_ms': round(
                            (stats['total_time'] / stats['count']) * 1000, 1
                        ) if stats['count'] > 0 else 0,
                    }
                    for path, stats in sorted_paths
                ]

                # Analyze error rate
                error_rate = result['metrics']['error_rate_percent']
                if error_rate > 5:
                    result['issues'].append({
                        'severity': 'critical' if error_rate > 10 else 'warning',
                        'area': 'requests',
                        'message': f'High error rate: {error_rate:.1f}% ({error_requests} errors in {self.minutes} min)',
                        'recommendation': 'Check application logs for 5xx errors and fix underlying issues',
                    })

                # Check for slow paths
                slow_paths = [
                    p for p in result['metrics']['top_paths']
                    if p['avg_duration_ms'] > 2000
                ]
                if slow_paths:
                    result['metrics']['slow_paths'] = slow_paths
                    result['issues'].append({
                        'severity': 'warning',
                        'area': 'requests',
                        'message': f'{len(slow_paths)} endpoint(s) with avg duration > 2s',
                        'recommendation': 'Check for N+1 queries or missing indexes on slow paths',
                    })

            # Analyze from log files as well (reuse _analyze_logs result)
            log_analysis = report.get('logs', {})
            slow_requests_count = (
                log_analysis.get('metrics', {})
                .get('performance_log', {})
                .get('slow_requests', 0)
            )
            if slow_requests_count > 10:
                result['metrics']['slow_requests_in_logs'] = slow_requests_count
                result['issues'].append({
                    'severity': 'info',
                    'area': 'requests',
                    'message': f'{slow_requests_count} slow requests (>2s) found in log files',
                    'recommendation': 'Review logs/performance.log for specific slow requests',
                })

        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            result['issues'].append({
                'severity': 'warning',
                'area': 'requests',
                'message': f'Request analysis limited: {e}',
                'recommendation': 'Metrics may not be fully collected; check RequestTimingMiddleware',
            })

        return result

    # ── System Analysis ──────────────────────────────────────────────────

    def _analyze_system(self):
        """Analyze system-level performance metrics."""
        result = {'status': 'ok', 'metrics': {}, 'issues': []}

        try:
            import psutil

            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            result['metrics']['cpu'] = {
                'percent': cpu_percent,
                'physical_cores': psutil.cpu_count(logical=False),
                'logical_cores': cpu_count,
                'load_avg': [round(x, 2) for x in psutil.getloadavg()] if hasattr(psutil, 'getloadavg') else [],
            }

            if cpu_percent > 80:
                result['issues'].append({
                    'severity': 'warning',
                    'area': 'system',
                    'message': f'High CPU usage: {cpu_percent}%',
                    'recommendation': 'Consider scaling up app instances or optimizing computation-heavy views',
                })

            # Memory
            memory = psutil.virtual_memory()
            result['metrics']['memory'] = {
                'total_gb': round(memory.total / (1024 ** 3), 2),
                'available_gb': round(memory.available / (1024 ** 3), 2),
                'percent': memory.percent,
            }

            if memory.percent > 85:
                result['issues'].append({
                    'severity': 'warning',
                    'area': 'system',
                    'message': f'High memory usage: {memory.percent}% ({memory.available / (1024**3):.1f} GB available)',
                    'recommendation': 'Increase system memory or reduce per-instance memory limits',
                })

            # Disk
            disk = psutil.disk_usage('/')
            result['metrics']['disk'] = {
                'total_gb': round(disk.total / (1024 ** 3), 2),
                'used_gb': round(disk.used / (1024 ** 3), 2),
                'free_gb': round(disk.free / (1024 ** 3), 2),
                'percent': disk.percent,
            }

            if disk.percent > 90:
                result['issues'].append({
                    'severity': 'critical' if disk.percent > 95 else 'warning',
                    'area': 'system',
                    'message': f'Low disk space: {disk.percent}% used ({disk.free / (1024**3):.1f} GB free)',
                    'recommendation': 'Clean up old logs, static files, or increase disk size',
                })

            # Network I/O
            net_io = psutil.net_io_counters()
            result['metrics']['network'] = {
                'bytes_sent_mb': round(net_io.bytes_sent / (1024 * 1024), 1),
                'bytes_recv_mb': round(net_io.bytes_recv / (1024 * 1024), 1),
            }

        except ImportError:
            # psutil not installed - try os module fallback
            result['status'] = 'limited'
            result['metrics']['note'] = 'psutil not installed; limited system metrics available'
            try:
                import os as os_module
                if hasattr(os_module, 'getloadavg'):
                    load = os_module.getloadavg()
                    result['metrics']['cpu_load_avg'] = [round(x, 2) for x in load]
            except Exception:
                pass

        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)

        return result

    # ── Celery Analysis ─────────────────────────────────────────────────

    def _analyze_celery(self):
        """Analyze Celery worker and task queue performance."""
        result = {'status': 'ok', 'metrics': {}, 'issues': []}

        try:
            from celery import current_app

            # Ping workers
            inspect = current_app.control.inspect(timeout=2.0)
            if inspect:
                stats = inspect.stats()
                if stats:
                    workers = list(stats.keys())
                    result['metrics']['active_workers'] = workers
                    result['metrics']['worker_count'] = len(workers)

                    # Aggregate worker stats
                    total_tasks = 0
                    for worker_name, worker_stats in stats.items():
                        total_tasks += worker_stats.get('total', {}).get('tasks', {}).get('total', 0)

                    result['metrics']['total_processed'] = total_tasks
                else:
                    result['status'] = 'degraded'
                    result['metrics']['worker_count'] = 0
                    result['issues'].append({
                        'severity': 'warning',
                        'area': 'celery',
                        'message': 'No Celery workers responding to ping',
                        'recommendation': 'Start Celery workers: celery -A cfbc worker -l info',
                    })
            else:
                result['status'] = 'degraded'
                result['issues'].append({
                    'severity': 'warning',
                    'area': 'celery',
                    'message': 'Celery inspect returned no data',
                    'recommendation': 'Check Celery worker status and broker connection',
                })

            # Check queue lengths via Redis
            try:
                from redis import Redis
                redis_client = Redis.from_url(settings.CELERY_BROKER_URL)
                queues = ['email', 'file_processing', 'reports', 'default', 'maintenance', 'backup']
                queue_lengths = {}
                for queue in queues:
                    length = redis_client.llen(queue)
                    if length > 0:
                        queue_lengths[queue] = length

                if queue_lengths:
                    result['metrics']['queue_lengths'] = queue_lengths
                    for queue, length in queue_lengths.items():
                        if length > 100:
                            result['issues'].append({
                                'severity': 'warning' if length > 500 else 'info',
                                'area': 'celery',
                                'message': f'Queue "{queue}" has {length} pending tasks',
                                'recommendation': f'Increase worker concurrency for "{queue}" queue',
                            })
            except Exception:
                pass

        except ImportError:
            result['status'] = 'limited'
            result['metrics']['note'] = 'Celery not available in this environment'

        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)

        return result

    # ── Log Analysis ─────────────────────────────────────────────────────

    def _analyze_logs(self):
        """Analyze log files for performance issues."""
        result = {'metrics': {}, 'issues': []}

        log_dir = Path(self.log_dir)
        if not log_dir.exists():
            result['metrics']['note'] = f'Log directory not found: {self.log_dir}'
            return result

        # Analyze performance logs
        perf_log = log_dir / 'performance.log'
        if perf_log.exists():
            slow_requests = 0
            slow_queries = 0
            high_query_counts = 0

            try:
                with open(perf_log, 'r', encoding='utf-8') as f:
                    for line in f:
                        if 'SLOW REQUEST' in line:
                            slow_requests += 1
                        elif 'SLOW QUERY' in line:
                            slow_queries += 1
                        elif 'HIGH DB QUERIES' in line:
                            high_query_counts += 1
            except Exception:
                pass

            result['metrics']['performance_log'] = {
                'slow_requests': slow_requests,
                'slow_queries': slow_queries,
                'high_query_counts': high_query_counts,
            }

            if slow_queries > 10:
                result['issues'].append({
                    'severity': 'warning',
                    'area': 'logs',
                    'message': f'{slow_queries} slow queries logged in performance.log',
                    'recommendation': 'Review slow queries for missing indexes or optimization opportunities',
                })

        # Analyze error logs
        err_log = log_dir / 'errors.log'
        if err_log.exists():
            error_count = 0
            error_types = defaultdict(int)
            try:
                with open(err_log, 'r', encoding='utf-8') as f:
                    for line in f:
                        if '"level":"ERROR"' in line or ' ERROR ' in line:
                            error_count += 1
                        # Categorize errors
                        for err_type in ['OperationalError', 'Timeout', 'ConnectionError',
                                         'IntegrityError', 'DoesNotExist', 'MultipleObjectsReturned']:
                            if err_type in line:
                                error_types[err_type] += 1
            except Exception:
                pass

            result['metrics']['error_log'] = {
                'total_errors': error_count,
                'error_types': dict(error_types),
            }

        return result

    # ── Helper Methods ───────────────────────────────────────────────────

    def _assess_health(self, issues):
        """Assess overall system health based on issues found."""
        critical = sum(1 for i in issues if i.get('severity') == 'critical')
        warnings = sum(1 for i in issues if i.get('severity') == 'warning')

        if critical > 0:
            return 'critical'
        elif warnings > 0:
            return 'degraded'
        else:
            return 'healthy'

    def _generate_recommendations(self, issues):
        """Generate prioritized recommendations from issues."""
        recommendations = []

        # Group by severity
        for severity in ['critical', 'warning', 'info']:
            severity_issues = [i for i in issues if i.get('severity') == severity]
            if severity_issues:
                recommendations.append({
                    'priority': severity.upper(),
                    'count': len(severity_issues),
                    'recommendations': list(set(
                        i.get('recommendation', '') for i in severity_issues
                        if i.get('recommendation')
                    )),
                })

        if not recommendations:
            recommendations.append({
                'priority': 'INFO',
                'message': 'No specific performance issues detected. System appears healthy.',
            })

        return recommendations

    # ── Output ───────────────────────────────────────────────────────────

    def _output_report(self, report):
        """Output the report in the requested format."""
        if self.output_format == 'json':
            self.stdout.write(json.dumps(report, indent=2, default=str))
        else:
            self._output_text(report)

    def _output_text(self, report):
        """Output the report as formatted text."""
        summary = report.get('summary', {})
        health = summary.get('overall_health', 'unknown')
        health_color = self.style.SUCCESS if health == 'healthy' else (
            self.style.WARNING if health == 'degraded' else self.style.ERROR
        )

        self.stdout.write(health_color(f"\n  Overall Health: {health.upper()}"))
        self.stdout.write(f"  Issues: {summary.get('issues_found', 0)} total "
                          f"({summary.get('critical_issues', 0)} critical, "
                          f"{summary.get('warning_issues', 0)} warnings, "
                          f"{summary.get('info_issues', 0)} info)")

        # Database section
        if 'database' in report:
            db = report['database']
            self.stdout.write(self.style.MIGRATE_HEADING("\n  📊 Database"))
            metrics = db.get('metrics', {})
            if metrics.get('connections'):
                conns = metrics['connections']
                self.stdout.write(f"     Connections: {conns.get('active', '?')} active, "
                                  f"{conns.get('idle', '?')} idle, "
                                  f"{conns.get('waiting', '?')} waiting")
                self.stdout.write(f"     Pool utilization: {metrics.get('pool_utilization_percent', '?')}%")
            if metrics.get('database_size_gb'):
                self.stdout.write(f"     DB size: {metrics['database_size_gb']} GB")
            if metrics.get('pg_cache_hit_ratio'):
                self.stdout.write(f"     Pg cache hit ratio: {metrics['pg_cache_hit_ratio']}%")
            if metrics.get('long_running_queries'):
                self.stdout.write(f"     Long-running queries: {len(metrics['long_running_queries'])}")

        # Cache section
        if 'cache' in report:
            cache_data = report['cache']
            self.stdout.write(self.style.MIGRATE_HEADING("\n  💾 Cache"))
            metrics = cache_data.get('metrics', {})
            if metrics.get('hit_ratio') is not None:
                self.stdout.write(f"     Hit ratio: {metrics['hit_ratio']:.1f}%")
                self.stdout.write(f"     Hits: {metrics.get('hits', 0)}, "
                                  f"Misses: {metrics.get('misses', 0)}")
            redis_info = metrics.get('redis', {})
            if redis_info:
                self.stdout.write(f"     Redis memory: {redis_info.get('used_memory_human', '?')} "
                                  f"(peak: {redis_info.get('used_memory_peak_human', '?')})")
                self.stdout.write(f"     Connected clients: {redis_info.get('connected_clients', '?')}")
                if redis_info.get('evicted_keys', 0) > 0:
                    self.stdout.write(self.style.WARNING(
                        f"     ⚠ Evicted keys: {redis_info['evicted_keys']}"
                    ))

        # Requests section
        if 'requests' in report:
            req = report['requests']
            self.stdout.write(self.style.MIGRATE_HEADING("\n  🌐 Requests"))
            metrics = req.get('metrics', {})
            if metrics.get('total_requests'):
                self.stdout.write(f"     Total: {metrics['total_requests']} requests "
                                  f"(avg {metrics.get('avg_minute_rate', '?')}/min)")
                self.stdout.write(f"     Error rate: {metrics.get('error_rate_percent', '?')}%")
                if metrics.get('top_paths'):
                    self.stdout.write("     Top paths:")
                    for path_info in metrics['top_paths'][:5]:
                        self.stdout.write(
                            f"       {path_info['path']}: {path_info['requests']} req, "
                            f"{path_info['avg_duration_ms']}ms avg"
                        )

        # System section
        if 'system' in report:
            sys_data = report['system']
            self.stdout.write(self.style.MIGRATE_HEADING("\n  🖥 System"))
            metrics = sys_data.get('metrics', {})
            cpu = metrics.get('cpu', {})
            if cpu:
                self.stdout.write(f"     CPU: {cpu.get('percent', '?')}% "
                                  f"({cpu.get('logical_cores', '?')} cores)")
            mem = metrics.get('memory', {})
            if mem:
                self.stdout.write(f"     Memory: {mem.get('percent', '?')}% used "
                                  f"({mem.get('available_gb', '?')} GB free)")
            disk = metrics.get('disk', {})
            if disk:
                self.stdout.write(f"     Disk: {disk.get('percent', '?')}% used "
                                  f"({disk.get('free_gb', '?')} GB free)")

        # Celery section
        if 'celery' in report:
            celery_data = report['celery']
            self.stdout.write(self.style.MIGRATE_HEADING("\n  ⚙ Celery"))
            metrics = celery_data.get('metrics', {})
            if metrics.get('worker_count') is not None:
                self.stdout.write(f"     Workers: {metrics['worker_count']}")
            queue_lengths = metrics.get('queue_lengths', {})
            if queue_lengths:
                self.stdout.write("     Queue lengths:")
                for queue, length in queue_lengths.items():
                    color = self.style.WARNING if length > 100 else self.style.SUCCESS
                    self.stdout.write(color(f"       {queue}: {length} tasks"))

        # Issues
        all_issues = []
        for section in ['database', 'cache', 'requests', 'system', 'celery', 'logs']:
            section_data = report.get(section, {})
            all_issues.extend(section_data.get('issues', []))

        if all_issues:
            self.stdout.write(self.style.MIGRATE_HEADING("\n  ⚠ Issues Found"))
            for issue in sorted(all_issues, key=lambda x: (
                {'critical': 0, 'warning': 1, 'info': 2}.get(x.get('severity', 'info'), 3)
            )):
                severity = issue.get('severity', 'info')
                color = self.style.ERROR if severity == 'critical' else (
                    self.style.WARNING if severity == 'warning' else self.style.NOTICE
                )
                self.stdout.write(color(f"     [{severity.upper()}] {issue.get('area', '')}: "
                                         f"{issue.get('message', '')}"))

        # Recommendations
        recommendations = summary.get('recommendations', [])
        if recommendations:
            self.stdout.write(self.style.MIGRATE_HEADING("\n  💡 Recommendations"))
            for rec in recommendations:
                priority = rec.get('priority', 'INFO')
                color = self.style.ERROR if priority == 'CRITICAL' else (
                    self.style.WARNING if priority == 'WARNING' else self.style.SUCCESS
                )
                recs = rec.get('recommendations', [])
                if recs:
                    for r in recs:
                        self.stdout.write(color(f"     [{priority}] {r}"))

        self.stdout.write('')
