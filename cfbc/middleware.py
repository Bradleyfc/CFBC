"""
APM, structured logging, and request monitoring middleware for CFBC.

Provides:
- CorrelationIdMiddleware: Adds unique request IDs for distributed tracing
- RequestTimingMiddleware: Tracks request duration, DB queries, cache metrics
- Structured logging with JSON format

Requirements:
    pip install structlog django-structlog
"""

import os
import time
import uuid
import logging
import json
from datetime import datetime

from django.conf import settings
from django.db import connection
from django.core.cache import cache

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Correlation ID Middleware
# ─────────────────────────────────────────────────────────────────────────────

class CorrelationIdMiddleware:
    """
    Adds a unique correlation/request ID to every request for distributed tracing.

    - Reads existing X-Request-ID from the incoming request (if behind a proxy)
    - Generates a new UUID if none exists
    - Adds X-Request-ID to the response
    - Makes the ID available on request.correlation_id
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get or generate correlation ID
        correlation_id = request.META.get('HTTP_X_REQUEST_ID')
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Store on request for use throughout the app
        request.correlation_id = correlation_id
        request._request_start_time = time.time()

        # Process the request
        response = self.get_response(request)

        # Add correlation ID to response headers
        response['X-Request-ID'] = correlation_id
        response['X-Response-Time'] = f"{(time.time() - request._request_start_time) * 1000:.0f}ms"

        return response


# ─────────────────────────────────────────────────────────────────────────────
# Request Timing / APM Middleware
# ─────────────────────────────────────────────────────────────────────────────

class RequestTimingMiddleware:
    """
    Application Performance Monitoring (APM) middleware.

    Tracks per-request:
    - Total request duration
    - Database query count and total time
    - Cache operations (if any)
    - Response status code

    Stores metrics in Redis for aggregation and alerting.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store timing data on request for use by views
        request._db_queries_before = len(connection.queries)
        request._cache_operations = 0

        # Process the request
        response = self.get_response(request)

        # Calculate metrics
        db_queries = len(connection.queries) - request._db_queries_before
        db_time = sum(
            float(q['time']) for q in connection.queries[request._db_queries_before:]
        ) if db_queries > 0 else 0.0

        total_time = time.time() - getattr(request, '_request_start_time', time.time())

        # Store metrics for the metrics endpoint
        self._record_metrics(
            path=request.path,
            method=request.method,
            status_code=response.status_code,
            duration=total_time,
            db_queries=db_queries,
            db_time=db_time,
            correlation_id=getattr(request, 'correlation_id', ''),
        )

        # Add debug headers (if DEBUG mode)
        if settings.DEBUG:
            response['X-DB-Queries'] = str(db_queries)
            response['X-DB-Time'] = f"{db_time:.3f}s"

        return response

    def _record_metrics(self, path, method, status_code, duration,
                        db_queries, db_time, correlation_id=''):
        """Record metrics to Redis for aggregation and monitoring dashboards."""
        try:
            # Normalize path for aggregation (replace IDs with {id})
            normalized_path = self._normalize_path(path)

            # Get start of current minute for time-series
            now = datetime.now()
            minute_key = now.strftime('%Y-%m-%dT%H:%M')

            # Store in Redis using pipeline for atomicity
            pipe = cache.client.get_client().pipeline() if hasattr(cache, 'client') else None
            if pipe:
                # Request count per path
                pipe.hincrby(f'cfbc:metrics:requests:{minute_key}', normalized_path, 1)
                # Duration tracking (sum and count for avg)
                pipe.hincrbyfloat(f'cfbc:metrics:duration:{minute_key}',
                                  f'{normalized_path}:sum', duration)
                pipe.hincrby(f'cfbc:metrics:duration:{minute_key}',
                             f'{normalized_path}:count', 1)
                # Status code tracking
                status_group = f"{status_code // 100}xx"
                pipe.hincrby(f'cfbc:metrics:status:{minute_key}', status_group, 1)
                # DB query tracking
                pipe.hincrby(f'cfbc:metrics:db:{minute_key}',
                             f'{normalized_path}:count', db_queries)
                pipe.hincrbyfloat(f'cfbc:metrics:db:{minute_key}',
                                  f'{normalized_path}:time', db_time)
                # Expire after 1 hour
                for key in [f'cfbc:metrics:requests:{minute_key}',
                           f'cfbc:metrics:duration:{minute_key}',
                           f'cfbc:metrics:status:{minute_key}',
                           f'cfbc:metrics:db:{minute_key}']:
                    pipe.expire(key, 3600)
                pipe.execute()

            # Log slow requests (> 2 seconds)
            if duration > 2.0:
                logger.warning(
                    f"SLOW REQUEST ({duration:.2f}s) {method} {normalized_path} "
                    f"→ {status_code} | {db_queries} queries ({db_time:.3f}s) | "
                    f"correlation_id={correlation_id}"
                )

            # Log high DB query count (> 30 queries)
            if db_queries > 30:
                logger.warning(
                    f"HIGH DB QUERIES ({db_queries}) {method} {normalized_path} "
                    f"→ {status_code} | duration={duration:.2f}s | "
                    f"correlation_id={correlation_id}"
                )

        except Exception as e:
            logger.debug(f"Failed to record metrics: {e}")

    @staticmethod
    def _normalize_path(path):
        """Normalize URL path for aggregation by replacing IDs with {id}."""
        import re
        # Replace UUIDs
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
                      '/{uuid}', path)
        # Replace numeric IDs
        path = re.sub(r'/\d+', '/{id}', path)
        return path


