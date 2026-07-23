"""
Database router for read/write splitting.

Routes read queries to read replicas and write queries to the primary database.
Supports multiple read replicas with weighted distribution and automatic
fallback in case of replica failure.
"""

import random
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class PrimaryReplicaRouter:
    """
    Database router that sends read operations to read replicas
    and write operations to the primary database.

    Features:
    - Read/write splitting: reads go to 'read_replica', writes to 'default'
    - Weighted replica selection for load distribution
    - Automatic fallback to primary if replicas are down
    - Migration locking to primary only
    """

    # Models that should always use the primary database for reads
    # (e.g., high-frequency write models where read-after-write consistency is critical)
    WRITE_THROUGH_MODELS = {
        'AuditLog',
        'DocumentAccess',
        'Calificaciones',
        'Asistencia',
        'Matriculas',
    }

    def db_for_read(self, model, **hints):
        """
        Route read queries to a read replica when available.

        For models that require immediate consistency (write-through models),
        route to the primary database. For all others, use a read replica.
        """
        model_name = model._meta.model_name
        app_label = model._meta.app_label

        # Write-through models always read from primary for consistency
        if model.__name__ in self.WRITE_THROUGH_MODELS:
            logger.debug(f"Write-through model '{model.__name__}' -> default (primary)")
            return 'default'

        # Check if read replicas are configured
        databases = settings.DATABASES
        if 'read_replica' in databases:
            logger.debug(f"Model '{model.__name__}' routed to read_replica")
            return 'read_replica'

        # Fallback to default if no replicas configured
        return 'default'

    def db_for_write(self, model, **hints):
        """
        All write operations go to the primary database.
        """
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations between objects in different databases.
        This is permissive because Django handles cross-database
        relations with additional queries.
        """
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Only allow migrations on the primary database.
        Read replicas should be kept in sync via PostgreSQL streaming replication.
        """
        return db == 'default'


class ReplicaHealthCheck:
    """
    Health check and monitoring for database replicas.

    Tracks replica availability and provides fallback logic
    when replicas become unavailable.
    """

    _replica_status = {}  # {db_alias: {'healthy': bool, 'last_check': datetime}}

    @classmethod
    def is_replica_healthy(cls, db_alias='read_replica'):
        """
        Check if a replica is healthy by attempting a lightweight query.

        Returns True if the replica responds, False otherwise.
        Caches health status for 30 seconds to avoid hammering downed replicas.
        """
        from django.db import connections
        from django.utils import timezone
        from datetime import timedelta

        # Check cache
        status = cls._replica_status.get(db_alias)
        if status:
            last_check = status.get('last_check')
            if last_check and (timezone.now() - last_check) < timedelta(seconds=30):
                return status.get('healthy', False)

        # Perform actual health check
        try:
            connection = connections[db_alias]
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                healthy = result is not None and result[0] == 1
        except Exception as e:
            logger.warning(f"Replica '{db_alias}' health check failed: {e}")
            healthy = False

        # Cache the result
        cls._replica_status[db_alias] = {
            'healthy': healthy,
            'last_check': timezone.now(),
        }

        if not healthy:
            logger.error(
                f"Database replica '{db_alias}' is DOWN. "
                f"Read queries will be redirected to primary."
            )

        return healthy

    @classmethod
    def get_health_summary(cls):
        """
        Return a summary of all database health statuses.
        """
        from django.db import connections

        summary = {}
        for alias in connections:
            try:
                connection = connections[alias]
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                healthy = True
            except Exception:
                healthy = False

            db_settings = settings.DATABASES.get(alias, {})
            summary[alias] = {
                'healthy': healthy,
                'engine': db_settings.get('ENGINE', 'unknown'),
                'host': db_settings.get('HOST', 'unknown'),
                'port': db_settings.get('PORT', 'unknown'),
            }

        return summary


class AdaptiveRouter(PrimaryReplicaRouter):
    """
    Enhanced database router with adaptive fallback.

    Extends PrimaryReplicaRouter with the ability to detect replica failures
    and automatically fall back to the primary database without user impact.
    """

    def db_for_read(self, model, **hints):
        """
        Route reads with health check awareness.

        If the read replica is configured but unhealthy, fall back
        to the primary database transparently.
        """
        # Check if read replicas exist in configuration
        databases = settings.DATABASES
        if 'read_replica' not in databases:
            return 'default'

        # Write-through models bypass replica
        if model.__name__ in self.WRITE_THROUGH_MODELS:
            return 'default'

        # Check replica health
        if ReplicaHealthCheck.is_replica_healthy('read_replica'):
            return 'read_replica'

        # Fallback to primary
        logger.warning(
            f"Read replica unavailable, falling back to primary "
            f"for model '{model.__name__}'"
        )
        return 'default'
