"""
Database query logging middleware for performance optimization.
"""
import time
from django.db import connection
from django.conf import settings
import logging

logger = logging.getLogger('django.db.backends')

class QueryLoggingMiddleware:
    """
    Middleware to log slow database queries and track N+1 query problems.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.slow_query_threshold = getattr(settings, 'SLOW_QUERY_THRESHOLD', 0.1)  # 100ms default
    
    def __call__(self, request):
        # Initialize query tracking
        request._query_count = 0
        request._query_time = 0
        request._queries = []
        
        # Start timing
        start_time = time.time()
        
        # Process the request
        response = self.get_response(request)
        
        # Calculate total time
        total_time = time.time() - start_time
        
        # Log if queries exceed thresholds
        if request._query_count > 50:  # Too many queries
            logger.warning(
                f"High query count: {request._query_count} queries in {total_time:.3f}s "
                f"for {request.path} (user: {request.user})"
            )
        
        if request._query_time > 1.0:  # Too much time in queries
            logger.warning(
                f"High query time: {request._query_time:.3f}s total query time "
                f"in {total_time:.3f}s overall for {request.path}"
            )
        
        # Log individual slow queries
        for query_info in request._queries:
            if query_info['time'] > self.slow_query_threshold:
                logger.warning(
                    f"Slow query ({query_info['time']:.3f}s): {query_info['sql'][:200]}..."
                )
        
        return response


class QueryDebugMiddleware:
    """
    Debug middleware to track and analyze database queries.
    Can be enabled only in development.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Only enable in debug mode
        if not settings.DEBUG:
            return self.get_response(request)
        
        # Reset query count
        request._query_count_start = len(connection.queries)
        
        # Process the request
        response = self.get_response(request)
        
        # Calculate queries made during this request
        queries_made = len(connection.queries) - request._query_count_start
        
        if queries_made > 0:
            # Add debug headers
            response['X-DB-Queries'] = str(queries_made)
            response['X-DB-Time'] = str(
                sum(float(q['time']) for q in connection.queries[request._query_count_start:])
            )
        
        # Log warning for high query count
        if queries_made > 20:
            logger = logging.getLogger('django.db.performance')
            logger.warning(
                f"High query count detected: {queries_made} queries for {request.path}"
            )
            
            # Log duplicate queries (potential N+1 problems)
            sql_queries = [q['sql'] for q in connection.queries[request._query_count_start:]]
            from collections import Counter
            query_counts = Counter(sql_queries)
            for query, count in query_counts.items():
                if count > 5:  # Same query executed many times
                    logger.warning(
                        f"Potential N+1 query detected: same query executed {count} times: {query[:100]}..."
                    )
        
        return response


def query_profile_middleware(get_response):
    """
    Simple middleware to profile database queries.
    """
    def middleware(request):
        # Count queries before request
        initial_queries = len(connection.queries)
        initial_time = time.time()
        
        response = get_response(request)
        
        # Calculate queries made
        queries_made = len(connection.queries) - initial_queries
        query_time = sum(float(q['time']) for q in connection.queries[initial_queries:])
        total_time = time.time() - initial_time
        
        # Log performance metrics
        if queries_made > 10 or query_time > 0.5:
            logger = logging.getLogger('django.db.performance')
            logger.info(
                f"Query Profile - Path: {request.path}, "
                f"Queries: {queries_made}, "
                f"Query Time: {query_time:.3f}s, "
                f"Total Time: {total_time:.3f}s"
            )
        
        return response
    
    return middleware