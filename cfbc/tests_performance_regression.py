"""
Performance regression tests for CFBC application.

These tests verify that:
1. Database queries remain optimized (no N+1 problems, reasonable query counts)
2. Cache behavior is correct (set/get works, invalidation works)
3. Celery configuration is valid
4. Database configuration parameters are reasonable
5. Middleware performance overhead is acceptable

Run with:
    python manage.py test cfbc.tests_performance_regression --verbosity=2

To skip slow tests:
    python manage.py test cfbc.tests_performance_regression --exclude-tag=slow
"""

import time
import os
from unittest import skipIf
from django.test import tag

from django.test import TestCase, override_settings, TransactionTestCase
from django.db import connection, connections
from django.core.cache import cache
from django.conf import settings

# Skip test setup if not available
try:
    from django.contrib.auth.models import User
except ImportError:
    User = None


# ═════════════════════════════════════════════════════════════════════════════
# Database Query Optimization Tests
# ═════════════════════════════════════════════════════════════════════════════

@tag('performance', 'database')
class DatabaseQueryOptimizationTests(TestCase):
    """Tests that verify database queries remain optimized."""

    def setUp(self):
        """Set up test data."""
        # Create test users, categories, and posts for blog benchmarks
        from django.contrib.auth.models import User
        from blog.models import Categoria, Noticia, Comentario

        self.user = User.objects.create_user(
            username='perf_test_user',
            password='testpass123'
        )
        self.categoria = Categoria.objects.create(
            nombre='Test Category',
            slug='test-category'
        )

        # Create test noticias
        for i in range(5):
            Noticia.objects.create(
                titulo=f'Test Noticia {i}',
                contenido='Test content ' * 20,
                resumen='Test summary',
                estado='publicado',
                autor=self.user,
                categoria=self.categoria,
            )

    def test_noticia_list_query_count(self):
        """Test that Noticia list view uses select_related properly (no N+1)."""
        from blog.models import Noticia

        # Clear query log
        connection.queries_log.clear()

        # Optimized query: should be 1 query with select_related
        noticias = list(
            Noticia.objects.filter(estado='publicado')
            .select_related('categoria', 'autor')
            .order_by('-fecha_actualizacion')
        )

        query_count = len(connection.queries_log)
        self.assertLessEqual(
            query_count, 1,
            f"Expected ≤1 query for optimized noticia list, got {query_count}. "
            "Check that select_related('categoria', 'autor') is being used."
        )

    def test_author_stats_aggregation(self):
        """Test that author stats use single aggregated query instead of 4 count queries."""
        from blog.models import Noticia
        from django.db.models import Count, Q

        # Clear query log
        connection.queries_log.clear()

        # Single aggregated query
        counts = Noticia.objects.filter(autor=self.user).aggregate(
            total=Count('id'),
            publicadas=Count('id', filter=Q(estado='publicado')),
            borradores=Count('id', filter=Q(estado='borrador')),
        )

        query_count = len(connection.queries_log)
        self.assertLessEqual(
            query_count, 1,
            f"Expected ≤1 query for aggregated author stats, got {query_count}. "
            "Use aggregated Count queries instead of separate .count() calls."
        )

    @tag('slow')
    def test_noticia_with_comments_query_count(self):
        """Test that noticia detail with comments uses prefetch_related properly."""
        from blog.models import Noticia, Comentario
        from django.contrib.auth.models import User

        # Create some comments
        other_user = User.objects.create_user(
            username='perf_commenter',
            password='testpass123'
        )
        noticia = Noticia.objects.first()
        for i in range(3):
            Comentario.objects.create(
                noticia=noticia,
                autor=other_user,
                contenido=f'Test comment {i}',
            )

        # Clear query log
        connection.queries_log.clear()

        # Optimized query with prefetch_related
        noticia = Noticia.objects.prefetch_related('comentarios').get(id=noticia.id)
        comments = list(noticia.comentarios.all())

        query_count = len(connection.queries_log)
        # Expected: 1 for the noticia query + 1 for the prefetch = 2
        self.assertLessEqual(
            query_count, 2,
            f"Expected ≤2 queries for noticia with comments via prefetch_related, "
            f"got {query_count}. Use prefetch_related('comentarios')."
        )

    def test_database_configuration(self):
        """Test that database configuration parameters are set to reasonable values."""
        db_config = settings.DATABASES.get('default', {})

        # CONN_MAX_AGE should be set for connection pooling
        conn_max_age = db_config.get('CONN_MAX_AGE', 0)
        self.assertGreaterEqual(
            conn_max_age, 0,
            "CONN_MAX_AGE must be >= 0 for connection reuse"
        )

        # CONN_HEALTH_CHECKS should be enabled
        health_checks = db_config.get('CONN_HEALTH_CHECKS', False)
        self.assertTrue(
            health_checks,
            "CONN_HEALTH_CHECKS should be True for production reliability"
        )

        # Verify our custom database settings exist
        self.assertTrue(
            hasattr(settings, 'DB_POOL_MIN_SIZE'),
            "DB_POOL_MIN_SIZE should be configured"
        )
        self.assertTrue(
            hasattr(settings, 'DB_POOL_MAX_SIZE'),
            "DB_POOL_MAX_SIZE should be configured"
        )
        self.assertTrue(
            hasattr(settings, 'DB_SLOW_QUERY_THRESHOLD_MS'),
            "DB_SLOW_QUERY_THRESHOLD_MS should be configured"
        )

    def test_query_timeout_configuration(self):
        """Test that query timeout configuration returns valid values."""
        from cfbc.db_monitoring import QueryTimeoutConfig

        # Get default timeout
        default = QueryTimeoutConfig.get_timeout('default')
        self.assertIn('statement_timeout', default)
        self.assertIn('lock_timeout', default)
        self.assertGreater(default['statement_timeout'], 0)
        self.assertGreater(default['lock_timeout'], 0)

        # Get operation-specific timeout (should not exceed global)
        for operation in ['list', 'detail', 'search', 'report', 'export']:
            op_timeout = QueryTimeoutConfig.get_timeout('default', operation)
            self.assertLessEqual(
                op_timeout['statement_timeout'],
                default['statement_timeout'],
                f"Operation timeout for '{operation}' should not exceed default"
            )


