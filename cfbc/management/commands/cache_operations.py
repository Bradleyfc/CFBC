"""
Management command for cache operations and monitoring.
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
import time
import json
from typing import Dict, Any

from cfbc.cache_utils import CacheMetrics
from cfbc.cache_signals import check_cache_health, warm_cache


class Command(BaseCommand):
    help = 'Manage Redis cache operations and monitor performance'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['stats', 'health', 'warm', 'clear', 'reset-metrics'],
            help='Action to perform'
        )
        parser.add_argument(
            '--pattern',
            default='*',
            help='Pattern for cache keys (for clear action)'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'stats':
            self.show_cache_stats()
        elif action == 'health':
            self.check_cache_health()
        elif action == 'warm':
            self.warm_cache()
        elif action == 'clear':
            self.clear_cache(options['pattern'])
        elif action == 'reset-metrics':
            self.reset_metrics()
    
    def show_cache_stats(self):
        """Display cache statistics."""
        stats = CacheMetrics.get_stats()
        
        self.stdout.write("Cache Statistics:")
        self.stdout.write(f"  Hits: {stats['hits']}")
        self.stdout.write(f"  Misses: {stats['misses']}")
        self.stdout.write(f"  Hit Ratio: {stats['hit_ratio']:.2%}")
        
        # Show some cache info if available
        try:
            # This is a simple test - in production you'd use Redis INFO command
            test_key = 'cfbc:stats_test'
            cache.set(test_key, 'test_value', 5)
            retrieved = cache.get(test_key)
            cache.delete(test_key)
            
            if retrieved == 'test_value':
                self.stdout.write(self.style.SUCCESS("  Cache backend: Working correctly"))
            else:
                self.stdout.write(self.style.WARNING("  Cache backend: May have issues"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Cache backend error: {e}"))
    
    def check_cache_health(self):
        """Check cache health status."""
        health_status = check_cache_health()
        
        self.stdout.write("Cache Health Check:")
        self.stdout.write(f"  Status: {health_status['status'].upper()}")
        
        if health_status['status'] == 'healthy':
            self.stdout.write(self.style.SUCCESS("  ✓ Cache is working correctly"))
        elif health_status['status'] == 'degraded':
            self.stdout.write(self.style.WARNING("  ⚠ Cache is degraded"))
            self.stdout.write(f"    Expected: {health_status['expected_value']}")
            self.stdout.write(f"    Retrieved: {health_status['retrieved_value']}")
        else:
            self.stdout.write(self.style.ERROR("  ✗ Cache is unhealthy"))
            self.stdout.write(f"    Error: {health_status['error']}")
    
    def warm_cache(self):
        """Warm up the cache by pre-loading frequently accessed data."""
        self.stdout.write("Warming cache...")
        
        if warm_cache():
            self.stdout.write(self.style.SUCCESS("Cache warm-up completed successfully"))
        else:
            self.stdout.write(self.style.ERROR("Cache warm-up failed"))
    
    def clear_cache(self, pattern='*'):
        """Clear cache keys matching pattern."""
        self.stdout.write(f"Clearing cache keys matching pattern: {pattern}")
        
        try:
            keys = cache.keys(pattern)
            if keys:
                deleted = cache.delete_many(keys)
                self.stdout.write(self.style.SUCCESS(f"Cleared {deleted} cache keys"))
            else:
                self.stdout.write("No cache keys found matching pattern")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error clearing cache: {e}"))
    
    def reset_metrics(self):
        """Reset cache performance metrics."""
        CacheMetrics.reset_metrics()
        self.stdout.write(self.style.SUCCESS("Cache metrics reset successfully"))


# Additional utility functions
def get_redis_info() -> Dict[str, Any]:
    """
    Get Redis server information if available.
    
    Returns:
        Dictionary with Redis server info
    """
    try:
        # Try to get Redis connection
        redis_client = cache.get_master_client()
        
        # This method varies by Redis client library
        # For django-redis, we can try to get info
        info = {}
        
        # Try different approaches to get Redis info
        if hasattr(redis_client, 'info'):
            info = redis_client.info()
        elif hasattr(cache, 'client'):
            try:
                client = cache.client.get_client()
                if hasattr(client, 'info'):
                    info = client.info()
            except:
                pass
        
        return info
        
    except Exception as e:
        return {'error': str(e), 'available': False}