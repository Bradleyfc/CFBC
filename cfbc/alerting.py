"""
Alerting and notification system for CFBC monitoring.

Provides:
- Threshold-based alert rules for critical metrics
- Multiple alert channels (log, file, email)
- Alert deduplication and rate limiting
- Alert escalation policies
- Alert history tracking

Usage:
    from cfbc.alerting import AlertManager

    alert_manager = AlertManager()
    alert_manager.check_and_alert(metric_name='cpu_usage', value=85.0, instance_id='app-1')
"""

import os
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field, asdict

from django.conf import settings

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Data Structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AlertRule:
    """Definition of an alert rule with threshold and severity."""
    name: str
    metric_name: str
    severity: str  # 'info', 'warning', 'critical'
    operator: str  # 'gt', 'lt', 'gte', 'lte', 'eq'
    threshold: float
    duration_seconds: int = 0  # How long the condition must persist
    description: str = ""
    enabled: bool = True
    cooldown_seconds: int = 300  # Minimum time between alerts (5 min default)
    channels: list = field(default_factory=lambda: ['log'])

    def evaluate(self, value: float) -> bool:
        """Evaluate if the current value triggers the alert rule."""
        try:
            if self.operator == 'gt':
                return value > self.threshold
            elif self.operator == 'lt':
                return value < self.threshold
            elif self.operator == 'gte':
                return value >= self.threshold
            elif self.operator == 'lte':
                return value <= self.threshold
            elif self.operator == 'eq':
                return value == self.threshold
            return False
        except (TypeError, ValueError):
            return False


@dataclass
class AlertEvent:
    """Record of a triggered alert."""
    rule_name: str
    metric_name: str
    severity: str
    value: float
    threshold: float
    instance_id: str
    timestamp: float
    message: str
    channel: str
    acknowledged: bool = False
    acknowledged_at: Optional[float] = None


