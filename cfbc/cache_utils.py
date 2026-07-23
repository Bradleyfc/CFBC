"""
Advanced cache utilities for the CFBC Django application.
Provides page-level caching, stampede protection, versioning,
fragment caching support, and granular TTL configuration.
"""

from django.core.cache import cache
from django.db.models import QuerySet
from functools import wraps
import hashlib
import time
import logging
from contextlib import contextmanager
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Cache key prefixes
# ─────────────────────────────────────────────────────────────────────────────

CACHE_KEY_PREFIX = "cfbc"
NOTICIAS_PUBLICADAS_KEY = f"{CACHE_KEY_PREFIX}:noticias_publicadas"
CATEGORIAS_ALL_KEY = f"{CACHE_KEY_PREFIX}:categorias_all"
DOCUMENT_FOLDERS_BY_CURSO_PREFIX = f"{CACHE_KEY_PREFIX}:folders_curso"
PAGE_CACHE_PREFIX = f"{CACHE_KEY_PREFIX}:page"
FRAGMENT_CACHE_PREFIX = f"{CACHE_KEY_PREFIX}:fragment"
STAMPEDE_LOCK_PREFIX = f"{CACHE_KEY_PREFIX}:lock"

# ─────────────────────────────────────────────────────────────────────────────
# Granular cache timeouts based on content volatility
# ─────────────────────────────────────────────────────────────────────────────

# Static / rarely-changing content
STATIC_PAGE_TIMEOUT = 3600 * 24  # 24 hours
CATEGORIAS_TIMEOUT = 3600  # 1 hour

# Moderately-changing content
NOTICIAS_TIMEOUT = 300  # 5 minutes
NOTICIA_DETAIL_TIMEOUT = 600  # 10 minutes

# User-specific / dynamic content
FOLDERS_TIMEOUT = 300  # 5 minutes
DASHBOARD_STATS_TIMEOUT = 300  # 5 minutes

# Fragment cache timeouts
HEADER_FRAGMENT_TIMEOUT = 3600  # 1 hour
FOOTER_FRAGMENT_TIMEOUT = 3600 * 24  # 24 hours
SIDEBAR_FRAGMENT_TIMEOUT = 600  # 10 minutes
NOTICIA_LIST_FRAGMENT_TIMEOUT = 300  # 5 minutes

# Aggressive caching for high-traffic content
HOME_PAGE_TIMEOUT = 600  # 10 minutes
CURSO_LIST_TIMEOUT = 600  # 10 minutes