# ─────────────────────────────────────────────────────────────────────────────
# Structured Logging Middleware
# ─────────────────────────────────────────────────────────────────────────────

class StructuredLoggingMiddleware:
    """
    Middleware that adds structured context to log records.

    Adds the following to each log record within a request:
    - correlation_id
    - user_id (if authenticated)
    - request_path
    - request_method
    - client_ip

    Usage: This middleware sets up context for structlog or JSON logging.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store structured context on request
        request.structured_log = {
            'correlation_id': getattr(request, 'correlation_id', ''),
            'user_id': request.user.id if request.user.is_authenticated else None,
            'username': request.user.username if request.user.is_authenticated else 'anonymous',
            'path': request.path,
            'method': request.method,
            'client_ip': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
            'referer': request.META.get('HTTP_REFERER', ''),
        }

        response = self.get_response(request)

        # Log request summary with structured context
        duration = time.time() - getattr(request, '_request_start_time', time.time())
        log_data = {
            **request.structured_log,
            'status_code': response.status_code,
            'duration_ms': round(duration * 1000, 1),
            'content_length': len(response.content) if hasattr(response, 'content') and response.content else 0,
        }

        # Log at appropriate level based on status code
        if response.status_code >= 500:
            logger.error(f"Request completed with error", extra={'structured_log': log_data})
        elif response.status_code >= 400:
            logger.warning(f"Request completed with client error", extra={'structured_log': log_data})
        else:
            logger.info(f"Request completed", extra={'structured_log': log_data})

        return response

    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request headers."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')


# ─────────────────────────────────────────────────────────────────────────────
# Configure structured logging
# ─────────────────────────────────────────────────────────────────────────────

def configure_structured_logging():
    """
    Configure Django logging to output structured JSON logs.

    Call this in settings.py to enable JSON-formatted logging
    for production environments. In development, use the console
    formatter for readability.

    Usage in settings.py:
        from cfbc.middleware import configure_structured_logging
        configure_structured_logging()

    Or set LOGGING directly in settings.py (recommended):
        See docs/monitoring_stack.md for the LOGGING config.
    """
    import logging.config

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                '()': 'cfbc.middleware.JsonFormatter',
            },
            'verbose': {
                'format': '{levelname} {asctime} {module} {message}',
                'style': '{',
            },
            'simple': {
                'format': '{levelname} {message}',
                'style': '{',
            },
        },
        'filters': {
            'correlation_id': {
                '()': 'cfbc.middleware.CorrelationIdFilter',
            },
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
            },
            'console_json': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'json',
            },
            'performance_file': {
                'level': 'WARNING',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/performance.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'formatter': 'json',
            },
            'monitoring_file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/monitoring.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'formatter': 'json',
            },
            'errors_file': {
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/errors.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 10,
                'formatter': 'json',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console', 'errors_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'django.request': {
                'handlers': ['console_json', 'errors_file'],
                'level': 'WARNING',
                'propagate': False,
            },
            'django.db.backends': {
                'handlers': ['performance_file'],
                'level': 'WARNING',
                'propagate': False,
            },
            'django.db.performance': {
                'handlers': ['performance_file', 'console_json'],
                'level': 'WARNING',
                'propagate': False,
            },
            'cfbc': {
                'handlers': ['console_json', 'monitoring_file', 'errors_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'cfbc.autoscaler': {
                'handlers': ['monitoring_file'],
                'level': 'INFO',
                'propagate': False,
            },
        },
    }

    logging.config.dictConfig(LOGGING)


class JsonFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as JSON objects.

    Makes log aggregation (ELK, Splunk, etc.) easier by producing
    structured log output that can be parsed programmatically.
    """

    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info and record.exc_info[0]:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
            }

        # Add structured log data if present
        if hasattr(record, 'structured_log'):
            log_data.update(record.structured_log)

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in ('args', 'asctime', 'created', 'exc_info', 'exc_text',
                          'filename', 'funcName', 'levelname', 'levelno',
                          'lineno', 'module', 'msecs', 'message', 'msg',
                          'name', 'pathname', 'process', 'processName',
                          'relativeCreated', 'stack_info', 'thread', 'threadName',
                          'structured_log'):
                log_data[key] = value

        return json.dumps(log_data, default=str)


