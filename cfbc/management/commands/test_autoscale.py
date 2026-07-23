"""
Management command to test auto-scaling logic.

Simulates different load scenarios to verify the auto-scaler makes
correct scaling decisions without needing actual user traffic.

Usage:
    # Run all test scenarios
    python manage.py test_autoscale

    # Run specific test scenario
    python manage.py test_autoscale --scenario high_load
    python manage.py test_autoscale --scenario low_load
    python manage.py test_autoscale --scenario mixed

    # Verify dry-run mode works
    python manage.py test_autoscale --dry-run

    # Show current status
    python manage.py test_autoscale --status
"""

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Test auto-scaling logic with simulated metrics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--scenario', '-s',
            type=str,
            choices=['all', 'high_load', 'low_load', 'mixed',
                     'cpu_spike', 'memory_spike', 'request_surge'],
            default='all',
            help='Test scenario to run (default: all)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Do not execute scaling, only show decisions'
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show current auto-scaler status'
        )

    def handle(self, *args, **options):
        from cfbc.autoscaler import (
            AutoScaler, SystemMetrics, ScaleDirection, DEFAULT_CONFIG
        )
        from datetime import datetime

        config = getattr(settings, 'AUTOSCALER_CONFIG', {}).copy()
        config['dry_run'] = options['dry_run']
        config['min_instances'] = 2
        config['max_instances'] = 8

        scaler = AutoScaler(config)

        if options['status']:
            self._show_status(scaler)
            return

        scenario = options['scenario']

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Auto-Scaler Test Scenarios {'(DRY RUN)' if options['dry_run'] else ''}"
        ))
        self.stdout.write(f"  Mode: {config.get('deployment_mode', 'docker')}")
        self.stdout.write(f"  Min instances: {config['min_instances']}")
        self.stdout.write(f"  Max instances: {config['max_instances']}")
        self.stdout.write('')

        scenarios = {
            'high_load': self._scenario_high_load,
            'low_load': self._scenario_low_load,
            'mixed': self._scenario_mixed,
            'cpu_spike': self._scenario_cpu_spike,
            'memory_spike': self._scenario_memory_spike,
            'request_surge': self._scenario_request_surge,
        }

        if scenario == 'all':
            for name, func in scenarios.items():
                self._run_scenario(scaler, name, func, options['dry_run'])
        else:
            func = scenarios.get(scenario)
            if func:
                self._run_scenario(scaler, scenario, func, options['dry_run'])
            else:
                self.stdout.write(self.style.ERROR(f"Unknown scenario: {scenario}"))

    def _run_scenario(self, scaler, name, scenario_func, dry_run):
        """Run a single test scenario."""
        from datetime import timedelta

        self.stdout.write(self.style.MIGRATE_HEADING(f"Scenario: {name}"))
        metrics = scenario_func()

        base_time = datetime.now()
        cooldown_up = scaler.config.get('cooldown_period_scale_up', 120)
        cooldown_down = scaler.config.get('cooldown_period_scale_down', 300)

        for i, metric in enumerate(metrics):
            # Offset timestamps so cooldowns are respected between steps
            offset = (i + 1) * max(cooldown_up, cooldown_down)
            metric.timestamp = base_time + timedelta(seconds=offset)

            decision = scaler.policy_engine.evaluate(metric)
            self.stdout.write(
                f"  Step {i+1}: CPU={metric.cpu_percent:5.1f}% "
                f"Mem={metric.memory_percent:5.1f}% "
                f"Req/s={metric.request_rate:5.1f} "
                f"P95={metric.p95_response_time:.2f}s "
                f"Queue={metric.queue_depth:3d} "
                f"→ {decision[0].value.upper():4s} "
                f"({decision[1][:50]})"
            )

        # Run the full evaluation for the last metric in the scenario
        if not dry_run:
            self.stdout.write('')
            self.stdout.write("  🔄 Running full evaluation cycle...")
            event = scaler.evaluate_and_scale()
            if event.direction.value != 'none':
                color = self.style.SUCCESS if event.success else self.style.ERROR
                self.stdout.write(color(
                    f"     {event.direction.value}: "
                    f"{event.instances_before} → {event.instances_after} instances"
                ))
            else:
                self.stdout.write(f"     ✓ No scaling needed ({event.reason})")

    def _show_status(self, scaler):
        """Display current auto-scaler status."""
        status = scaler.get_status()
        self.stdout.write(self.style.MIGRATE_HEADING('Auto-Scaler Status'))
        for key, value in status.items():
            self.stdout.write(f"  {key}: {value}")

    # ── Test Scenarios ──────────────────────────────────────────────────

    def _scenario_high_load(self):
        """Simulate sustained high load that should trigger scale-up."""
        now = datetime.now()
        return [
            SystemMetrics(
                timestamp=now, cpu_percent=85.0, memory_percent=80.0,
                request_rate=75.0, avg_response_time=1.5, p95_response_time=2.1,
                active_instances=2, connection_pool_utilization=75.0,
                queue_depth=15, celery_queue_depth=5,
            ),
            SystemMetrics(
                timestamp=now, cpu_percent=90.0, memory_percent=82.0,
                request_rate=80.0, avg_response_time=1.8, p95_response_time=2.5,
                active_instances=2, connection_pool_utilization=80.0,
                queue_depth=20, celery_queue_depth=8,
            ),
            SystemMetrics(
                timestamp=now, cpu_percent=88.0, memory_percent=85.0,
                request_rate=70.0, avg_response_time=1.6, p95_response_time=2.3,
                active_instances=2, connection_pool_utilization=78.0,
                queue_depth=18, celery_queue_depth=6,
            ),
        ]

    def _scenario_low_load(self):
        """Simulate low load that should trigger scale-down."""
        now = datetime.now()
        return [
            SystemMetrics(
                timestamp=now, cpu_percent=20.0, memory_percent=35.0,
                request_rate=5.0, avg_response_time=0.2, p95_response_time=0.3,
                active_instances=8, connection_pool_utilization=20.0,
                queue_depth=1, celery_queue_depth=0,
            ),
            SystemMetrics(
                timestamp=now, cpu_percent=15.0, memory_percent=32.0,
                request_rate=3.0, avg_response_time=0.15, p95_response_time=0.25,
                active_instances=8, connection_pool_utilization=18.0,
                queue_depth=0, celery_queue_depth=0,
            ),
            SystemMetrics(
                timestamp=now, cpu_percent=18.0, memory_percent=30.0,
                request_rate=4.0, avg_response_time=0.18, p95_response_time=0.28,
                active_instances=8, connection_pool_utilization=15.0,
                queue_depth=0, celery_queue_depth=0,
            ),
        ]

    def _scenario_mixed(self):
        """Simulate fluctuating load to test stability."""
        now = datetime.now()
        return [
            SystemMetrics(
                timestamp=now, cpu_percent=25.0, memory_percent=45.0,
                request_rate=15.0, avg_response_time=0.3, p95_response_time=0.5,
                active_instances=4, connection_pool_utilization=30.0,
                queue_depth=2, celery_queue_depth=1,
            ),
            SystemMetrics(
                timestamp=now, cpu_percent=75.0, memory_percent=70.0,
                request_rate=55.0, avg_response_time=0.8, p95_response_time=1.2,
                active_instances=4, connection_pool_utilization=60.0,
                queue_depth=8, celery_queue_depth=3,
            ),
            SystemMetrics(
                timestamp=now, cpu_percent=30.0, memory_percent=50.0,
                request_rate=20.0, avg_response_time=0.4, p95_response_time=0.6,
                active_instances=4, connection_pool_utilization=35.0,
                queue_depth=3, celery_queue_depth=1,
            ),
            SystemMetrics(
                timestamp=now, cpu_percent=80.0, memory_percent=78.0,
                request_rate=65.0, avg_response_time=1.0, p95_response_time=1.5,
                active_instances=4, connection_pool_utilization=70.0,
                queue_depth=12, celery_queue_depth=4,
            ),
        ]

    def _scenario_cpu_spike(self):
        """Simulate a CPU spike to test response."""
        now = datetime.now()
        return [
            SystemMetrics(
                timestamp=now, cpu_percent=45.0, memory_percent=50.0,
                request_rate=30.0, avg_response_time=0.4, p95_response_time=0.6,
                active_instances=4, connection_pool_utilization=40.0,
                queue_depth=3, celery_queue_depth=2,
            ),
            SystemMetrics(
                timestamp=now, cpu_percent=95.0, memory_percent=55.0,
                request_rate=35.0, avg_response_time=0.5, p95_response_time=0.8,
                active_instances=4, connection_pool_utilization=45.0,
                queue_depth=5, celery_queue_depth=2,
            ),
            SystemMetrics(
                timestamp=now, cpu_percent=92.0, memory_percent=52.0,
                request_rate=32.0, avg_response_time=0.45, p95_response_time=0.7,
                active_instances=4, connection_pool_utilization=42.0,
                queue_depth=4, celery_queue_depth=2,
            ),
            SystemMetrics(
                timestamp=now, cpu_percent=50.0, memory_percent=50.0,
                request_rate=30.0, avg_response_time=0.4, p95_response_time=0.6,
                active_instances=4, connection_pool_utilization=40.0,
                queue_depth=3, celery_queue_depth=2,
            ),
        ]

    def _scenario_memory_spike(self):
        """Simulate a memory spike to test response."""
        now = datetime.now()
        return [
            SystemMetrics(
                timestamp=now, cpu_percent=50.0, memory_percent=85.0,
                request_rate=40.0, avg_response_time=0.6, p95_response_time=0.9,
                active_instances=4, connection_pool_utilization=50.0,
                queue_depth=4, celery_queue_depth=2,
            ),
            SystemMetrics(
                timestamp=now, cpu_percent=55.0, memory_percent=90.0,
                request_rate=45.0, avg_response_time=0.7, p95_response_time=1.0,
                active_instances=4, connection_pool_utilization=55.0,
                queue_depth=6, celery_queue_depth=3,
            ),
            SystemMetrics(
                timestamp=now, cpu_percent=52.0, memory_percent=88.0,
                request_rate=42.0, avg_response_time=0.65, p95_response_time=0.95,
                active_instances=4, connection_pool_utilization=52.0,
                queue_depth=5, celery_queue_depth=2,
            ),
        ]

    def _scenario_request_surge(self):
        """Simulate a sudden surge in request rate."""
        now = datetime.now()
        return [
            SystemMetrics(
                timestamp=now, cpu_percent=40.0, memory_percent=45.0,
                request_rate=100.0, avg_response_time=0.8, p95_response_time=1.5,
                active_instances=4, connection_pool_utilization=60.0,
                queue_depth=25, celery_queue_depth=10,
            ),
            SystemMetrics(
                timestamp=now, cpu_percent=65.0, memory_percent=50.0,
                request_rate=120.0, avg_response_time=1.2, p95_response_time=2.0,
                active_instances=4, connection_pool_utilization=70.0,
                queue_depth=35, celery_queue_depth=15,
            ),
            SystemMetrics(
                timestamp=now, cpu_percent=70.0, memory_percent=55.0,
                request_rate=110.0, avg_response_time=1.0, p95_response_time=1.8,
                active_instances=4, connection_pool_utilization=65.0,
                queue_depth=30, celery_queue_depth=12,
            ),
        ]