# ─────────────────────────────────────────────────────────────────────────────
# Cache key generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate a unique cache key from prefix and arguments.
    Hashes long keys to stay within Redis limits.
    """
    key_parts = [prefix]
    for arg in args:
        key_parts.append(str(arg))
    for key in sorted(kwargs.keys()):
        key_parts.append(f"{key}:{kwargs[key]}")
    key_str = ":".join(key_parts)
    if len(key_str) > 200:
        key_str = f"{prefix}:{hashlib.md5(key_str.encode()).hexdigest()}"
    return key_str


# ─────────────────────────────────────────────────────────────────────────────
# Cache versioning for schema changes
# ─────────────────────────────────────────────────────────────────────────────

class CacheVersion:
    """
    Manages cache version keys.
    Increment a version group when schema changes to invalidate
    all cached data for that group without flushing Redis.
    
    Usage:
        CacheVersion.get('noticias')  # Returns current version
        CacheVersion.increment('noticias')  # Invalidates all noticia cache
    """

    _VERSION_GROUPS = {
        "noticias": "cfbc:version:noticias",
        "categorias": "cfbc:version:categorias",
        "comentarios": "cfbc:version:comentarios",
        "cursos": "cfbc:version:cursos",
        "documentos": "cfbc:version:documentos",
        "evaluaciones": "cfbc:version:evaluaciones",
        "usuarios": "cfbc:version:usuarios",
        "general": "cfbc:version:general",
    }

    @classmethod
    def get(cls, group: str = "general") -> int:
        """Get the current version number for a group."""
        key = cls._VERSION_GROUPS.get(group, cls._VERSION_GROUPS["general"])
        return cache.get(key, 1)

    @classmethod
    def increment(cls, group: str = "general") -> int:
        """Increment version for a group, invalidating cached data."""
        key = cls._VERSION_GROUPS.get(group, cls._VERSION_GROUPS["general"])
        try:
            new_version = cache.incr(key)
            logger.info(f"Cache version incremented for group '{group}': now v{new_version}")
            return new_version
        except ValueError:
            # Key doesn't exist yet
            cache.set(key, 2, timeout=None)  # Start at 2 (1 is default)
            logger.info(f"Cache version initialized for group '{group}': v2")
            return 2

    @classmethod
    def make_key(cls, base_key: str, group: str = "general") -> str:
        """Append version to a cache key."""
        version = cls.get(group)
        return f"{base_key}:v{version}"

    @classmethod
    def all_groups(cls) -> dict:
        """Get all version groups and their current values."""
        result = {}
        for group, key in cls._VERSION_GROUPS.items():
            result[group] = cache.get(key, 1)
        return result


# ─────────────────────────────────────────────────────────────────────────────
# Cache stampede protection
# ─────────────────────────────────────────────────────────────────────────────

def stampede_protect(lock_timeout: int = 5, cache_timeout: Optional[int] = None):
    """
    Decorator that prevents cache stampede by using a distributed lock.
    Only one process regenerates the cached value; others wait or
    get a slightly stale value.
    
    Args:
        lock_timeout: Seconds before the lock auto-releases
        cache_timeout: Override the inner cached decorator timeout
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate a unique cache key for this function call
            prefix = f"{func.__module__}:{func.__name__}"
            cache_key = generate_cache_key(prefix, *args, **kwargs)
            lock_key = f"{STAMPEDE_LOCK_PREFIX}:{cache_key}"

            # Try to get from cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Try to acquire the regeneration lock
            lock_acquired = cache.add(lock_key, "locked", lock_timeout)

            if lock_acquired:
                # We are the regenerator
                try:
                    result = func(*args, **kwargs)
                    timeout = cache_timeout if cache_timeout is not None else 300
                    cache.set(cache_key, result, timeout)
                    return result
                finally:
                    cache.delete(lock_key)
            else:
                # Another process is regenerating - wait and retry
                max_wait = lock_timeout
                waited = 0
                while waited < max_wait:
                    time.sleep(0.1)
                    cached_result = cache.get(cache_key)
                    if cached_result is not None:
                        return cached_result
                    waited += 0.1
                # Fall back to executing the function
                logger.warning(f"Stampede protection timeout for key: {cache_key}")
                return func(*args, **kwargs)

        return wrapper
    return decorator


@contextmanager
def stampede_lock(cache_key: str, lock_timeout: int = 5):
    """
    Context manager for stampede protection.
    Use inside a function that regenerates cached data.
    """
    lock_key = f"{STAMPEDE_LOCK_PREFIX}:{cache_key}"
    lock_acquired = cache.add(lock_key, "locked", lock_timeout)
    try:
        yield lock_acquired
    finally:
        if lock_acquired:
            cache.delete(lock_key)


# ─────────────────────────────────────────────────────────────────────────────
# Basic query caching decorator
# ─────────────────────────────────────────────────────────────────────────────

