"""
Auto-Scaling Configuration for CFBC Django Application
=======================================================

Provides a comprehensive auto-scaling system for Docker Compose and Systemd
deployments. Monitors application and system metrics, makes scaling decisions
based on configurable policies, and manages instance lifecycle.

Architecture:
    ┌─────────────────────────────────────────────┐
    │              AutoScaler                      │
    │  ┌──────────┐  ┌──────────┐  ┌────────────┐ │
    │  │Metrics   │  │Policies  │  │Instance    │ │
    │  │Collector │──│Engine    │──│Manager     │ │
    │  └──────────┘  └──────────┘  └────────────┘ │
    │                      │                       │
    │              ┌───────▼───────┐               │
    │              │Event Logger   │               │
    │              └───────────────┘               │
    └─────────────────────────────────────────────┘

Usage:
    # Run as a management command (recommended):
    python manage.py autoscale --interval 60

    # Or run as a Celery periodic task:
    # (Configure in django-celery-beat admin)
"""

import os
import re
import time
import json
import logging
import subprocess
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

import requests

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

# Default scaling configuration
DEFAULT_CONFIG = {
    'min_instances': 2,
    'max_instances': 8,
    'scale_up_threshold_cpu': 70.0,      # CPU percentage
    'scale_down_threshold_cpu': 30.0,    # CPU percentage
    'scale_up_threshold_memory': 75.0,   # Memory percentage
    'scale_down_threshold_memory': 40.0,  # Memory percentage
    'scale_up_threshold_request_rate': 50.0,  # Requests per second per instance
    'scale_down_threshold_request_rate': 10.0,  # Requests per second per instance
    'scale_up_threshold_response_time': 1.0,    # Seconds (95th percentile)
    'scale_down_threshold_response_time': 0.3,  # Seconds (95th percentile)
    'scale_up_threshold_queue_depth': 10,   # Pending requests in Nginx queue
    'scale_down_threshold_queue_depth': 3,  # Pending requests in Nginx queue
    'cooldown_period_scale_up': 120,    # Seconds to wait after scaling up
    'cooldown_period_scale_down': 300,  # Seconds to wait after scaling down
    'evaluation_period': 60,            # Seconds of data to evaluate
    'scale_up_step': 1,                 # Instances to add at a time
    'scale_down_step': 1,               # Instances to remove at a time
    'deployment_mode': 'docker',        # 'docker' or 'systemd'
    'docker_compose_file': 'deploy/docker-compose.prod.yml',
    'nginx_config_file': 'deploy/nginx/nginx.conf',
    'nginx_upstream_name': 'django_backend',
    'log_file': 'logs/autoscale.log',
    'health_check_retries': 3,
    'health_check_interval': 10,        # Seconds between health checks
}


# ─────────────────────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────────────────────

class ScaleDirection(Enum):
    """Direction of scaling action."""
    UP = 'up'
    DOWN = 'down'
    NONE = 'none'


class DeploymentMode(Enum):
    """Deployment mode for instance management."""
    DOCKER = 'docker'
    SYSTEMD = 'systemd'