class CorrelationIdFilter(logging.Filter):
    """
    Logging filter that adds correlation_id to log records.
    Usage: Add this filter to handlers to include correlation IDs in all logs.
    """

    def filter(self, record):
        # correlation_id is added via structured_log by the middleware
        return True


# ─────────────────────────────────────────────────────────────────────────────
# Cache-Control Headers Middleware
# ─────────────────────────────────────────────────────────────────────────────

class CacheControlMiddleware:
    """
    Middleware that adds Cache-Control headers to responses for:
    - Static assets: long-lived cache (30 days)
    - API responses: no-cache for dynamic data
    - HTML pages: short-lived cache (5-10 minutes) for public content
    - User-specific pages: private, no-cache

    This optimizes content delivery by:
    - Reducing redundant requests to the server
    - Improving page load times for repeat visitors
    - Leveraging browser caching for static files
    - Ensuring fresh data for authenticated/dynamic content
    """

    # File extensions that can be safely cached for a long time
    STATIC_EXTENSIONS = {
        '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
        '.woff', '.woff2', '.ttf', '.eot', '.webp', '.mp4', '.webm',
    }

    # Paths that should never be cached (user-specific)
    PRIVATE_PATHS = {
        '/perfil/', '/admin/', '/accounts/', '/calificaciones/', '/asistencias/',
        '/matriculas/', '/evaluaciones/', '/mensajes/', '/notificaciones/',
    }

    # Paths with dynamic content that should be checked for freshness
    DYNAMIC_PATHS = {
        '/noticias/', '/cursos/', '/course-documents/',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Skip if Cache-Control already set by view
        if response.has_header('Cache-Control'):
            return response

        path = request.path.lower()

        # Static files: cache for 30 days
        if self._is_static_file(path):
            response['Cache-Control'] = 'public, max-age=2592000, immutable'
            return response

        # Private/user-specific pages: no caching
        if self._is_private_path(path) or request.user.is_authenticated:
            response['Cache-Control'] = 'private, no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response

        # API endpoints: no caching
        if path.startswith('/api/') or path.startswith('/health/') or path.startswith('/metrics/'):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            return response

        # Dynamic but public content: short-lived cache (5 min)
        if self._is_dynamic_path(path):
            response['Cache-Control'] = 'public, max-age=300'
            return response

        # Public HTML pages: moderate cache (10 min)
        if not self._is_private_path(path) and not request.user.is_authenticated:
            response['Cache-Control'] = 'public, max-age=600'
            return response

        # Default: no caching for safety
        response['Cache-Control'] = 'no-cache, private'

        return response

    def _is_static_file(self, path):
        """Check if the request is for a static file."""
        _, ext = os.path.splitext(path) if isinstance(path, str) else ('', '')
        return ext.lower() in self.STATIC_EXTENSIONS

    def _is_private_path(self, path):
        """Check if the path contains user-specific content."""
        for private_path in self.PRIVATE_PATHS:
            if path.startswith(private_path):
                return True
        return False

    def _is_dynamic_path(self, path):
        """Check if the path is dynamic but public content."""
        for dynamic_path in self.DYNAMIC_PATHS:
            if path.startswith(dynamic_path):
                return True
        return False


# ═════════════════════════════════════════════════════════════════════════════
# Security Headers Middleware (CSP, HSTS, X-Frame-Options, etc.)
# ═════════════════════════════════════════════════════════════════════════════

class SecurityHeadersMiddleware:
    """
    Middleware that adds security headers to all HTTP responses.

    Headers added:
    - Content-Security-Policy (CSP): Restricts content sources
    - Strict-Transport-Security (HSTS): Forces HTTPS
    - X-Content-Type-Options: Prevents MIME sniffing
    - X-Frame-Options: Prevents clickjacking
    - Referrer-Policy: Controls referrer information
    - Permissions-Policy: Restricts browser features
    - X-XSS-Protection: Enables XSS filter in older browsers

    These headers work in conjunction with Nginx-level headers configured
    in deploy/nginx/nginx.conf. Django-level headers ensure security
    even when not behind Nginx (e.g., development or direct access).

    In DEBUG=True mode, CSP is relaxed to allow local development.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # === Content-Security-Policy ===
        # Strict CSP in production, relaxed for development
        if settings.DEBUG:
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'"
            )
        else:
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )  # Note: 'unsafe-eval' excluded in production intentionally

        # Only add if not already set by the view or Nginx
        if not response.has_header('Content-Security-Policy'):
            # Use configurable CSP from settings if available
            custom_csp = getattr(settings, 'CONTENT_SECURITY_POLICY', None)
            response['Content-Security-Policy'] = custom_csp or csp

        # === Strict-Transport-Security (HSTS) ===
        # Only add for HTTPS responses (not in development)
        if not response.has_header('Strict-Transport-Security'):
            if request.is_secure() or not settings.DEBUG:
                hsts_max_age = getattr(settings, 'HSTS_MAX_AGE', 31536000)
                hsts_include_subdomains = getattr(settings, 'HSTS_INCLUDE_SUBDOMAINS', True)
                hsts_preload = getattr(settings, 'HSTS_PRELOAD', False)

                hsts_value = f"max-age={hsts_max_age}"
                if hsts_include_subdomains:
                    hsts_value += "; includeSubDomains"
                if hsts_preload:
                    hsts_value += "; preload"

                response['Strict-Transport-Security'] = hsts_value

        # === X-Content-Type-Options ===
        if not response.has_header('X-Content-Type-Options'):
            response['X-Content-Type-Options'] = 'nosniff'

        # === X-Frame-Options ===
        if not response.has_header('X-Frame-Options'):
            x_frame_value = getattr(settings, 'X_FRAME_OPTIONS', 'DENY')
            response['X-Frame-Options'] = x_frame_value

        # === Referrer-Policy ===
        if not response.has_header('Referrer-Policy'):
            referrer_policy = getattr(settings, 'REFERRER_POLICY',
                                      'strict-origin-when-cross-origin')
            response['Referrer-Policy'] = referrer_policy

        # === Permissions-Policy ===
        if not response.has_header('Permissions-Policy'):
            permissions_policy = getattr(settings, 'PERMISSIONS_POLICY',
                'camera=(), microphone=(), geolocation=(), '
                'payment=(), usb=(), display-capture=()'
            )
            response['Permissions-Policy'] = permissions_policy

        # === X-XSS-Protection (for older browsers) ===
        if not response.has_header('X-XSS-Protection'):
            response['X-XSS-Protection'] = '1; mode=block'

        return response


# ═════════════════════════════════════════════════════════════════════════════
# Rate Limiting Middleware (Django-level)
# ═════════════════════════════════════════════════════════════════════════════

class RateLimitMiddleware:
    """
    Middleware for IP-based rate limiting at the Django level.

    Provides rate limiting for:
    - Login attempts: 5 requests per minute per IP
    - API endpoints: 30 requests per minute per IP
    - File uploads: 10 requests per minute per IP
    - General: 200 requests per minute per IP

    Uses Django's cache (Redis) for tracking request counts, which
    means rate limits are shared across all application instances.

    This complements Nginx-level rate limiting by providing:
    - Application-aware rate limits (e.g., login failures vs attempts)
    - User-specific rate limits (beyond just IP-based)
    - Rate limit headers in responses for client awareness

    Rate limiting can be disabled in development via the
    DISABLE_RATE_LIMITING setting.
    """

    # Rate limit configurations: (requests, window_seconds, block_seconds)
    RATE_LIMITS = {
        'login': {'requests': 5, 'window': 60, 'block': 300},       # 5/min, block 5min
        'api': {'requests': 30, 'window': 60, 'block': 120},        # 30/min, block 2min
        'upload': {'requests': 10, 'window': 60, 'block': 300},     # 10/min, block 5min
        'general': {'requests': 200, 'window': 60, 'block': 60},    # 200/min, block 1min
    }

    # Paths that match each rate limit category
    PATH_MAP = {
        'login': ['/accounts/login/', '/admin/login/'],
        'api': ['/api/'],
        'upload': ['/course-documents/upload/', '/course-documents/create/'],
    }

    # Headers to add to rate-limited responses
    RATE_LIMIT_HEADERS = {
        'X-RateLimit-Limit': 'requests_per_minute',
        'X-RateLimit-Remaining': 'remaining_requests',
        'X-RateLimit-Reset': 'reset_time',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip rate limiting if disabled
        if getattr(settings, 'DISABLE_RATE_LIMITING', settings.DEBUG):
            return self.get_response(request)

        # Determine rate limit category for this request
        category = self._get_category(request)
        if not category:
            return self.get_response(request)

        # Get client identifier (IP for anonymous, user_id for authenticated)
        client_id = self._get_client_id(request)
        if not client_id:
            return self.get_response(request)

        # Check rate limit
        limit_config = self.RATE_LIMITS[category]
        is_allowed, remaining, reset_time = self._check_rate_limit(
            category, client_id, limit_config
        )

        if not is_allowed:
            return self._rate_limit_response(
                request, category, limit_config, reset_time
            )

        # Process the request
        response = self.get_response(request)

        # Add rate limit headers
        response['X-RateLimit-Limit'] = str(limit_config['requests'])
        response['X-RateLimit-Remaining'] = str(remaining)
        response['X-RateLimit-Reset'] = str(reset_time)

        return response

    def _get_category(self, request):
        """Determine the rate limit category for a request."""
        path = request.path.lower()

        # Check specific path mappings first
        for category, paths in self.PATH_MAP.items():
            for check_path in paths:
                if path.startswith(check_path):
                    return category

        # API endpoints
        if path.startswith('/api/'):
            return 'api'

        # POST to login endpoints
        if request.method == 'POST' and ('login' in path or 'auth' in path):
            return 'login'

        # File uploads
        if request.method == 'POST' and request.FILES:
            return 'upload'

        # Default: no rate limiting for general GET requests
        # (Nginx handles general rate limiting at 100r/s)
        return None

    def _get_client_id(self, request):
        """Get a unique identifier for the client."""
        if request.user.is_authenticated:
            return f"user:{request.user.id}"

        # Use IP address for anonymous users
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')

        return f"ip:{ip}"

    def _check_rate_limit(self, category, client_id, config):
        """
        Check if the request is within rate limits.

        Returns:
            Tuple of (is_allowed, remaining_requests, reset_timestamp)
        """
        from django.core.cache import cache

        window = config['window']
        max_requests = config['requests']

        # Cache key for this rate limit counter
        cache_key = f"cfbc:ratelimit:{category}:{client_id}"

        # Get current count and expiry
        data = cache.get(cache_key)
        now = int(time.time())

        if data is None:
            # First request in this window
            remaining = max_requests - 1
            cache.set(cache_key, {
                'count': 1,
                'window_start': now,
                'blocked_until': 0,
            }, window)
            return True, remaining, now + window

        # Check if blocked
        if data.get('blocked_until', 0) > now:
            return False, 0, data['blocked_until']

        # Check if window has expired
        window_start = data.get('window_start', 0)
        if now - window_start > window:
            # New window
            data = {'count': 1, 'window_start': now, 'blocked_until': 0}
            cache.set(cache_key, data, window)
            return True, max_requests - 1, now + window

        # Increment count
        data['count'] += 1

        if data['count'] > max_requests:
            # Rate limit exceeded - block the client
            block_seconds = config['block']
            data['blocked_until'] = now + block_seconds
            cache.set(cache_key, data, block_seconds)

            logger.warning(
                f"Rate limit exceeded: category={category}, "
                f"client={client_id}, count={data['count']}"
            )
            return False, 0, now + block_seconds

        remaining = max_requests - data['count']
        cache.set(cache_key, data, window)

        return True, remaining, window_start + window

    def _rate_limit_response(self, request, category, config, reset_time):
        """Generate a 429 Too Many Requests response."""
        from django.http import JsonResponse, HttpResponse

        wait_seconds = max(0, reset_time - int(time.time()))

        # Accept header-based response format
        accept = request.META.get('HTTP_ACCEPT', '')
        if 'application/json' in accept or request.path.startswith('/api/'):
            response = JsonResponse(
                {
                    'error': 'Too Many Requests',
                    'message': f"Rate limit exceeded. Try again in {wait_seconds} seconds.",
                    'retry_after': wait_seconds,
                    'category': category,
                },
                status=429,
            )
        else:
            response = HttpResponse(
                f"<h1>429 Too Many Requests</h1>"
                f"<p>Rate limit exceeded for {category}. "
                f"Please wait {wait_seconds} seconds before trying again.</p>",
                status=429,
                content_type='text/html',
            )

        response['Retry-After'] = str(wait_seconds)
        response['X-RateLimit-Limit'] = str(config['requests'])
        response['X-RateLimit-Reset'] = str(reset_time)

        return response


# ═════════════════════════════════════════════════════════════════════════════
# Security Audit Middleware
# ═════════════════════════════════════════════════════════════════════════════

class SecurityAuditMiddleware:
    """
    Middleware for security-focused logging and audit trail.

    Logs security-relevant events:
    - Failed login attempts (with IP and username)
    - Successful logins (with IP)
    - Unauthorized access attempts (403 responses)
    - Suspicious request patterns
    - File uploads and downloads
    - Admin panel access

    Sensitive data is automatically sanitized from logs.
    """

    # Sensitive parameters to redact from logs
    SENSITIVE_PARAMS = {'password', 'password1', 'password2', 'token',
                        'csrfmiddlewaretoken', 'secret', 'api_key', 'auth',
                        'sessionid', 'access_token', 'refresh_token'}

    # Paths that trigger audit logging
    AUDIT_PATHS = {
        'login': ['/accounts/login/', '/admin/login/'],
        'admin': ['/admin/'],
        'upload': ['/course-documents/'],
        'settings': ['/accounts/password/', '/accounts/profile/'],
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request
        response = self.get_response(request)

        # Audit based on response status and path
        self._audit_request(request, response)

        return response

    def _audit_request(self, request, response):
        """Audit a request based on its characteristics."""
        status = response.status_code
        path = request.path.lower()
        method = request.method

        # Skip non-auditable requests
        if path.startswith('/static/') or path.startswith('/health/'):
            return

        # Determine audit event type
        event_type = self._get_event_type(path, status, method)
        if not event_type:
            return

        # Build audit log entry with sanitized data
        audit_entry = self._build_audit_entry(request, response, event_type)

        # Log at appropriate level
        if status >= 500:
            logger.error(f"SECURITY_AUDIT: {audit_entry}")
        elif status == 403 or status == 401:
            logger.warning(f"SECURITY_AUDIT: {audit_entry}")
        elif event_type in ('login_success', 'login_failure', 'logout'):
            logger.info(f"SECURITY_AUDIT: {audit_entry}")
        else:
            logger.debug(f"SECURITY_AUDIT: {audit_entry}")

    def _get_event_type(self, path, status, method):
        """Determine the type of security event."""
        # Login events
        for login_path in self.AUDIT_PATHS['login']:
            if path.startswith(login_path):
                if method == 'POST':
                    if status == 302:
                        return 'login_success'
                    elif status == 200:
                        return 'login_failure'
                elif method == 'GET':
                    return 'login_page'

        # Admin access
        for admin_path in self.AUDIT_PATHS['admin']:
            if path.startswith(admin_path):
                if status == 200:
                    return 'admin_access'
                elif status == 302:
                    return 'admin_redirect'

        # Unauthorized access
        if status == 403:
            return 'unauthorized_access'
        if status == 401:
            return 'unauthenticated_access'

        # File operations
        for upload_path in self.AUDIT_PATHS['upload']:
            if path.startswith(upload_path):
                if method == 'POST':
                    return 'file_upload'
                elif 'download' in path:
                    return 'file_download'

        # Settings changes
        for settings_path in self.AUDIT_PATHS['settings']:
            if path.startswith(settings_path) and method == 'POST':
                return 'settings_change'

        # 404s on sensitive paths
        if status == 404:
            sensitive_patterns = ['admin', 'api', 'login', 'config', 'backup',
                                  'database', 'sql', '.env', 'wp-']
            for pattern in sensitive_patterns:
                if pattern in path:
                    return 'probe_scan'

        return None

    def _build_audit_entry(self, request, response, event_type):
        """Build a structured audit log entry with sanitized data."""
        entry = {
            'event': event_type,
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'ip': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:100],
        }

        # Add user info if available
        if request.user.is_authenticated:
            entry['user_id'] = request.user.id
            entry['username'] = request.user.username

        # Add correlation ID if available
        correlation_id = getattr(request, 'correlation_id', None)
        if correlation_id:
            entry['correlation_id'] = correlation_id

        # Sanitize POST data (only log on errors for privacy)
        if request.method == 'POST' and request.POST and response.status_code >= 400:
            sanitized_data = self._sanitize_data(dict(request.POST))
            if sanitized_data:
                entry['params'] = sanitized_data

        # Add referer for context
        referer = request.META.get('HTTP_REFERER', '')
        if referer:
            entry['referer'] = referer[:200]

        return str(entry)

    def _sanitize_data(self, data):
        """Remove sensitive parameters from logged data."""
        sanitized = {}
        for key, value in data.items():
            key_lower = key.lower()
            if key_lower in self.SENSITIVE_PARAMS:
                sanitized[key] = '***REDACTED***'
            else:
                # Truncate long values
                if isinstance(value, str) and len(value) > 100:
                    sanitized[key] = value[:100] + '...'
                elif isinstance(value, list):
                    sanitized[key] = [v[:50] + '...' if isinstance(v, str) and len(v) > 50 else v
                                      for v in value]
                else:
                    sanitized[key] = value
        return sanitized

    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request headers."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