def cached_query(timeout: int = 300, key_prefix: Optional[str] = None):
    """
    Decorator for caching database query results.
    Includes automatic version prefixing for invalidation.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            prefix = key_prefix or f"{func.__module__}:{func.__name__}"
            base_key = generate_cache_key(prefix, *args, **kwargs)
            # Add versioning for schema-change invalidation
            cache_key = CacheVersion.make_key(base_key, _detect_group(func.__name__))

            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result

            logger.debug(f"Cache miss for key: {cache_key}")
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator


def _detect_group(func_name: str) -> str:
    """Heuristic to detect which version group a function belongs to."""
    func_lower = func_name.lower()
    if "noticia" in func_lower or "news" in func_lower or "blog" in func_lower:
        return "noticias"
    if "categoria" in func_lower:
        return "categorias"
    if "comentario" in func_lower or "comment" in func_lower:
        return "comentarios"
    if "curso" in func_lower or "course" in func_lower:
        return "cursos"
    if "document" in func_lower or "folder" in func_lower:
        return "documentos"
    if "evaluacion" in func_lower or "evaluation" in func_lower:
        return "evaluaciones"
    if "user" in func_lower or "profile" in func_lower or "registro" in func_lower:
        return "usuarios"
    return "general"


# ─────────────────────────────────────────────────────────────────────────────
# Page-level caching decorator
# ─────────────────────────────────────────────────────────────────────────────

def cached_page(timeout: int = 300, key_prefix: Optional[str] = None,
                vary_on_user: bool = False, vary_on_auth: bool = False):
    """
    Decorator for full-page caching of Django views.
    
    Args:
        timeout: Cache duration in seconds
        key_prefix: Optional key prefix
        vary_on_user: If True, cache varies per user (e.g., dashboard)
        vary_on_auth: If True, cache differs for authenticated vs anonymous
    
    Usage:
        @cached_page(timeout=600)
        def my_view(request):
            ...
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Build cache key from path + query params
            path = request.get_full_path()
            prefix = key_prefix or f"{PAGE_CACHE_PREFIX}:{view_func.__name__}"

            key_parts = [prefix, path]

            if vary_on_user and request.user.is_authenticated:
                key_parts.append(f"user:{request.user.id}")
            elif vary_on_auth:
                key_parts.append(f"auth:{request.user.is_authenticated}")

            base_key = ":".join(key_parts)
            if len(base_key) > 200:
                base_key = f"{prefix}:{hashlib.md5(base_key.encode()).hexdigest()}"

            # Apply versioning and stampede protection
            cache_key = CacheVersion.make_key(base_key, "general")

            cached_response = cache.get(cache_key)
            if cached_response is not None:
                logger.debug(f"Page cache HIT: {path}")
                return cached_response

            logger.debug(f"Page cache MISS: {path}")
            response = view_func(request, *args, **kwargs)

            # Only cache successful responses
            if response.status_code == 200:
                cache.set(cache_key, response, timeout)

            return response
        return wrapper
    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# Fragment cache utilities
# ─────────────────────────────────────────────────────────────────────────────