@dataclass
class SystemMetrics:
    """Collected system metrics at a point in time."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    request_rate: float       # Requests per second per instance
    avg_response_time: float  # Average response time in seconds
    p95_response_time: float  # 95th percentile response time in seconds
    active_instances: int
    connection_pool_utilization: float  # Percentage
    queue_depth: int          # Nginx queue depth
    celery_queue_depth: int   # Celery task queue depth

    def to_dict(self) -> dict:
        return {k: v.isoformat() if isinstance(v, datetime) else v
                for k, v in asdict(self).items()}


@dataclass
class ScalingEvent:
    """Record of a scaling action."""
    timestamp: datetime
    direction: ScaleDirection
    instances_before: int
    instances_after: int
    reason: str
    metrics_snapshot: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'direction': self.direction.value,
            'instances_before': self.instances_before,
            'instances_after': self.instances_after,
            'reason': self.reason,
            'metrics_snapshot': self.metrics_snapshot,
            'success': self.success,
            'error_message': self.error_message,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Metrics Collector
# ─────────────────────────────────────────────────────────────────────────────

class MetricsCollector:
    """
    Collects system and application metrics for scaling decisions.

    Gathers data from:
    - System CPU, memory (via /proc/stat, /proc/meminfo or psutil if available)
    - Nginx stub_status (request rate, queue depth)
    - Django health endpoint (response times)
    - Database connection pool monitor
    - Celery queue inspection
    """

    def __init__(self, config: dict = None):
        self.config = config or DEFAULT_CONFIG.copy()
        self._history: List[SystemMetrics] = []
        self._lock = threading.Lock()
        self._psutil_available = self._check_psutil()

    def _check_psutil(self) -> bool:
        """Check if psutil is available for system metrics."""
        try:
            import psutil
            return True
        except ImportError:
            return False

    def collect(self) -> SystemMetrics:
        """Collect current system and application metrics."""
        metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=self._get_cpu_percent(),
            memory_percent=self._get_memory_percent(),
            request_rate=self._get_request_rate(),
            avg_response_time=self._get_avg_response_time(),
            p95_response_time=self._get_p95_response_time(),
            active_instances=self._get_active_instances(),
            connection_pool_utilization=self._get_connection_pool_utilization(),
            queue_depth=self._get_queue_depth(),
            celery_queue_depth=self._get_celery_queue_depth(),
        )

        with self._lock:
            self._history.append(metrics)
            # Keep only the last hour of history
            cutoff = datetime.now() - timedelta(hours=1)
            self._history = [m for m in self._history if m.timestamp > cutoff]

        return metrics

    def get_recent_metrics(self, seconds: int = 60) -> List[SystemMetrics]:
        """Get metrics from the last N seconds."""
        cutoff = datetime.now() - timedelta(seconds=seconds)
        with self._lock:
            return [m for m in self._history if m.timestamp > cutoff]

    def _get_cpu_percent(self) -> float:
        """Get current CPU usage percentage."""
        if self._psutil_available:
            try:
                import psutil
                return psutil.cpu_percent(interval=0.5)
            except Exception:
                pass

        # Fallback: read from /proc/stat
        try:
            with open('/proc/stat', 'r') as f:
                cpu_line = f.readline()
            parts = cpu_line.strip().split()
            if len(parts) >= 5:
                user, nice, system, idle = int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
                total = user + nice + system + idle
                active = user + nice + system
                if total > 0:
                    return (active / total) * 100
        except Exception:
            pass

        return 0.0

    def _get_memory_percent(self) -> float:
        """Get current memory usage percentage."""
        if self._psutil_available:
            try:
                import psutil
                return psutil.virtual_memory().percent
            except Exception:
                pass

        # Fallback: read from /proc/meminfo
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
            mem_total = None
            mem_available = None
            for line in lines:
                if line.startswith('MemTotal:'):
                    mem_total = int(line.split()[1])
                elif line.startswith('MemAvailable:'):
                    mem_available = int(line.split()[1])
                elif line.startswith('MemFree:'):
                    if mem_available is None:
                        mem_available = int(line.split()[1])
            if mem_total and mem_available:
                return ((mem_total - mem_available) / mem_total) * 100
        except Exception:
            pass

        return 0.0

    def _get_request_rate(self) -> float:
        """Estimate current request rate from cache or nginx."""
        # Try to get from cache (set by middleware)
        rate = cache.get('autoscale:request_rate')
        if rate is not None:
            return float(rate)

        # Fallback: read from nginx stub_status
        try:
            resp = requests.get('http://127.0.0.1:8080/nginx_status', timeout=2)
            if resp.status_code == 200:
                # Parse nginx stub_status output
                lines = resp.text.strip().split('\n')
                if len(lines) >= 3:
                    # Third line: "X active connections"
                    parts = lines[2].split()
                    if len(parts) >= 1:
                        active = int(parts[0])
                        # Rough estimate: active connections / instances
                        active_instances = max(self._get_active_instances(), 1)
                        return active / active_instances
        except requests.exceptions.ConnectionError:
            logger.warning("Nginx stub_status not available at "
                           "http://127.0.0.1:8080/nginx_status")
        except Exception as e:
            logger.warning(f"Failed to get request rate: {e}")

        return 0.0

    def _get_avg_response_time(self) -> float:
        """Get average response time in seconds."""
        # Try from cache (set by middleware)
        avg = cache.get('autoscale:avg_response_time')
        if avg is not None:
            return float(avg)
        return 0.0

    def _get_p95_response_time(self) -> float:
        """Get 95th percentile response time in seconds."""
        p95 = cache.get('autoscale:p95_response_time')
        if p95 is not None:
            return float(p95)
        return 0.0

    def _get_active_instances(self) -> int:
        """Get count of currently active application instances."""
        mode = self.config.get('deployment_mode', 'docker')

        if mode == 'docker':
            try:
                result = subprocess.run(
                    ['docker', 'ps', '--filter', 'name=cfbc-app', '--format', '{{.Names}}'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    return len([n for n in result.stdout.strip().split('\n') if n])
            except Exception:
                pass
        else:
            try:
                result = subprocess.run(
                    ['systemctl', 'list-units', '--type=service',
                     '--state=running', 'cfbc@*', '--no-legend'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    return len([l for l in result.stdout.strip().split('\n') if l])
            except Exception:
                pass

        return 0

    def _get_connection_pool_utilization(self) -> float:
        """Get database connection pool utilization percentage."""
        try:
            from django.db import connections
            from django.conf import settings

            total_max = 0
            used = 0
            for alias in connections:
                conn = connections[alias]
                try:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT count(*) as active,
                                   current_setting('max_connections') as max_conn
                            FROM pg_stat_activity
                            WHERE datname = current_database()
                        """)
                        row = cursor.fetchone()
                        if row:
                            used += row[0]
                            total_max += int(row[1])
                except Exception:
                    pass

            if total_max > 0:
                return (used / total_max) * 100
        except Exception:
            pass

        return 0.0

    def _get_queue_depth(self) -> int:
        """Get Nginx request queue depth."""
        try:
            resp = requests.get('http://127.0.0.1:8080/nginx_status', timeout=2)
            if resp.status_code == 200:
                lines = resp.text.strip().split('\n')
                if len(lines) >= 1:
                    # Last line: "Reading: X Writing: Y Waiting: Z"
                    last_line = lines[-1]
                    match = re.search(r'Waiting:\s*(\d+)', last_line)
                    if match:
                        return int(match.group(1))
        except requests.exceptions.ConnectionError:
            logger.warning("Nginx stub_status not available at "
                           "http://127.0.0.1:8080/nginx_status")
        except Exception as e:
            logger.warning(f"Failed to get queue depth: {e}")

        return 0

    def _get_celery_queue_depth(self) -> int:
        """Get Celery task queue depth (pending tasks)."""
        try:
            from celery import current_app

            inspect = current_app.control.inspect(timeout=2.0)
            if inspect:
                # reserved() returns tasks that have been received but not yet executed
                reserved = inspect.reserved()
                if reserved:
                    total = 0
                    for worker, tasks in reserved.items():
                        total += len(tasks)

                    # Also check scheduled tasks
                    scheduled = inspect.scheduled()
                    if scheduled:
                        for worker, tasks in scheduled.items():
                            total += len(tasks)

                    return total
        except Exception as e:
            logger.warning(f"Failed to get Celery queue depth: {e}")

        return 0


