"""
Cache invalidation signals and warm-up utilities for maintaining cache consistency.
Connect these signals in your app's apps.py or __init__.py.
Includes Celery task for scheduled cache warming.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)


@receiver(post_save)
@receiver(post_delete)
def invalidate_cache_on_model_change(sender, **kwargs):
    """
    Generic cache invalidation based on model changes.
    This is a fallback mechanism for models not specifically handled.
    """
    if kwargs.get('raw', False):
        return

    model_name = sender.__name__

    if model_name == 'Noticia':
        from blog.cached_views import invalidate_cache_on_noticia_save
        invalidate_cache_on_noticia_save(sender, **kwargs)
        logger.debug(f"Cache invalidated for Noticia change")

    elif model_name == 'Categoria':
        from blog.cached_views import invalidate_cache_on_categoria_save
        invalidate_cache_on_categoria_save(sender, **kwargs)
        logger.debug(f"Cache invalidated for Categoria change")

    elif model_name == 'Comentario':
        pass

    elif model_name == 'DocumentFolder':
        from course_documents.cached_views import invalidate_cache_on_document_folder_save
        invalidate_cache_on_document_folder_save(sender, **kwargs)
        logger.debug(f"Cache invalidated for DocumentFolder change")

    elif model_name == 'CourseDocument':
        from course_documents.cached_views import invalidate_cache_on_course_document_save
        invalidate_cache_on_course_document_save(sender, **kwargs)
        logger.debug(f"Cache invalidated for CourseDocument change")

    elif model_name == 'DocumentAccess':
        from course_documents.cached_views import invalidate_cache_on_document_access_save
        invalidate_cache_on_document_access_save(sender, **kwargs)
        logger.debug(f"Cache invalidated for DocumentAccess change")


def setup_cache_signals():
    """
    Setup all cache invalidation signals.
    Call this function in your app's ready() method.
    """
    from django.apps import apps

    try:
        from blog import models as blog_models
        from course_documents import models as course_documents_models

        logger.info("Cache signals setup complete")
        return True
    except ImportError as e:
        logger.error(f"Failed to setup cache signals: {e}")
        return False


# ========== Cache warming utilities ==========

def warm_cache():
    """
    Warm up the cache by pre-loading frequently accessed data.
    This should be called during deployment or after cache clearance.
    Can also be called from a Celery scheduled task.
    """
    from blog.cached_views import (
        get_cached_noticias_publicadas,
        get_cached_categorias,
        get_categorias_with_counts,
    )
    from course_documents.cached_views import (
        warm_course_documents_cache,
    )
    from cfbc.cache_utils import CacheMetrics, CacheVersion

    logger.info("Starting cache warm-up...")

    results = {
        "noticias": 0,
        "categorias": 0,
        "categorias_with_counts": 0,
        "course_documents": 0,
        "errors": [],
    }

    try:
        noticias = get_cached_noticias_publicadas()
        results["noticias"] = noticias.count()

        categorias = get_cached_categorias()
        results["categorias"] = categorias.count()

        categorias_with_counts = get_categorias_with_counts()
        if hasattr(categorias_with_counts, 'count'):
            results["categorias_with_counts"] = categorias_with_counts.count()
        else:
            results["categorias_with_counts"] = len(list(categorias_with_counts))

        logger.info(
            f"Warmed blog cache: {results['noticias']} news, "
            f"{results['categorias']} categories"
        )

    except Exception as e:
        logger.error(f"Blog cache warm-up failed: {e}")
        results["errors"].append(f"blog: {e}")

    try:
        warm_course_documents_cache()
        results["course_documents"] = 1
        logger.info("Warmed course documents cache")

    except Exception as e:
        logger.error(f"Course documents cache warm-up failed: {e}")
        results["errors"].append(f"course_documents: {e}")

    try:
        CacheMetrics.reset_metrics()
    except Exception as e:
        logger.warning(f"Failed to reset cache metrics: {e}")

    logger.info(
        f"Cache warm-up complete: "
        f"{results['noticias']} noticias, "
        f"{results['categorias']} categorias, "
        f"{results['course_documents']} curso docs warmed. "
        f"Errors: {len(results['errors'])}"
    )

    return results


# ========== Celery task for scheduled cache warming ==========

def register_warm_cache_task(app):
    """
    Register a periodic Celery task to warm the cache at regular intervals.
    Call this from the Celery app's on_after_finalize handler.

    Usage in cfbc/celery.py:
        from cfbc.cache_signals import register_warm_cache_task
        register_warm_cache_task(app)
    """
    from celery.schedules import crontab

    @app.task(
        name='cfbc.cache.warm_cache',
        bind=True,
        max_retries=3,
        default_retry_delay=120,
        soft_time_limit=300,
        time_limit=360,
        acks_late=True,
    )
    def warm_cache_task(self):
        logger.info("Celery warm_cache_task started")
        try:
            results = warm_cache()
            logger.info(f"Celery warm_cache_task completed: {results}")
            return results
        except Exception as exc:
            logger.error(f"Celery warm_cache_task failed: {exc}")
            raise self.retry(exc=exc)

    if not hasattr(app.conf, 'beat_schedule') or app.conf.beat_schedule is None:
        app.conf.beat_schedule = {}
    app.conf.beat_schedule.update({
        'warm-cache-every-30-minutes': {
            'task': 'cfbc.cache.warm_cache',
            'schedule': crontab(minute='*/30'),
            'options': {
                'queue': 'maintenance',
                'expires': 600,
            },
        },
    })

    logger.info("Registered warm_cache_task with Celery beat schedule (every 30 min)")
    return warm_cache_task


# ========== Periodic cache health check task ==========

def register_health_check_task(app):
    """Register a periodic Celery task to check cache health."""
    from celery.schedules import crontab

    @app.task(
        name='cfbc.cache.health_check',
        bind=True,
        max_retries=2,
        default_retry_delay=60,
        soft_time_limit=30,
        time_limit=60,
    )
    def cache_health_check_task(self):
        health = check_cache_health()
        logger.info(f"Cache health check: {health.get('status', 'unknown')}")
        if health.get('status') == 'unhealthy':
            logger.error(f"Cache is UNHEALTHY: {health}")
            raise self.retry(exc=Exception(f"Cache unhealthy: {health.get('error')}"))
        return health

    if not hasattr(app.conf, 'beat_schedule') or app.conf.beat_schedule is None:
        app.conf.beat_schedule = {}
    app.conf.beat_schedule.update({
        'cache-health-check-every-5-minutes': {
            'task': 'cfbc.cache.health_check',
            'schedule': crontab(minute='*/5'),
            'options': {
                'queue': 'maintenance',
                'expires': 120,
            },
        },
    })

    logger.info("Registered cache_health_check_task with Celery beat schedule (every 5 min)")
    return cache_health_check_task


# ========== Cache health check ==========

def check_cache_health():
    """
    Check cache health by testing basic operations.

    Returns:
        Dictionary with cache health status
    """
    from django.core.cache import cache
    import time

    test_key = 'cfbc:health_check'
    test_value = f'health_check_{int(time.time())}'

    try:
        cache.set(test_key, test_value, 10)
        retrieved = cache.get(test_key)
        cache.delete(test_key)

        health_status = {
            'status': 'healthy' if retrieved == test_value else 'degraded',
            'operation': 'set_get_delete',
            'retrieved_value': retrieved,
            'expected_value': test_value,
            'timestamp': time.time()
        }

        if retrieved != test_value:
            logger.warning(f"Cache health check failed: retrieved={retrieved}, expected={test_value}")

        return health_status

    except Exception as e:
        logger.error(f"Cache health check failed with error: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': time.time()
        }
