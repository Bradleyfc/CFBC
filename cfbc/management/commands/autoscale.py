"""
Management command for running the CFBC auto-scaler.

Usage:
    # Run a single evaluation cycle
    python manage.py autoscale --once

    # Run continuously (default)
    python manage.py autoscale --interval 60

    # Show current status
    python manage.py autoscale --status

    # Dry run (show what would be done without scaling)
    python manage.py autoscale --dry-run

    # With custom config
    python manage.py autoscale --interval 30 --min-instances 2 --max-instances 8

    # Verbose mode (log to console)
    python manage.py autoscale --interval 60 --verbose
"""

import os
import sys
import signal
import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

logger = logging.getLogger(__name__)


def _setup_logging(verbose: bool = False):
    """Configure logging for the auto-scaler."""
    root_logger = logging.getLogger('cfbc.autoscaler')
    root_logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Remove any existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler (for verbose mode)
    if verbose:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Ensure autoscale.log handler is also set up by the AutoScaler's
    # ScalingEventLogger when it initializes. The logger won't propagate
    # to avoid duplicate messages.


class Command(BaseCommand):
    help = 'Auto-scale application instances based on system metrics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval', '-i',
            type=int,
            default=60,
            help='Seconds between evaluation cycles (default: 60)'
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Run a single evaluation cycle and exit'
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show auto-scaler status and exit'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually scaling'
        )
        parser.add_argument(
            '--min-instances',
            type=int,
            default=None,
            help='Minimum number of application instances'
        )
        parser.add_argument(
            '--max-instances',
            type=int,
            default=None,
            help='Maximum number of application instances'
        )
        parser.add_argument(
            '--mode',
            choices=['docker', 'systemd'],
            default=None,
            help='Deployment mode (docker or systemd)'
        )
        parser.add_argument(
            '--log-file',
            type=str,
            default=None,
            help='Path to log file for auto-scaling events'
        )
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose logging to console'
        )

    def handle(self, *args, **options):
        # Setup logging first
        _setup_logging(verbose=options.get('verbose', False))

        # Build config from Django settings + CLI options
        config = getattr(settings, 'AUTOSCALER_CONFIG', {}).copy()

        if options['min_instances'] is not None:
            config['min_instances'] = options['min_instances']
        if options['max_instances'] is not None:
            config['max_instances'] = options['max_instances']
        if options['mode'] is not None:
            config['deployment_mode'] = options['mode']
        if options['log_file'] is not None:
            config['log_file'] = options['log_file']
        if options['dry_run']:
            config['dry_run'] = True

        # Import autoscaler
        from cfbc.autoscaler import (
            AutoScaler, create_default_scaler, DEFAULT_CONFIG
        )

        scaler = AutoScaler(config)

        if options['status']:
            self._show_status(scaler)
            return

        if options['once']:
            self._run_once(scaler, options['dry_run'])
            return

        # Continuous mode - run until interrupted
        self._run_loop(scaler, options)

    def _show_status(self, scaler):
        """Display auto-scaler status."""
        status = scaler.get_status()

        self.stdout.write(self.style.MIGRATE_HEADING('Auto-Scaler Status'))
        self.stdout.write(f"  Running: {status['running']}")
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('Configuration:'))
        self.stdout.write(f"  Min instances: {status['config']['min_instances']}")
        self.stdout.write(f"  Max instances: {status['config']['max_instances']}")
        self.stdout.write(f"  Cooldown (up): {status['config']['cooldown_scale_up']}s")
        self.stdout.write(f"  Cooldown (down): {status['config']['cooldown_scale_down']}s")
        self.stdout.write(f"  Mode: {status['config']['deployment_mode']}")
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('Policy State:'))
        self.stdout.write(f"  Can scale up: {status['can_scale_up']}")
        self.stdout.write(f"  Can scale down: {status['can_scale_down']}")
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('Recent Events:'))
        for event in status['recent_events']:
            direction = (
                '⬆ UP' if event['direction'] == 'up'
                else '⬇ DOWN' if event['direction'] == 'down'
                else '➖ NONE'
            )
            self.stdout.write(
                f"  {event['timestamp']} | {direction} | "
                f"{event['instances_before']} → {event['instances_after']} | "
                f"{event['reason'][:80]}"
            )

    def _run_once(self, scaler, dry_run=False):
        """Run a single evaluation cycle."""
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Auto-scaler evaluation {'(DRY RUN)' if dry_run else ''}"
        ))

        try:
            event = scaler.evaluate_and_scale()

            direction_emoji = {
                'up': '⬆',
                'down': '⬇',
                'none': '➖',
            }.get(event.direction.value, '➖')

            color = self.style.SUCCESS if event.success else self.style.ERROR

            self.stdout.write(color(
                f"  {direction_emoji} Decision: {event.direction.value.upper()}"
            ))
            self.stdout.write(f"  Instances: {event.instances_before} → {event.instances_after}")
            self.stdout.write(f"  Reason: {event.reason}")

            if event.metrics_snapshot:
                self.stdout.write('')
                self.stdout.write(self.style.MIGRATE_HEADING('Metrics:'))
                metrics = event.metrics_snapshot
                self.stdout.write(f"  CPU: {metrics.get('cpu_percent', 'N/A'):>5.1f}%")
                self.stdout.write(f"  Memory: {metrics.get('memory_percent', 'N/A'):>5.1f}%")
                self.stdout.write(f"  Request rate: {metrics.get('request_rate', 'N/A'):>5.1f} req/s")
                self.stdout.write(f"  P95 response: {metrics.get('p95_response_time', 'N/A'):>5.2f}s")
                self.stdout.write(f"  Queue depth: {metrics.get('queue_depth', 'N/A'):>5}")
                self.stdout.write(f"  Conn pool: {metrics.get('connection_pool_utilization', 'N/A'):>5.1f}%")
                self.stdout.write(f"  Celery queue: {metrics.get('celery_queue_depth', 'N/A'):>5}")

            if event.error_message:
                self.stdout.write(self.style.ERROR(f"  Error: {event.error_message}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Evaluation failed: {e}"))

    def _run_loop(self, scaler, options):
        """Run the auto-scaler in a continuous loop."""
        interval = options['interval']

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Auto-scaler started (interval: {interval}s)"
        ))
        self.stdout.write(f"  Min instances: {scaler.config.get('min_instances', 2)}")
        self.stdout.write(f"  Max instances: {scaler.config.get('max_instances', 8)}")
        self.stdout.write(f"  Mode: {scaler.config.get('deployment_mode', 'docker')}")
        self.stdout.write(f"  Dry run: {options.get('dry_run', False)}")
        self.stdout.write('')
        self.stdout.write("Press Ctrl+C to stop.")
        self.stdout.write('')

        # Handle graceful shutdown
        def signal_handler(sig, frame):
            self.stdout.write(self.style.WARNING('\nStopping auto-scaler...'))
            scaler.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Run the loop
        try:
            scaler.run_loop(interval=interval)
        except KeyboardInterrupt:
            scaler.stop()
            self.stdout.write(self.style.SUCCESS('\nAuto-scaler stopped.'))