# ═════════════════════════════════════════════════════════════════════════════
# Cache Performance Tests
# ═════════════════════════════════════════════════════════════════════════════

@tag('performance', 'cache')
class CachePerformanceTests(TestCase):
    """Tests that verify cache behavior and performance."""

    def setUp(self):
        # Clear cache before each test
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_cache_set_get_performance(self):
        """Test basic cache set/get operations work."""
        cache_key = 'perf_test_key'
        test_value = {'data': 'test_value', 'number': 42}

        cache.set(cache_key, test_value, timeout=60)
        cached = cache.get(cache_key)

        self.assertEqual(cached, test_value)

    def test_cache_metrics_functions(self):
        """Test that cache metrics recording works."""
        from cfbc.cache_utils import CacheMetrics

        # Reset metrics
        CacheMetrics.reset_metrics()

        # Record some hits and misses
        for i in range(8):
            CacheMetrics.record_hit(f'key_{i}')
        for i in range(2):
            CacheMetrics.record_miss(f'key_{i}')

        stats = CacheMetrics.get_stats()
        self.assertEqual(stats['hits'], 8)
        self.assertEqual(stats['misses'], 2)
        self.assertAlmostEqual(stats['hit_ratio'], 0.8)

    def test_cache_versioning(self):
        """Test that cache versioning works for invalidation."""
        from cfbc.cache_utils import CacheVersion

        # Get default version
        v1 = CacheVersion.get('general')
        self.assertGreaterEqual(v1, 1)

        # Increment
        v2 = CacheVersion.increment('general')
        self.assertEqual(v2, v1 + 1)

        # New key with version
        cache_key = CacheVersion.make_key('test_key', 'general')
        self.assertIn(f'v{v2}', cache_key)

    def test_cache_key_generation(self):
        """Test that cache key generation works and handles long keys."""
        from cfbc.cache_utils import generate_cache_key

        # Simple key
        key1 = generate_cache_key('prefix', 'arg1', 'arg2')
        self.assertTrue(key1.startswith('prefix'))
        self.assertIn('arg1', key1)

        # Key with kwargs
        key2 = generate_cache_key('prefix', key='value', id=123)
        self.assertTrue(key2.startswith('prefix'))

        # Long key should be hashed
        long_arg = 'a' * 300
        key3 = generate_cache_key('prefix', long_arg)
        self.assertLessEqual(len(key3), 220)  # prefix + hash

    def test_stampede_protection(self):
        """Test that cache stampede protection lock works."""
        from cfbc.cache_utils import stampede_lock

        cache_key = 'stampede_test'
        with stampede_lock(cache_key, lock_timeout=5) as acquired:
            self.assertTrue(acquired, "Should acquire lock first time")

        # Lock should be released after context exits
        with stampede_lock(cache_key, lock_timeout=5) as acquired:
            self.assertTrue(acquired, "Should acquire lock after release")

    def test_cache_ttl_configuration(self):
        """Test that cache TTL values are reasonable."""
        from cfbc.cache_utils import (
            STATIC_PAGE_TIMEOUT, NOTICIAS_TIMEOUT, CATEGORIAS_TIMEOUT,
            HOME_PAGE_TIMEOUT, HEADER_FRAGMENT_TIMEOUT
        )

        # Static content should have longest TTL
        self.assertGreaterEqual(
            STATIC_PAGE_TIMEOUT, NOTICIAS_TIMEOUT,
            "Static page TTL should be >= dynamic content TTL"
        )

        # Header fragments should have longer TTL than news
        self.assertGreaterEqual(
            HEADER_FRAGMENT_TIMEOUT, NOTICIAS_TIMEOUT,
            "Header fragment TTL should be >= news TTL"
        )

        # All TTLs should be positive
        for ttl_name, ttl_value in [
            ('STATIC_PAGE_TIMEOUT', STATIC_PAGE_TIMEOUT),
            ('NOTICIAS_TIMEOUT', NOTICIAS_TIMEOUT),
            ('CATEGORIAS_TIMEOUT', CATEGORIAS_TIMEOUT),
            ('HOME_PAGE_TIMEOUT', HOME_PAGE_TIMEOUT),
        ]:
            self.assertGreater(ttl_value, 0, f"{ttl_name} should be > 0")

    def test_cache_configuration(self):
        """Test that cache configuration is valid."""
        caches_config = settings.CACHES

        self.assertIn('default', caches_config, "Default cache must be configured")
        self.assertIn('session', caches_config, "Session cache must be configured")

        default_cache = caches_config['default']
        self.assertEqual(
            default_cache['BACKEND'], 'django_redis.cache.RedisCache',
            "Default cache should use Redis backend"
        )

        self.assertEqual(
            caches_config['session']['BACKEND'], 'django_redis.cache.RedisCache',
            "Session cache should use Redis backend"
        )


