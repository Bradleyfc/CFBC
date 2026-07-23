"""
Query logging configuration for performance optimization.
Add this to your settings.py:

# Add to INSTALLED_APPS:
INSTALLED_APPS += [
    'django.contrib.humanize',
    # ... other apps
]

# Add to MIDDLEWARE (at appropriate position):
MIDDLEWARE += [
    'cfbc.middleware.QueryLoggingMiddleware',
    # For development only:
    # 'cfbc.middleware.QueryDebugMiddleware',
]

# Configure logging:
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'performance_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': 'logs/performance.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.db.performance': {
            'handlers': ['performance_file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['performance_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
"""

import logging

# Configure logging for performance monitoring
def configure_performance_logging():
    """
    Configure logging for database performance monitoring.
    Call this function in your settings.py or asgi.py.
    """
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/performance.log'),
            logging.StreamHandler()
        ]
    )
    
    # Create specific logger for database performance
    db_logger = logging.getLogger('django.db.performance')
    db_logger.setLevel(logging.WARNING)


class PerformanceMetrics:
    """
    Utility class for tracking and reporting performance metrics.
    """
    
    @staticmethod
    def track_query_performance(view_name, query_count, query_time, total_time):
        """
        Track and log query performance for a view.
        
        Args:
            view_name: Name of the view being tracked
            query_count: Number of database queries executed
            query_time: Total time spent on queries (seconds)
            total_time: Total request time (seconds)
        """
        logger = logging.getLogger('django.db.performance')
        
        metrics = {
            'view': view_name,
            'query_count': query_count,
            'query_time': query_time,
            'total_time': total_time,
            'query_percentage': (query_time / total_time) * 100 if total_time > 0 else 0
        }
        
        # Log warning if thresholds exceeded
        if query_count > 50:
            logger.warning(
                f"High query count in {view_name}: {query_count} queries "
                f"({query_time:.3f}s query time, {total_time:.3f}s total)"
            )
        
        if query_time > 1.0:
            logger.warning(
                f"High query time in {view_name}: {query_time:.3f}s query time "
                f"({metrics['query_percentage']:.1f}% of {total_time:.3f}s total)"
            )
        
        # Log info for all views (adjust level as needed)
        logger.info(
            f"View {view_name}: {query_count} queries, "
            f"{query_time:.3f}s query time ({metrics['query_percentage']:.1f}%), "
            f"{total_time:.3f}s total"
        )
        
        return metrics


def get_slow_query_threshold():
    """
    Get the slow query threshold from settings or use default.
    """
    from django.conf import settings
    return getattr(settings, 'SLOW_QUERY_THRESHOLD', 0.1)  # 100ms default


def setup_query_monitoring():
    """
    Setup comprehensive query monitoring.
    """
    configure_performance_logging()
    
    logger = logging.getLogger(__name__)
    logger.info("Query performance monitoring configured")
    
    return True