def cache_fragment(key: str, timeout: int = 300, group: str = "general"):
    """
    Cache a rendered template fragment.
    Returns a decorator for template tag functions.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            base_key = f"{FRAGMENT_CACHE_PREFIX}:{key}:{generate_cache_key('frag', *args, **kwargs)}"
            cache_key = CacheVersion.make_key(base_key, group)

            cached = cache.get(cache_key)
            if cached is not None:
                return cached

            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator


def invalidate_fragment(pattern: str) -> int:
    """Invalidate fragment caches matching a key pattern."""
    full_pattern = f"{FRAGMENT_CACHE_PREFIX}:{pattern}"
    return invalidate_cache_pattern(full_pattern)


# ─────────────────────────────────────────────────────────────────────────────
# Cache invalidation utilities
# ─────────────────────────────────────────────────────────────────────────────

def invalidate_cache_pattern(pattern: str) -> int:
    """Invalidate all cache keys matching a pattern."""
    try:
        keys = cache.keys(pattern)
        if keys:
            deleted = cache.delete_many(keys)
            logger.debug(f"Invalidated {deleted} keys matching: {pattern}")
            return deleted
        return 0
    except Exception as e:
        logger.error(f"Error invalidating cache pattern {pattern}: {e}")
        return 0


# ─────────────────────────────────────────────────────────────────────────────
# Blog-specific cached queries
# ─────────────────────────────────────────────────────────────────────────────

@cached_query(timeout=NOTICIAS_TIMEOUT, key_prefix=NOTICIAS_PUBLICADAS_KEY)
def get_cached_noticias_publicadas() -> QuerySet:
    """Get published news with caching."""
    from blog.models import Noticia
    return Noticia.objects.filter(estado="publicado").select_related("categoria", "autor")


@cached_query(timeout=CATEGORIAS_TIMEOUT, key_prefix=CATEGORIAS_ALL_KEY)
def get_cached_categorias() -> QuerySet:
    """Get all categories with caching."""
    from blog.models import Categoria
    return Categoria.objects.all()


def invalidate_noticias_cache() -> int:
    """Invalidate all news-related cache."""
    return CacheVersion.increment("noticias")


def invalidate_categorias_cache() -> int:
    """Invalidate all category-related cache."""
    return CacheVersion.increment("categorias")


# ─────────────────────────────────────────────────────────────────────────────
# Course documents cached queries
# ─────────────────────────────────────────────────────────────────────────────

def get_cached_folders_for_curso(curso_id: int) -> QuerySet:
    """Get document folders for a course with caching."""
    from course_documents.models import DocumentFolder
    base_key = generate_cache_key(DOCUMENT_FOLDERS_BY_CURSO_PREFIX, curso_id)
    cache_key = CacheVersion.make_key(base_key, "documentos")

    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    folders = DocumentFolder.objects.filter(curso_id=curso_id).order_by("name")
    cache.set(cache_key, folders, FOLDERS_TIMEOUT)
    return folders


def invalidate_folders_cache_for_curso(curso_id: int) -> bool:
    """Invalidate folder cache for a specific course."""
    base_key = generate_cache_key(DOCUMENT_FOLDERS_BY_CURSO_PREFIX, curso_id)
    cache_key = CacheVersion.make_key(base_key, "documentos")
    cache.delete(cache_key)
    # Also increment documentos version to invalidate all document caches
    CacheVersion.increment("documentos")
    return True


def invalidate_all_folders_cache() -> int:
    """Invalidate all document folders cache."""
    return invalidate_cache_pattern(f"{DOCUMENT_FOLDERS_BY_CURSO_PREFIX}:*")


# ─────────────────────────────────────────────────────────────────────────────
# Integrated decorator: cached_query + stampede_protect + metrics
# ─────────────────────────────────────────────────────────────────────────────

def cached_with_metrics(timeout: int = 300, key_prefix: Optional[str] = None,
                        stampede: bool = False):
    """
    Combined decorator: caching + metrics + optional stampede protection.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            prefix = key_prefix or f"{func.__module__}:{func.__name__}"
            base_key = generate_cache_key(prefix, *args, **kwargs)
            cache_key = CacheVersion.make_key(base_key, _detect_group(func.__name__))

            cached_result = cache.get(cache_key)
            if cached_result is not None:
                CacheMetrics.record_hit(cache_key)
                logger.debug(f"Cache hit with metrics for key: {cache_key}")
                return cached_result

            CacheMetrics.record_miss(cache_key)
            logger.debug(f"Cache miss with metrics for key: {cache_key}")

            if stampede:
                # Apply stampede protection
                lock_key = f"{STAMPEDE_LOCK_PREFIX}:{cache_key}"
                lock_acquired = cache.add(lock_key, "locked", 5)
                if not lock_acquired:
                    # Another process is regenerating
                    
                    for _ in range(50):  # Wait up to 5s
                        time.sleep(0.1)
                        cached_result = cache.get(cache_key)
                        if cached_result is not None:
                            CacheMetrics.record_hit(cache_key)
                            return cached_result
                    # Timeout - regenerate anyway
                try:
                    result = func(*args, **kwargs)
                    cache.set(cache_key, result, timeout)
                    return result
                finally:
                    if lock_acquired:
                        cache.delete(lock_key)
            else:
                result = func(*args, **kwargs)
                cache.set(cache_key, result, timeout)
                return result
        return wrapper
    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# Cache metrics
# ─────────────────────────────────────────────────────────────────────────────

class CacheMetrics:
    """Tracks cache performance metrics."""

    HITS_KEY = f"{CACHE_KEY_PREFIX}:metrics:hits"
    MISSES_KEY = f"{CACHE_KEY_PREFIX}:metrics:misses"

    @staticmethod
    def record_hit(cache_key: str):
        try:
            cache.incr(CacheMetrics.HITS_KEY, 1)
        except ValueError:
            cache.set(CacheMetrics.HITS_KEY, 1, timeout=None)

    @staticmethod
    def record_miss(cache_key: str):
        try:
            cache.incr(CacheMetrics.MISSES_KEY, 1)
        except ValueError:
            cache.set(CacheMetrics.MISSES_KEY, 1, timeout=None)

    @staticmethod
    def get_hit_ratio() -> float:
        hits = cache.get(CacheMetrics.HITS_KEY, 0)
        misses = cache.get(CacheMetrics.MISSES_KEY, 0)
        total = hits + misses
        return hits / total if total > 0 else 0.0

    @staticmethod
    def reset_metrics():
        cache.delete(CacheMetrics.HITS_KEY)
        cache.delete(CacheMetrics.MISSES_KEY)

    @staticmethod
    def get_stats() -> dict:
        hits = cache.get(CacheMetrics.HITS_KEY, 0)
        misses = cache.get(CacheMetrics.MISSES_KEY, 0)
        return {
            "hits": hits,
            "misses": misses,
            "hit_ratio": CacheMetrics.get_hit_ratio(),
            "versions": CacheVersion.all_groups(),
        }