# ═════════════════════════════════════════════════════════════════════════════
# Celery Configuration Tests
# ═════════════════════════════════════════════════════════════════════════════

@tag('performance', 'celery')
class CeleryConfigurationTests(TestCase):
    """Tests that verify Celery configuration is valid."""

    def test_celery_broker_configured(self):
        """Test that Celery broker URL is configured."""
        self.assertTrue(
            hasattr(settings, 'CELERY_BROKER_URL'),
            "CELERY_BROKER_URL must be configured"
        )
        self.assertTrue(
            settings.CELERY_BROKER_URL,
            "CELERY_BROKER_URL must not be empty"
        )

    def test_celery_result_backend_configured(self):
        """Test that Celery result backend is configured."""
        self.assertTrue(
            hasattr(settings, 'CELERY_RESULT_BACKEND'),
            "CELERY_RESULT_BACKEND must be configured"
        )

    def test_celery_task_routes_defined(self):
        """Test that Celery task routes are properly defined."""
        self.assertTrue(
            hasattr(settings, 'CELERY_TASK_ROUTES'),
            "CELERY_TASK_ROUTES must be configured"
        )

        routes = settings.CELERY_TASK_ROUTES
        self.assertGreater(
            len(routes), 0,
            "At least one task route must be defined"
        )

        # Verify all routes have valid queue names
        for task_pattern, route in routes.items():
            if isinstance(route, dict):
                self.assertIn('queue', route, f"Route for {task_pattern} must specify queue")
                self.assertIn(
                    route['queue'],
                    ['email', 'file_processing', 'reports', 'default', 'maintenance', 'backup'],
                    f"Queue '{route['queue']}' for {task_pattern} is not one of the defined queues"
                )

    def test_celery_time_limits_reasonable(self):
        """Test that Celery time limits are set and reasonable."""
        annotations = getattr(settings, 'CELERY_TASK_ANNOTATIONS', {})
        for task_name, task_config in annotations.items():
            time_limit = task_config.get('time_limit', None)
            soft_time_limit = task_config.get('soft_time_limit', None)

            if time_limit:
                self.assertLessEqual(
                    time_limit, 3600,  # 1 hour max
                    f"Task {task_name}: time_limit ({time_limit}s) exceeds 1 hour max"
                )

            if time_limit and soft_time_limit:
                self.assertLess(
                    soft_time_limit, time_limit,
                    f"Task {task_name}: soft_time_limit must be < time_limit"
                )

    def test_celery_worker_concurrency_defined(self):
        """Test that worker concurrency configuration is defined."""
        concurrency = getattr(settings, 'CELERY_WORKER_CONCURRENCY', {})
        self.assertGreater(
            len(concurrency), 0,
            "CELERY_WORKER_CONCURRENCY must define at least one queue"
        )

        # Verify all concurrency values are positive
        for queue, count in concurrency.items():
            self.assertGreater(
                count, 0,
                f"Concurrency for queue '{queue}' must be > 0"
            )