# ─────────────────────────────────────────────────────────────────────────────
# Default Alert Rules
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_ALERT_RULES = [
    AlertRule(
        name='high_cpu',
        metric_name='cpu_usage',
        severity='warning',
        operator='gt',
        threshold=80.0,
        duration_seconds=120,
        description='CPU usage above 80% for 2 minutes',
        cooldown_seconds=300,
        channels=['log', 'file'],
    ),
    AlertRule(
        name='critical_cpu',
        metric_name='cpu_usage',
        severity='critical',
        operator='gt',
        threshold=90.0,
        duration_seconds=60,
        description='CPU usage above 90% for 1 minute',
        cooldown_seconds=120,
        channels=['log', 'file'],
    ),
    AlertRule(
        name='high_memory',
        metric_name='memory_usage',
        severity='warning',
        operator='gt',
        threshold=85.0,
        duration_seconds=120,
        description='Memory usage above 85% for 2 minutes',
        cooldown_seconds=300,
        channels=['log', 'file'],
    ),
    AlertRule(
        name='critical_memory',
        metric_name='memory_usage',
        severity='critical',
        operator='gt',
        threshold=95.0,
        duration_seconds=60,
        description='Memory usage above 95% for 1 minute',
        cooldown_seconds=120,
        channels=['log', 'file', 'email'],
    ),
    AlertRule(
        name='high_request_rate',
        metric_name='request_rate',
        severity='warning',
        operator='gt',
        threshold=100.0,
        duration_seconds=60,
        description='Request rate above 100 req/s for 1 minute',
        cooldown_seconds=300,
        channels=['log', 'file'],
    ),
    AlertRule(
        name='slow_response_time',
        metric_name='avg_response_time',
        severity='warning',
        operator='gt',
        threshold=2.0,
        duration_seconds=300,
        description='Average response time above 2s for 5 minutes',
        cooldown_seconds=300,
        channels=['log', 'file'],
    ),
    AlertRule(
        name='critical_response_time',
        metric_name='avg_response_time',
        severity='critical',
        operator='gt',
        threshold=5.0,
        duration_seconds=120,
        description='Average response time above 5s for 2 minutes',
        cooldown_seconds=120,
        channels=['log', 'file', 'email'],
    ),
    AlertRule(
        name='high_db_connections',
        metric_name='db_connections',
        severity='warning',
        operator='gt',
        threshold=80,
        duration_seconds=60,
        description='Database connections above 80% of pool',
        cooldown_seconds=300,
        channels=['log', 'file'],
    ),
    AlertRule(
        name='critical_db_connections',
        metric_name='db_connections',
        severity='critical',
        operator='gt',
        threshold=95,
        duration_seconds=30,
        description='Database connections above 95% of pool',
        cooldown_seconds=120,
        channels=['log', 'file', 'email'],
    ),
    AlertRule(
        name='high_error_rate',
        metric_name='error_rate',
        severity='warning',
        operator='gt',
        threshold=5.0,
        duration_seconds=120,
        description='Error rate above 5% for 2 minutes',
        cooldown_seconds=300,
        channels=['log', 'file'],
    ),
    AlertRule(
        name='critical_error_rate',
        metric_name='error_rate',
        severity='critical',
        operator='gt',
        threshold=10.0,
        duration_seconds=60,
        description='Error rate above 10% for 1 minute',
        cooldown_seconds=120,
        channels=['log', 'file', 'email'],
    ),
    AlertRule(
        name='disk_space_warning',
        metric_name='disk_free_percent',
        severity='warning',
        operator='lt',
        threshold=10.0,
        duration_seconds=0,
        description='Disk space below 10%',
        cooldown_seconds=3600,
        channels=['log', 'file'],
    ),
    AlertRule(
        name='disk_space_critical',
        metric_name='disk_free_percent',
        severity='critical',
        operator='lt',
        threshold=5.0,
        duration_seconds=0,
        description='Disk space below 5%',
        cooldown_seconds=1800,
        channels=['log', 'file', 'email'],
    ),
    AlertRule(
        name='celery_queue_backlog',
        metric_name='celery_queue_depth',
        severity='warning',
        operator='gt',
        threshold=100,
        duration_seconds=120,
        description='Celery queue backlog above 100 tasks for 2 minutes',
        cooldown_seconds=300,
        channels=['log', 'file'],
    ),
    AlertRule(
        name='celery_worker_down',
        metric_name='celery_workers',
        severity='critical',
        operator='lt',
        threshold=1,
        duration_seconds=60,
        description='No Celery workers responding',
        cooldown_seconds=60,
        channels=['log', 'file', 'email'],
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# Alert Manager
# ─────────────────────────────────────────────────────────────────────────────

class AlertManager:
    """
    Central alert management system.

    Features:
    - Checks metric values against configured alert rules
    - Supports multiple notification channels
    - Deduplication via cooldown periods
    - Alert escalation based on severity
    - Thread-safe operation
    """

    def __init__(self, rules: Optional[list] = None, config: Optional[dict] = None):
        """
        Initialize the AlertManager.

        Args:
            rules: List of AlertRule instances. Defaults to DEFAULT_ALERT_RULES.
            config: Override config dict. Keys: alert_log_file, enabled, etc.
        """
        self.rules = {rule.name: rule for rule in (rules or DEFAULT_ALERT_RULES)}
        self.config = {
            'enabled': True,
            'alert_log_file': os.getenv('ALERT_LOG_FILE', 'logs/alerts.log'),
            'alert_history_size': int(os.getenv('ALERT_HISTORY_SIZE', '1000')),
            'escalation_delay_minutes': int(os.getenv('ALERT_ESCALATION_DELAY', '15')),
        }
        if config:
            self.config.update(config)

        # Thread state
        self._lock = threading.Lock()
        self._last_alert_time: dict = {}  # rule_name -> timestamp
        self._condition_start: dict = {}  # metric_name -> (start_time, value)
        self._alert_history: list = []
        self._event_id_counter = 0

        # Ensure log directory exists
        log_dir = os.path.dirname(self.config['alert_log_file'])
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
            except OSError:
                pass

    # ── Rule Management ──────────────────────────────────────────────────

    def get_rules(self) -> dict:
        """Return all registered alert rules."""
        with self._lock:
            return {name: rule for name, rule in self.rules.items() if rule.enabled}

    def add_rule(self, rule: AlertRule) -> None:
        """Add or update an alert rule."""
        with self._lock:
            self.rules[rule.name] = rule

    def remove_rule(self, name: str) -> bool:
        """Remove an alert rule by name."""
        with self._lock:
            return self.rules.pop(name, None) is not None

    def enable_rule(self, name: str) -> bool:
        """Enable an alert rule."""
        with self._lock:
            if name in self.rules:
                self.rules[name].enabled = True
                return True
            return False

    def disable_rule(self, name: str) -> bool:
        """Disable an alert rule without removing it."""
        with self._lock:
            if name in self.rules:
                self.rules[name].enabled = False
                return True
            return False

    def _get_config(self, key: str, default=None):
        """Get configuration value with fallback."""
        return self.config.get(key, default)

    # ── Alert Evaluation ────────────────────────────────────────────────

    def check_and_alert(self, metric_name: str, value: float,
                        instance_id: str = 'unknown') -> list:
        """
        Evaluate a metric value against all matching alert rules and trigger alerts.

        Args:
            metric_name: The name of the metric (e.g., 'cpu_usage')
            value: The current numeric value
            instance_id: The instance reporting the metric

        Returns:
            List of triggered AlertEvent objects
        """
        if not self._get_config('enabled', True):
            return []

        triggered_events = []

        with self._lock:
            for rule in self.rules.values():
                if not rule.enabled:
                    continue

                # Check if rule applies to this metric
                if rule.metric_name != metric_name:
                    continue

                # Check cooldown period
                last_time = self._last_alert_time.get(rule.name, 0)
                if time.time() - last_time < rule.cooldown_seconds:
                    continue

                # Check duration condition
                if rule.duration_seconds > 0:
                    condition_key = f"{rule.name}:{metric_name}"
                    if rule.evaluate(value):
                        # Condition met - track start time
                        if condition_key not in self._condition_start:
                            self._condition_start[condition_key] = (time.time(), value)
                        else:
                            start_time, _ = self._condition_start[condition_key]
                            if time.time() - start_time >= rule.duration_seconds:
                                # Condition persisted long enough - trigger alert
                                events = self._trigger_alert(
                                    rule=rule,
                                    value=value,
                                    instance_id=instance_id,
                                )
                                triggered_events.extend(events)
                                del self._condition_start[condition_key]
                    else:
                        # Condition no longer met - reset
                        self._condition_start.pop(condition_key, None)
                else:
                    # Instant evaluation (no duration requirement)
                    if rule.evaluate(value):
                        events = self._trigger_alert(
                            rule=rule,
                            value=value,
                            instance_id=instance_id,
                        )
                        triggered_events.extend(events)

        return triggered_events

    # ── Alert Dispatch ──────────────────────────────────────────────────

    def _trigger_alert(self, rule: AlertRule, value: float,
                       instance_id: str) -> list:
        """Trigger an alert across all configured channels."""
        self._event_id_counter += 1
        events = []

        for channel in rule.channels:
            event = AlertEvent(
                rule_name=rule.name,
                metric_name=rule.metric_name,
                severity=rule.severity,
                value=value,
                threshold=rule.threshold,
                instance_id=instance_id,
                timestamp=time.time(),
                message=self._format_alert_message(rule, value, instance_id),
                channel=channel,
            )

            # Dispatch to channel
            dispatched = self._dispatch_alert(event, channel)
            if dispatched:
                events.append(event)
                self._alert_history.append(event)

        # Update last alert time for deduplication
        self._last_alert_time[rule.name] = time.time()

        # Trim history if needed
        max_history = self._get_config('alert_history_size', 1000)
        if len(self._alert_history) > max_history:
            self._alert_history = self._alert_history[-max_history:]

        return events

    def _dispatch_alert(self, event: AlertEvent, channel: str) -> bool:
        """Dispatch an alert to a specific channel."""
        try:
            if channel == 'log':
                self._log_alert(event)
                return True
            elif channel == 'file':
                self._file_alert(event)
                return True
            elif channel == 'email':
                self._email_alert(event)
                return True
            else:
                logger.warning(f"Unknown alert channel: {channel}")
                return False
        except Exception as e:
            logger.error(f"Failed to dispatch alert to {channel}: {e}")
            return False

    def _log_alert(self, event: AlertEvent) -> None:
        """Log the alert at the appropriate level."""
        log_method = {
            'critical': logger.critical,
            'warning': logger.warning,
            'info': logger.info,
        }.get(event.severity, logger.info)

        log_method(
            f"ALERT [{event.severity.upper()}] {event.rule_name}: "
            f"{event.message} | instance={event.instance_id} | "
            f"value={event.value:.2f} threshold={event.threshold}"
        )

    def _file_alert(self, event: AlertEvent) -> None:
        """Write the alert to the alert log file."""
        alert_file = self._get_config('alert_log_file', 'logs/alerts.log')
        try:
            with open(alert_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(event), default=str) + '\n')
        except (IOError, OSError) as e:
            logger.error(f"Failed to write alert to file: {e}")

    def _email_alert(self, event: AlertEvent) -> None:
        """Send an email alert for critical events."""
        # Try to send email using Django's email system
        try:
            from django.core.mail import send_mail
            subject = f"[{event.severity.upper()}] CFBC Alert: {event.rule_name}"
            message = (
                f"Alert: {event.rule_name}\n"
                f"Severity: {event.severity}\n"
                f"Metric: {event.metric_name}\n"
                f"Current Value: {event.value:.2f}\n"
                f"Threshold: {event.threshold}\n"
                f"Instance: {event.instance_id}\n"
                f"Timestamp: {datetime.fromtimestamp(event.timestamp).isoformat()}\n"
                f"Description: {event.message}\n"
            )
            recipients = os.getenv('ALERT_EMAIL_RECIPIENTS', 'admin@cfbc.edu.ni').split(',')
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[r.strip() for r in recipients if r.strip()],
                fail_silently=True,
            )
        except Exception as e:
            logger.warning(f"Email alert failed (non-critical): {e}")

    @staticmethod
    def _format_alert_message(rule: AlertRule, value: float, instance_id: str) -> str:
        """Format a human-readable alert message.
        The instance_id is included by the dispatch callers.
        """
        if rule.description:
            return rule.description
        direction = 'above' if rule.operator in ('gt', 'gte') else 'below' if rule.operator in ('lt', 'lte') else 'at'
        return (
            f"{rule.metric_name} is {direction} threshold: "
            f"{value:.2f} (threshold: {rule.threshold}, instance: {instance_id})"
        )

    # ── Alert History ───────────────────────────────────────────────────

    def get_alert_history(self, limit: int = 100,
                          severity: Optional[str] = None,
                          since: Optional[float] = None) -> list:
        """Get recent alert history with optional filtering."""
        with self._lock:
            history = self._alert_history[:]

        if severity:
            history = [e for e in history if e.severity == severity]
        if since:
            history = [e for e in history if e.timestamp >= since]

        # Sort by timestamp descending
        history.sort(key=lambda e: e.timestamp, reverse=True)
        return [asdict(e) for e in history[:limit]]

    def acknowledge_alert(self, rule_name: str, timestamp: float) -> bool:
        """Mark an alert event as acknowledged."""
        with self._lock:
            for event in reversed(self._alert_history):
                if event.rule_name == rule_name and event.timestamp == timestamp:
                    event.acknowledged = True
                    event.acknowledged_at = time.time()
                    return True
            return False

    def get_unacknowledged_count(self) -> int:
        """Get count of unacknowledged alerts."""
        with self._lock:
            return sum(1 for e in self._alert_history if not e.acknowledged)

    def get_active_alerts(self) -> list:
        """Get currently active (unacknowledged, recent) alerts."""
        fifteen_minutes_ago = time.time() - 900
        with self._lock:
            return [
                asdict(e) for e in self._alert_history
                if e.timestamp >= fifteen_minutes_ago and not e.acknowledged
            ]

    # ── Status ──────────────────────────────────────────────────────────

    def get_status(self) -> dict:
        """Get a status summary of the alerting system."""
        with self._lock:
            return {
                'enabled': self._get_config('enabled', True),
                'rules_total': len(self.rules),
                'rules_enabled': sum(1 for r in self.rules.values() if r.enabled),
                'rules_disabled': sum(1 for r in self.rules.values() if not r.enabled),
                'active_alerts': len(self.get_active_alerts()),
                'unacknowledged': self.get_unacknowledged_count(),
                'recent_history': len(self._alert_history),
                'channels_available': ['log', 'file', 'email'],
            }


# ─────────────────────────────────────────────────────────────────────────────
# Singleton instance (lazy-initialized)
# ─────────────────────────────────────────────────────────────────────────────

_alert_manager: Optional[AlertManager] = None
_alert_manager_lock = threading.Lock()


def get_alert_manager() -> AlertManager:
    """Get or create the singleton AlertManager instance."""
    global _alert_manager
    if _alert_manager is None:
        with _alert_manager_lock:
            if _alert_manager is None:
                _alert_manager = AlertManager()
    return _alert_manager


# ─────────────────────────────────────────────────────────────────────────────
# Health Check Integration
# ─────────────────────────────────────────────────────────────────────────────

def check_alerting_health() -> dict:
    """
    Health check function for the alerting system.
    Called by cfbc/views.py health_check endpoint.
    """
    try:
        manager = get_alert_manager()
        status = manager.get_status()
        return {
            'status': 'ok' if status['enabled'] else 'disabled',
            'active_alerts': status['active_alerts'],
            'unacknowledged': status['unacknowledged'],
            'rules_enabled': status['rules_enabled'],
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
        }