# ─────────────────────────────────────────────────────────────────────────────
# Scaling Policy Engine
# ─────────────────────────────────────────────────────────────────────────────

class ScalingPolicyEngine:
    """
    Evaluates system metrics against configured policies to determine
    if scaling actions should be taken.

    Uses a weighted scoring system to make robust scaling decisions,
    preventing flapping due to transient spikes.
    """

    def __init__(self, config: dict = None):
        self.config = config or DEFAULT_CONFIG.copy()
        self._last_scale_up = datetime.min
        self._last_scale_down = datetime.min
        self._lock = threading.Lock()

    def can_scale_up(self) -> bool:
        """Check if cooldown period for scaling up has elapsed."""
        with self._lock:
            elapsed = (datetime.now() - self._last_scale_up).total_seconds()
            return elapsed >= self.config.get('cooldown_period_scale_up', 120)

    def can_scale_down(self) -> bool:
        """Check if cooldown period for scaling down has elapsed."""
        with self._lock:
            elapsed = (datetime.now() - self._last_scale_down).total_seconds()
            return elapsed >= self.config.get('cooldown_period_scale_down', 300)

    def record_scale_up(self):
        """Record that a scale-up action was taken."""
        with self._lock:
            self._last_scale_up = datetime.now()

    def record_scale_down(self):
        """Record that a scale-down action was taken."""
        with self._lock:
            self._last_scale_down = datetime.now()

    def evaluate(self, metrics: SystemMetrics) -> Tuple[ScaleDirection, str]:
        """
        Evaluate current metrics against policies.

        Returns:
            Tuple of (direction, reason_string)
        """
        min_instances = self.config.get('min_instances', 2)
        max_instances = self.config.get('max_instances', 8)
        current_instances = metrics.active_instances

        # Don't scale below minimum
        if current_instances <= min_instances:
            if self._should_scale_up(metrics):
                return ScaleDirection.UP, self._build_reason(ScaleDirection.UP, metrics)
            return ScaleDirection.NONE, "At minimum instances, not scaling down"

        # Don't scale above maximum
        if current_instances >= max_instances:
            if self._should_scale_down(metrics):
                return ScaleDirection.DOWN, self._build_reason(ScaleDirection.DOWN, metrics)
            return ScaleDirection.NONE, "At maximum instances, not scaling up"

        # Evaluate scale up and down
        if self._should_scale_up(metrics) and self.can_scale_up():
            return ScaleDirection.UP, self._build_reason(ScaleDirection.UP, metrics)

        if self._should_scale_down(metrics) and self.can_scale_down():
            return ScaleDirection.DOWN, self._build_reason(ScaleDirection.DOWN, metrics)

        return ScaleDirection.NONE, "No scaling action needed"

    def _should_scale_up(self, metrics: SystemMetrics) -> bool:
        """Determine if conditions warrant scaling up."""
        score = 0
        thresholds_met = 0
        total_checks = 0

        # CPU threshold
        total_checks += 1
        if metrics.cpu_percent >= self.config['scale_up_threshold_cpu']:
            score += 1
            thresholds_met += 1

        # Memory threshold
        total_checks += 1
        if metrics.memory_percent >= self.config['scale_up_threshold_memory']:
            score += 1
            thresholds_met += 1

        # Request rate threshold
        total_checks += 1
        if metrics.request_rate >= self.config['scale_up_threshold_request_rate']:
            score += 1
            thresholds_met += 1

        # Response time threshold
        total_checks += 1
        if metrics.p95_response_time >= self.config['scale_up_threshold_response_time']:
            score += 1
            thresholds_met += 1

        # Queue depth threshold
        total_checks += 1
        metric = self.config['scale_up_threshold_queue_depth']
        if metrics.queue_depth >= metric:
            score += 1
            thresholds_met += 1

        # Scale up if majority of thresholds are met
        return thresholds_met >= (total_checks // 2 + 1)

    def _should_scale_down(self, metrics: SystemMetrics) -> bool:
        """Determine if conditions warrant scaling down."""
        score = 0
        thresholds_met = 0
        total_checks = 0

        # CPU threshold
        total_checks += 1
        if metrics.cpu_percent <= self.config['scale_down_threshold_cpu']:
            score += 1
            thresholds_met += 1

        # Memory threshold
        total_checks += 1
        if metrics.memory_percent <= self.config['scale_down_threshold_memory']:
            score += 1
            thresholds_met += 1

        # Request rate threshold
        total_checks += 1
        if metrics.request_rate <= self.config['scale_down_threshold_request_rate']:
            score += 1
            thresholds_met += 1

        # Response time threshold
        total_checks += 1
        if metrics.p95_response_time <= self.config['scale_down_threshold_response_time']:
            score += 1
            thresholds_met += 1

        # Queue depth threshold
        total_checks += 1
        if metrics.queue_depth <= self.config['scale_down_threshold_queue_depth']:
            score += 1
            thresholds_met += 1

        # Scale down if majority of thresholds are met and not at minimum
        return thresholds_met >= (total_checks // 2 + 1)

    def _build_reason(self, direction: ScaleDirection, metrics: SystemMetrics) -> str:
        """Build a human-readable reason for the scaling decision."""
        reasons = []
        if direction == ScaleDirection.UP:
            if metrics.cpu_percent >= self.config['scale_up_threshold_cpu']:
                reasons.append(f"CPU at {metrics.cpu_percent:.1f}%")
            if metrics.memory_percent >= self.config['scale_up_threshold_memory']:
                reasons.append(f"memory at {metrics.memory_percent:.1f}%")
            if metrics.request_rate >= self.config['scale_up_threshold_request_rate']:
                reasons.append(f"request rate at {metrics.request_rate:.1f} req/s")
            if metrics.p95_response_time >= self.config['scale_up_threshold_response_time']:
                reasons.append(f"P95 response time at {metrics.p95_response_time:.2f}s")
            if metrics.queue_depth >= self.config['scale_up_threshold_queue_depth']:
                reasons.append(f"queue depth at {metrics.queue_depth}")
        else:
            if metrics.cpu_percent <= self.config['scale_down_threshold_cpu']:
                reasons.append(f"CPU at {metrics.cpu_percent:.1f}%")
            if metrics.memory_percent <= self.config['scale_down_threshold_memory']:
                reasons.append(f"memory at {metrics.memory_percent:.1f}%")
            if metrics.request_rate <= self.config['scale_down_threshold_request_rate']:
                reasons.append(f"request rate at {metrics.request_rate:.1f} req/s")
            if metrics.p95_response_time <= self.config['scale_down_threshold_response_time']:
                reasons.append(f"P95 response time at {metrics.p95_response_time:.2f}s")
            if metrics.queue_depth <= self.config['scale_down_threshold_queue_depth']:
                reasons.append(f"queue depth at {metrics.queue_depth}")

        direction_str = "Scale Up" if direction == ScaleDirection.UP else "Scale Down"
        return f"{direction_str}: {', '.join(reasons)}"


# ─────────────────────────────────────────────────────────────────────────────
# Instance Lifecycle Manager
# ─────────────────────────────────────────────────────────────────────────────

class InstanceManager:
    """
    Manages application instance lifecycle for both Docker and Systemd deployments.

    Handles:
    - Starting new instances
    - Stopping instances gracefully
    - Health checking instances
    - Updating Nginx upstream configuration
    """

    def __init__(self, config: dict = None):
        self.config = config or DEFAULT_CONFIG.copy()
        self.mode = DeploymentMode(self.config.get('deployment_mode', 'docker'))

    def scale_up(self, count: int = 1) -> bool:
        """
        Add application instances.

        Args:
            count: Number of instances to add

        Returns:
            True if successful, False otherwise
        """
        current = self._get_current_instances()
        target = current + count
        max_instances = self.config.get('max_instances', 8)
        target = min(target, max_instances)

        if target <= current:
            logger.info(f"Already at {current} instances, no scale-up needed")
            return True

        logger.info(f"Scaling UP from {current} to {target} instances (+{count})")

        try:
            if self.mode == DeploymentMode.DOCKER:
                return self._docker_scale(target)
            else:
                return self._systemd_scale(target)
        except Exception as e:
            logger.error(f"Scale up failed: {e}")
            return False

    def scale_down(self, count: int = 1) -> bool:
        """
        Remove application instances.

        Args:
            count: Number of instances to remove

        Returns:
            True if successful, False otherwise
        """
        current = self._get_current_instances()
        target = current - count
        min_instances = self.config.get('min_instances', 2)
        target = max(target, min_instances)

        if target >= current:
            logger.info(f"Already at {current} instances, no scale-down needed")
            return True

        logger.info(f"Scaling DOWN from {current} to {target} instances (-{count})")

        try:
            if self.mode == DeploymentMode.DOCKER:
                return self._docker_scale(target)
            else:
                return self._systemd_scale(target)
        except Exception as e:
            logger.error(f"Scale down failed: {e}")
            return False

    def check_health(self, instance_name: str) -> bool:
        """
        Check if a specific instance is healthy.

        Args:
            instance_name: Container name or systemd service name

        Returns:
            True if healthy, False otherwise
        """
        if self.mode == DeploymentMode.DOCKER:
            try:
                result = subprocess.run(
                    ['docker', 'inspect', '--format', '{{.State.Health.Status}}',
                     instance_name],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    return result.stdout.strip() == 'healthy'
            except Exception:
                pass
        else:
            try:
                result = subprocess.run(
                    ['systemctl', 'is-active', instance_name],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    return result.stdout.strip() == 'active'
            except Exception:
                pass

        return False

    def wait_for_healthy(self, instance_name: str, max_retries: int = 3,
                         interval: int = 10) -> bool:
        """
        Wait for an instance to become healthy.

        Args:
            instance_name: Name of the instance to check
            max_retries: Maximum number of health check attempts
            interval: Seconds between checks

        Returns:
            True if healthy within retries, False otherwise
        """
        for attempt in range(1, max_retries + 1):
            if self.check_health(instance_name):
                logger.info(f"Instance {instance_name} is healthy (attempt {attempt})")
                return True
            logger.info(f"Waiting for {instance_name} to become healthy "
                        f"(attempt {attempt}/{max_retries})...")
            time.sleep(interval)
        return False

    def _get_current_instances(self) -> int:
        """Get count of currently running instances."""
        if self.mode == DeploymentMode.DOCKER:
            try:
                result = subprocess.run(
                    ['docker', 'ps', '--filter', 'name=cfbc-app', '--format', '{{.Names}}'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    return len([n for n in result.stdout.strip().split('\n') if n])
            except Exception:
                pass
        else:
            try:
                result = subprocess.run(
                    ['systemctl', 'list-units', '--type=service',
                     '--state=running', 'cfbc@*', '--no-legend'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    return len([l for l in result.stdout.strip().split('\n') if l])
            except Exception:
                pass
        return 0

    def _docker_scale(self, target: int) -> bool:
        """Scale Docker Compose to target instance count."""
        compose_file = self.config.get('docker_compose_file', 'deploy/docker-compose.prod.yml')

        # Docker Compose v2 syntax
        result = subprocess.run(
            ['docker', 'compose', '-f', compose_file, 'up', '-d',
             '--scale', f'app={target}', '--no-recreate', 'app'],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            logger.error(f"Docker scale failed: {result.stderr}")
            return False

        # Wait for new instances to become healthy
        time.sleep(5)
        for i in range(1, target + 1):
            self.wait_for_healthy(
                f'cfbc-app-{i}',
                max_retries=self.config.get('health_check_retries', 3),
                interval=self.config.get('health_check_interval', 10)
            )

        # Reload Nginx to pick up new instances
        self._reload_nginx()

        return True

    def _systemd_scale(self, target: int) -> bool:
        """Scale systemd services to target instance count."""
        # Get list of currently running instances
        # systemctl output format: "cfbc@8001.service   loaded active running   ..."
        running_ports = set()
        try:
            result = subprocess.run(
                ['systemctl', 'list-units', '--type=service',
                 '--state=running', 'cfbc@*', '--no-legend'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split()
                        if parts:
                            # Extract port from "cfbc@8001.service"
                            service_name = parts[0]
                            port_match = re.search(r'@(\d+)', service_name)
                            if port_match:
                                running_ports.add(int(port_match.group(1)))
        except Exception:
            pass

        # Base ports: 8001, 8002, 8003, ...
        base_port = 8001
        needed_ports = set(range(base_port, base_port + target))

        # Remove excess instances
        for port_num in sorted(running_ports):
            if port_num not in needed_ports:
                try:
                    result = subprocess.run(
                        ['sudo', 'systemctl', 'stop', f'cfbc@{port_num}'],
                        capture_output=True, text=True, timeout=30
                    )
                    if result.returncode != 0:
                        logger.warning(f"Failed to stop cfbc@{port_num}: {result.stderr}")
                    else:
                        logger.info(f"Stopped systemd instance cfbc@{port_num}")

                    result = subprocess.run(
                        ['sudo', 'systemctl', 'disable', f'cfbc@{port_num}'],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode != 0:
                        logger.warning(f"Failed to disable cfbc@{port_num}: {result.stderr}")
                except Exception as e:
                    logger.error(f"Error stopping cfbc@{port_num}: {e}")

        # Add missing instances
        for port_num in sorted(needed_ports):
            service_name = f'cfbc@{port_num}'
            if port_num not in running_ports:
                try:
                    result = subprocess.run(
                        ['sudo', 'systemctl', 'enable', service_name],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode != 0:
                        logger.warning(f"Failed to enable {service_name}: {result.stderr}")

                    result = subprocess.run(
                        ['sudo', 'systemctl', 'start', service_name],
                        capture_output=True, text=True, timeout=30
                    )
                    if result.returncode != 0:
                        logger.warning(f"Failed to start {service_name}: {result.stderr}")
                    else:
                        logger.info(f"Started systemd instance {service_name}")
                except Exception as e:
                    logger.error(f"Error starting {service_name}: {e}")

        # Wait for health checks
        for port_num in sorted(needed_ports):
            self.wait_for_healthy(
                f'cfbc@{port_num}',
                max_retries=self.config.get('health_check_retries', 3),
                interval=self.config.get('health_check_interval', 10)
            )

        # Update Nginx upstream
        self._update_nginx_upstream(target)

        return True

    def _reload_nginx(self) -> bool:
        """Reload Nginx configuration gracefully."""
        try:
            if self.mode == DeploymentMode.DOCKER:
                compose_file = self.config.get('docker_compose_file')
                result = subprocess.run(
                    ['docker', 'compose', '-f', compose_file, 'exec',
                     '-T', 'nginx', 'nginx', '-s', 'reload'],
                    capture_output=True, text=True, timeout=15
                )
                if result.returncode != 0:
                    logger.error(f"Nginx reload failed: {result.stderr}")
                    return False
            else:
                result = subprocess.run(
                    ['sudo', 'nginx', '-s', 'reload'],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode != 0:
                    logger.error(f"Nginx reload failed: {result.stderr}")
                    return False
            logger.info("Nginx reloaded successfully")
            return True
        except Exception as e:
            logger.error(f"Nginx reload failed: {e}")
            return False

    def _update_nginx_upstream(self, instance_count: int) -> None:
        """
        Update Nginx upstream configuration with current instances.
        This is only needed for systemd deployments where instances
        have dynamic ports.
        """
        if self.mode != DeploymentMode.SYSTEMD:
            return

        nginx_conf = self.config.get('nginx_config_file', 'deploy/nginx/nginx.conf')
        upstream_name = self.config.get('nginx_upstream_name', 'django_backend')

        try:
            with open(nginx_conf, 'r') as f:
                content = f.read()

            # Build new upstream block
            upstream_block = f'    upstream {upstream_name} {{\n'
            upstream_block += '        ip_hash;\n'
            base_port = 8001
            for i in range(instance_count):
                port = base_port + i
                upstream_block += (
                    f'        server 127.0.0.1:{port} '
                    f'max_fails=3 fail_timeout=30s weight=1;\n'
                )
            upstream_block += '        keepalive 32;\n    }'

            # Replace existing upstream block
            pattern = rf'upstream {re.escape(upstream_name)} \{{.*?\n    \}}'
            new_content = re.sub(
                pattern, upstream_block, content, flags=re.DOTALL
            )

            if new_content != content:
                with open(nginx_conf, 'w') as f:
                    f.write(new_content)
                logger.info(f"Updated Nginx upstream configuration for {instance_count} instances")
                self._reload_nginx()

        except Exception as e:
            logger.error(f"Failed to update Nginx config: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Event Logger
# ─────────────────────────────────────────────────────────────────────────────

class ScalingEventLogger:
    """
    Logs auto-scaling events to both the application log and a structured
    JSON file for analysis and monitoring.
    """

    def __init__(self, config: dict = None):
        self.config = config or DEFAULT_CONFIG.copy()
        self.events: List[ScalingEvent] = []
        self._lock = threading.Lock()
        self._setup_file_logging()

    def _setup_file_logging(self):
        """Setup logging to file for auto-scaling events."""
        log_file = self.config.get('log_file', 'logs/autoscale.log')
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        self._file_handler = logging.FileHandler(log_file)
        self._file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        self._file_handler.setFormatter(formatter)

        # Add handler to the autoscaler logger
        self._logger = logging.getLogger('cfbc.autoscaler.events')
        self._logger.setLevel(logging.INFO)
        self._logger.addHandler(self._file_handler)
        self._logger.propagate = False  # Don't propagate to root logger

    def log_event(self, event: ScalingEvent):
        """Log a scaling event."""
        with self._lock:
            self.events.append(event)
            # Keep only last 1000 events in memory
            if len(self.events) > 1000:
                self.events = self.events[-1000:]

        # Log to file
        direction_emoji = '⬆' if event.direction == ScaleDirection.UP else '⬇'
        status = '✅' if event.success else '❌'
        self._logger.info(
            f"{status} {direction_emoji} Scale {event.direction.value}: "
            f"{event.instances_before} → {event.instances_after} instances. "
            f"Reason: {event.reason}"
            + (f" Error: {event.error_message}" if event.error_message else "")
        )

        # Log to application logger
        if event.success:
            logger.info(
                f"Auto-scale {event.direction.value}: "
                f"{event.instances_before} → {event.instances_after} instances. "
                f"{event.reason}"
            )
        else:
            logger.error(
                f"Auto-scale {event.direction.value} FAILED: "
                f"{event.reason}. Error: {event.error_message}"
            )

        # Store event in cache for monitoring
        self._store_in_cache(event)

    def get_recent_events(self, limit: int = 20) -> List[ScalingEvent]:
        """Get the most recent scaling events."""
        with self._lock:
            return list(reversed(self.events[-limit:]))

    def _store_in_cache(self, event: ScalingEvent):
        """Store event in Redis cache for monitoring dashboards."""
        try:
            key = f'autoscale:events:{event.timestamp.strftime("%Y%m%d")}'
            events = cache.get(key) or []
            events.append(event.to_dict())
            # Keep only last 100 events per day
            if len(events) > 100:
                events = events[-100:]
            cache.set(key, events, timeout=86400)  # 24 hours
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# Auto-Scaler Orchestrator
# ─────────────────────────────────────────────────────────────────────────────

class AutoScaler:
    """
    Main auto-scaling orchestrator that ties together metrics collection,
    policy evaluation, instance management, and event logging.

    Usage:
        scaler = AutoScaler(config={...})
        scaler.evaluate_and_scale()  # Single evaluation
        scaler.run_loop(interval=60)  # Continuous loop
    """

    def __init__(self, config: dict = None):
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.metrics_collector = MetricsCollector(self.config)
        self.policy_engine = ScalingPolicyEngine(self.config)
        self.instance_manager = InstanceManager(self.config)
        self.event_logger = ScalingEventLogger(self.config)
        self._running = False
        self._stop_event = threading.Event()

    def evaluate_and_scale(self) -> ScalingEvent:
        """
        Run a single evaluation cycle: collect metrics, evaluate policies,
        and execute scaling action if needed.

        Returns:
            ScalingEvent with the result
        """
        # Collect current metrics
        metrics = self.metrics_collector.collect()
        dry_run = self.config.get('dry_run', False)

        # Evaluate policies
        direction, reason = self.policy_engine.evaluate(metrics)

        if direction == ScaleDirection.NONE:
            return ScalingEvent(
                timestamp=datetime.now(),
                direction=ScaleDirection.NONE,
                instances_before=metrics.active_instances,
                instances_after=metrics.active_instances,
                reason=reason,
                metrics_snapshot=metrics.to_dict(),
                success=True,
            )

        # Execute scaling action (skip if dry run)
        instances_before = metrics.active_instances
        success = False
        error_message = None
        instances_after = instances_before

        if dry_run:
            success = True
            error_message = "DRY RUN - no actual scaling performed"
            if direction == ScaleDirection.UP:
                step = self.config.get('scale_up_step', 1)
                instances_after = instances_before + step
            else:
                step = self.config.get('scale_down_step', 1)
                instances_after = max(
                    instances_before - step,
                    self.config.get('min_instances', 2)
                )
        elif direction == ScaleDirection.UP:
            step = self.config.get('scale_up_step', 1)
            success = self.instance_manager.scale_up(step)
            if success:
                self.policy_engine.record_scale_up()
                instances_after = self.instance_manager._get_current_instances()
        else:
            step = self.config.get('scale_down_step', 1)
            success = self.instance_manager.scale_down(step)
            if success:
                self.policy_engine.record_scale_down()
                instances_after = self.instance_manager._get_current_instances()

        if not success and not dry_run:
            error_message = "Scaling action failed (see logs for details)"

        event = ScalingEvent(
            timestamp=datetime.now(),
            direction=direction,
            instances_before=instances_before,
            instances_after=instances_after,
            reason=reason,
            metrics_snapshot=metrics.to_dict(),
            success=success,
            error_message=error_message,
        )

        self.event_logger.log_event(event)
        return event

    def run_loop(self, interval: int = 60):
        """
        Run the auto-scaler in a continuous loop.

        Args:
            interval: Seconds between evaluations
        """
        self._running = True
        self._stop_event.clear()

        logger.info(
            f"Auto-scaler started: checking every {interval}s, "
            f"min={self.config['min_instances']}, "
            f"max={self.config['max_instances']} instances"
        )

        cycle_count = 0
        while not self._stop_event.is_set():
            try:
                cycle_count += 1
                event = self.evaluate_and_scale()

                if event.direction != ScaleDirection.NONE:
                    logger.info(
                        f"Cycle #{cycle_count}: {event.direction.value.upper()} "
                        f"({event.instances_before} → {event.instances_after}) - "
                        f"{event.reason}"
                    )

            except Exception as e:
                logger.error(f"Auto-scaler cycle #{cycle_count} failed: {e}", exc_info=True)

            # Wait for next cycle (check for stop every second)
            for _ in range(interval):
                if self._stop_event.is_set():
                    break
                time.sleep(1)

        self._running = False
        logger.info("Auto-scaler stopped")

    def stop(self):
        """Stop the auto-scaler loop."""
        self._stop_event.set()

    @property
    def is_running(self) -> bool:
        return self._running

    def get_status(self) -> Dict[str, Any]:
        """Get current auto-scaler status."""
        return {
            'running': self._running,
            'config': {
                'min_instances': self.config['min_instances'],
                'max_instances': self.config['max_instances'],
                'cooldown_scale_up': self.config['cooldown_period_scale_up'],
                'cooldown_scale_down': self.config['cooldown_period_scale_down'],
                'deployment_mode': self.config['deployment_mode'],
            },
            'can_scale_up': self.policy_engine.can_scale_up(),
            'can_scale_down': self.policy_engine.can_scale_down(),
            'recent_events': [
                e.to_dict() for e in self.event_logger.get_recent_events(5)
            ],
        }


# ─────────────────────────────────────────────────────────────────────────────
# Convenience function for management command
# ─────────────────────────────────────────────────────────────────────────────

def create_default_scaler() -> AutoScaler:
    """
    Create an AutoScaler with settings from Django settings.
    """
    config = DEFAULT_CONFIG.copy()
    config.update(getattr(settings, 'AUTOSCALER_CONFIG', {}))
    return AutoScaler(config)