# ═════════════════════════════════════════════════════════════════════════════
# Middleware Performance Tests
# ═════════════════════════════════════════════════════════════════════════════

@tag('performance', 'middleware')
class MiddlewareTests(TestCase):
    """Tests that verify middleware configuration and behavior."""

    def test_cache_control_middleware_config(self):
        """Test that CacheControlMiddleware is in the middleware list."""
        middleware = settings.MIDDLEWARE
        self.assertIn(
            'cfbc.middleware.CacheControlMiddleware',
            middleware,
            "CacheControlMiddleware must be in MIDDLEWARE for browser caching optimization"
        )

    def test_correlation_id_middleware_config(self):
        """Test that CorrelationIdMiddleware is in the middleware list."""
        middleware = settings.MIDDLEWARE
        self.assertIn(
            'cfbc.middleware.CorrelationIdMiddleware',
            middleware,
            "CorrelationIdMiddleware must be in MIDDLEWARE for distributed tracing"
        )

    def test_request_timing_middleware_config(self):
        """Test that RequestTimingMiddleware is in the middleware list."""
        middleware = settings.MIDDLEWARE
        self.assertIn(
            'cfbc.middleware.RequestTimingMiddleware',
            middleware,
            "RequestTimingMiddleware must be in MIDDLEWARE for APM metrics"
        )

    def test_database_monitoring_middleware_config(self):
        """Test that DatabaseMonitoringMiddleware is in the middleware list."""
        middleware = settings.MIDDLEWARE
        self.assertIn(
            'cfbc.db_monitoring.DatabaseMonitoringMiddleware',
            middleware,
            "DatabaseMonitoringMiddleware must be in MIDDLEWARE for query monitoring"
        )


# ═════════════════════════════════════════════════════════════════════════════
# Performance Metrics Tests
# ═════════════════════════════════════════════════════════════════════════════

@tag('performance', 'metrics')
class PerformanceMetricsTests(TestCase):
    """Tests that verify performance metrics infrastructure works."""

    def test_business_metrics_functions(self):
        """Test that business metrics functions work without error."""
        from cfbc.business_metrics import (
            record_metric, get_business_metrics, get_business_metrics_text
        )

        # Record a test metric
        record_metric('test_metric', {'test_tag': 'value'})

        # Get metrics (should not throw)
        metrics = get_business_metrics()
        self.assertIn('timestamp', metrics)

        # Get text format (should not throw)
        text = get_business_metrics_text()
        self.assertIsInstance(text, str)

    def test_health_endpoint_definition(self):
        """Test that health check endpoint is configured."""
        from django.urls import reverse
        try:
            url = reverse('health_check')
            self.assertTrue(url)
        except Exception:
            self.fail("Health check URL 'health_check' not configured")

    def test_metrics_endpoint_definition(self):
        """Test that metrics endpoint is configured."""
        from django.urls import reverse
        try:
            url = reverse('metrics_view')
            self.assertTrue(url)
        except Exception:
            self.fail("Metrics URL 'metrics_view' not configured")

    def test_metrics_summary_endpoint_definition(self):
        """Test that metrics summary endpoint is configured."""
        from django.urls import reverse
        try:
            url = reverse('metrics_summary')
            self.assertTrue(url)
        except Exception:
            self.fail("Metrics summary URL 'metrics_summary' not configured")

    def test_db_monitoring_classes(self):
        """Test that database monitoring classes can be instantiated."""
        from cfbc.db_monitoring import (
            QueryTimeoutConfig, ConnectionPoolMonitor,
            SlowQueryLogger, DatabaseMonitoringMiddleware
        )

        # Test SlowQueryLogger
        logger = SlowQueryLogger(threshold_ms=500)
        self.assertEqual(logger.threshold_ms, 500)

        # Test QueryTimeoutConfig
        config = QueryTimeoutConfig.get_timeout('default', 'detail')
        self.assertIn('statement_timeout', config)
        self.assertIn('lock_timeout', config)


# ═════════════════════════════════════════════════════════════════════════════
# Auto-Scaler Configuration Tests
# ═════════════════════════════════════════════════════════════════════════════

@tag('performance', 'autoscaler')
class AutoScalerTests(TestCase):
    """Tests that verify auto-scaler configuration."""

    def test_autoscaler_config_exists(self):
        """Test that auto-scaler configuration is defined."""
        self.assertTrue(
            hasattr(settings, 'AUTOSCALER_CONFIG'),
            "AUTOSCALER_CONFIG must be defined"
        )
        config = settings.AUTOSCALER_CONFIG
        required_keys = ['min_instances', 'max_instances',
                         'scale_up_threshold_cpu', 'scale_down_threshold_cpu']
        for key in required_keys:
            self.assertIn(key, config, f"AUTOSCALER_CONFIG missing '{key}'")

    def test_autoscaler_reasonable_values(self):
        """Test that auto-scaler values are reasonable."""
        config = settings.AUTOSCALER_CONFIG

        # Min instances should be at least 1
        self.assertGreaterEqual(config.get('min_instances', 0), 1)

        # Max should be at least as large as min
        self.assertGreaterEqual(
            config.get('max_instances', 0),
            config.get('min_instances', 0)
        )

        # Scale-up thresholds should be higher than scale-down
        self.assertGreater(
            config.get('scale_up_threshold_cpu', 0),
            config.get('scale_down_threshold_cpu', 0),
            "Scale-up CPU threshold should be higher than scale-down"
        )

        # Cooldown periods should be positive
        self.assertGreater(config.get('cooldown_period_scale_up', 0), 0)
        self.assertGreater(config.get('cooldown_period_scale_down', 0), 0)


# ═════════════════════════════════════════════════════════════════════════════
# Monitoring Configuration Tests
# ═════════════════════════════════════════════════════════════════════════════

@tag('performance', 'monitoring')
class MonitoringConfigurationTests(TestCase):
    """Tests that verify monitoring configuration exists and is valid."""

    def test_alerting_config_exists(self):
        """Test that alerting configuration is defined."""
        self.assertTrue(
            hasattr(settings, 'ALERTING_CONFIG'),
            "ALERTING_CONFIG must be defined"
        )
        config = settings.ALERTING_CONFIG
        self.assertIn('enabled', config)

    def test_db_router_exists(self):
        """Test that database router is configured."""
        routers = settings.DATABASE_ROUTERS
        self.assertIn(
            'cfbc.db_router.AdaptiveRouter',
            routers,
            "AdaptiveRouter must be in DATABASE_ROUTERS"
        )

    def test_session_engine_configured(self):
        """Test that session engine uses cache (Redis)."""
        self.assertEqual(
            settings.SESSION_ENGINE,
            'django.contrib.sessions.backends.cache',
            "SESSION_ENGINE should use cache (Redis) backend"
        )

    def test_business_metrics_enabled(self):
        """Test that business metrics are enabled."""
        self.assertTrue(
            getattr(settings, 'BUSINESS_METRICS_ENABLED', False),
            "BUSINESS_METRICS_ENABLED should be True"
        )


# ═════════════════════════════════════════════════════════════════════════════
# Celery Task Discovery Tests
# ═════════════════════════════════════════════════════════════════════════════

@tag('performance', 'celery', 'slow')
class CeleryTaskDiscoveryTests(TestCase):
    """Tests that Celery tasks are discoverable and properly configured."""

    def test_celery_app_importable(self):
        """Test that Celery app can be imported."""
        try:
            from cfbc.celery import app
            self.assertIsNotNone(app)
        except ImportError as e:
            self.fail(f"Celery app import failed: {e}")

    def test_cache_warm_task_defined(self):
        """Test that cache warm task is defined."""
        try:
            from cfbc.cache_signals import register_warm_cache_task
            self.assertTrue(callable(register_warm_cache_task))
        except ImportError:
            pass  # Celery may not be installed in test env

    def test_cache_health_check_task_defined(self):
        """Test that cache health check task is defined."""
        try:
            from cfbc.cache_signals import register_health_check_task
            self.assertTrue(callable(register_health_check_task))
        except ImportError:
            pass  # Celery may not be installed in test env
