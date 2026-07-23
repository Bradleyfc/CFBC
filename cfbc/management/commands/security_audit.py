"""
Management command to perform a security audit of the CFBC application.

Scans the Django configuration and deployment for common security issues:
- Debug mode enabled in production
- Insecure secret key
- Missing security headers
- Weak password policies
- CSRF configuration
- Session security
- HTTPS configuration
- File upload security
- Database exposure

Usage:
    # Run full security audit
    python manage.py security_audit

    # Run specific checks only
    python manage.py security_audit --checks settings,headers,database

    # Output in JSON format
    python manage.py security_audit --format json

    # Output report to file
    python manage.py security_audit --output security_report.txt
"""

import json
import logging
import os
import socket
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connection

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Perform a comprehensive security audit of the application'

    SEVERITY_COLORS = {
        'critical': '\033[91m',   # Red
        'warning': '\033[93m',    # Yellow
        'info': '\033[94m',       # Blue
        'pass': '\033[92m',       # Green
        'reset': '\033[0m',       # Reset
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--checks', '-c',
            type=str,
            default='all',
            help='Comma-separated list of checks: settings,headers,database,session,deployment'
        )
        parser.add_argument(
            '--format', '-f',
            type=str,
            choices=['text', 'json'],
            default='text',
            help='Output format (default: text)'
        )
        parser.add_argument(
            '--output', '-o',
            type=str,
            default=None,
            help='Write report to file'
        )

    def handle(self, *args, **options):
        self.output_format = options['format']
        self.output_file = options['output']
        checks = options['checks']

        if checks != 'all':
            self.active_checks = set(c.strip() for c in checks.split(','))
        else:
            self.active_checks = {'settings', 'headers', 'database', 'session', 'deployment'}

        self.stdout.write(self.style.MIGRATE_HEADING(
            "\n🔒 CFBC Security Audit\n" + "=" * 60
        ))
        self.stdout.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        results = {
            'timestamp': datetime.now().isoformat(),
            'hostname': socket.gethostname(),
            'django_version': self._get_django_version(),
            'python_version': os.sys.version,
            'checks': {},
            'summary': {'total': 0, 'passed': 0, 'warnings': 0, 'critical': 0},
        }

        # Run selected checks
        if 'settings' in self.active_checks:
            results['checks']['settings'] = self._check_settings()
        if 'headers' in self.active_checks:
            results['checks']['headers'] = self._check_headers()
        if 'database' in self.active_checks:
            results['checks']['database'] = self._check_database()
        if 'session' in self.active_checks:
            results['checks']['session'] = self._check_session()
        if 'deployment' in self.active_checks:
            results['checks']['deployment'] = self._check_deployment()

        # Compile summary
        all_findings = []
        for check_name, check_results in results['checks'].items():
            if isinstance(check_results, dict) and 'findings' in check_results:
                all_findings.extend(check_results['findings'])

        results['summary'] = {
            'total': len(all_findings),
            'passed': sum(1 for f in all_findings if f['status'] == 'pass'),
            'warnings': sum(1 for f in all_findings if f['status'] == 'warning'),
            'critical': sum(1 for f in all_findings if f['status'] == 'critical'),
        }

        # Output results
        if self.output_format == 'json':
            output = json.dumps(results, indent=2, default=str)
        else:
            output = self._format_text_output(results)

        if self.output_file:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(output)
            self.stdout.write(self.style.SUCCESS(
                f"\nReport saved to: {self.output_file}"
            ))
        else:
            self.stdout.write(output)

    def _get_django_version(self):
        """Get Django version."""
        try:
            import django
            return django.VERSION
        except ImportError:
            return 'unknown'

    # ── Settings Checks ──────────────────────────────────────────────────

    def _check_settings(self):
        """Check Django settings for security issues."""
        findings = []

        # DEBUG mode
        findings.append(self._check(
            'DEBUG Mode',
            not settings.DEBUG,
            'critical',
            'DEBUG=True in production exposes sensitive information',
            'Set DEBUG=False in production. Use environment variables.',
            f"DEBUG={settings.DEBUG}"
        ))

        # SECRET_KEY
        has_secret = settings.SECRET_KEY is not None and len(settings.SECRET_KEY) > 32
        findings.append(self._check(
            'Secret Key Strength',
            has_secret,
            'critical',
            'SECRET_KEY is too short or using default value',
            'Generate a strong random SECRET_KEY via environment variable.',
            f"Length: {len(settings.SECRET_KEY) if settings.SECRET_KEY else 0}"
        ))

        # ALLOWED_HOSTS
        has_allowed_hosts = len(settings.ALLOWED_HOSTS) > 0 and (
            '*' not in settings.ALLOWED_HOSTS
        )
        findings.append(self._check(
            'ALLOWED_HOSTS',
            has_allowed_hosts,
            'critical',
            'ALLOWED_HOSTS is empty or contains wildcard (*)',
            'Set specific allowed hostnames.',
            f"Hosts: {settings.ALLOWED_HOSTS}"
        ))

        # CSRF configuration
        csrf_middleware = any(
            'csrf' in m.lower() for m in settings.MIDDLEWARE
        )
        findings.append(self._check(
            'CSRF Protection',
            csrf_middleware,
            'critical',
            'CSRF middleware is missing',
            'Add django.middleware.csrf.CsrfViewMiddleware to MIDDLEWARE',
            f"CSRF middleware: {'present' if csrf_middleware else 'MISSING'}"
        ))

        # Password validators
        has_password_validators = len(settings.AUTH_PASSWORD_VALIDATORS) > 0
        findings.append(self._check(
            'Password Validators',
            has_password_validators,
            'warning',
            'No password validators configured',
            'Add at least minimum length and common password validators.',
            f"Validators: {len(settings.AUTH_PASSWORD_VALIDATORS)}"
        ))

        return {'findings': findings}

    # ── Headers Checks ──────────────────────────────────────────────────

    def _check_headers(self):
        """Check security headers configuration."""
        findings = []
        middleware = settings.MIDDLEWARE

        # SecurityHeadersMiddleware
        has_security_headers = any(
            'SecurityHeaders' in m for m in middleware
        )
        findings.append(self._check(
            'SecurityHeadersMiddleware',
            has_security_headers,
            'critical',
            'SecurityHeadersMiddleware is not installed',
            'Add cfbc.middleware.SecurityHeadersMiddleware to MIDDLEWARE',
            f"Present: {has_security_headers}"
        ))

        # SecurityMiddleware
        has_security_middleware = any(
            'django.middleware.security.SecurityMiddleware' in m for m in middleware
        )
        findings.append(self._check(
            'Django SecurityMiddleware',
            has_security_middleware,
            'critical',
            'Django SecurityMiddleware is not installed',
            'Keep django.middleware.security.SecurityMiddleware in MIDDLEWARE',
            f"Present: {has_security_middleware}"
        ))

        # Rate limiting
        has_rate_limiting = any(
            'RateLimit' in m for m in middleware
        )
        findings.append(self._check(
            'Rate Limit Middleware',
            has_rate_limiting,
            'warning',
            'RateLimitMiddleware is not installed',
            'Add cfbc.middleware.RateLimitMiddleware to prevent brute force',
            f"Present: {has_rate_limiting}"
        ))

        return {'findings': findings}

    # ── Database Checks ─────────────────────────────────────────────────

    def _check_database(self):
        """Check database configuration for security issues."""
        findings = []

        # Check if using PostgreSQL (recommended)
        db_engine = settings.DATABASES.get('default', {}).get('ENGINE', '')
        using_postgres = 'postgresql' in db_engine
        findings.append(self._check(
            'Database Engine',
            using_postgres,
            'warning' if not using_postgres else 'pass',
            'Not using PostgreSQL - SQLite is not suitable for production',
            'Configure PostgreSQL in production.',
            f"Engine: {db_engine}"
        ))

        # Connection timeout
        connect_timeout = settings.DATABASES.get('default', {}).get(
            'OPTIONS', {}
        ).get('connect_timeout', 0)
        has_timeout = connect_timeout > 0
        findings.append(self._check(
            'Connection Timeout',
            has_timeout,
            'warning',
            'Database connection timeout not configured',
            'Set connect_timeout in database OPTIONS.',
            f"Timeout: {connect_timeout}s"
        ))

        # Connection health checks
        has_health_checks = settings.DATABASES.get('default', {}).get(
            'CONN_HEALTH_CHECKS', False
        )
        findings.append(self._check(
            'Connection Health Checks',
            has_health_checks,
            'info',
            '',
            '',
            f"Health checks: {has_health_checks}"
        ))

        return {'findings': findings}

    # ── Session Checks ──────────────────────────────────────────────────

    def _check_session(self):
        """Check session security configuration."""
        findings = []

        # Session engine
        session_engine = getattr(settings, 'SESSION_ENGINE', '')
        using_cache = 'cache' in session_engine
        findings.append(self._check(
            'Session Engine',
            using_cache,
            'info' if using_cache else 'warning',
            'Session engine should use cache (Redis) for scalability',
            'Set SESSION_ENGINE to use cache backend.',
            f"Engine: {session_engine}"
        ))

        # Session cookie age
        cookie_age = getattr(settings, 'SESSION_COOKIE_AGE', 0)
        findings.append(self._check(
            'Session Cookie Age',
            cookie_age <= 1209600,  # 2 weeks max
            'info',
            '',
            '',
            f"Age: {cookie_age}s ({cookie_age / 86400:.0f} days)"
        ))

        # Secure cookie in production
        secure_cookie = getattr(settings, 'SESSION_COOKIE_SECURE', False)
        http_only = getattr(settings, 'SESSION_COOKIE_HTTPONLY', True)
        findings.append(self._check(
            'Secure Cookies',
            secure_cookie or getattr(settings, 'SESSION_COOKIE_SECURE', False),
            'info',
            '',
            'Set SESSION_COOKIE_SECURE=True and SESSION_COOKIE_HTTPONLY=True',
            f"Secure: {secure_cookie}, HttpOnly: {http_only}"
        ))

        return {'findings': findings}

    # ── Deployment Checks ──────────────────────────────────────────────

    def _check_deployment(self):
        """Check deployment configuration."""
        findings = []

        # Secure proxy SSL header
        has_ssl_header = getattr(settings, 'SECURE_PROXY_SSL_HEADER', None) is not None
        behind_lb = getattr(settings, 'BEHIND_LOAD_BALANCER', False)
        findings.append(self._check(
            'HTTPS Behind Proxy',
            has_ssl_header if behind_lb else True,
            'warning' if behind_lb else 'pass',
            'SECURE_PROXY_SSL_HEADER not configured for load balancer',
            'Configure SECURE_PROXY_SSL_HEADER when behind a proxy.',
            f"Configured: {has_ssl_header}, Behind LB: {behind_lb}"
        ))

        # File upload size limits
        max_upload = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 0)
        max_data = getattr(settings, 'DATA_UPLOAD_MAX_MEMORY_SIZE', 0)
        findings.append(self._check(
            'Upload Size Limits',
            max_upload <= 26214400,  # 25MB max recommended
            'info',
            '',
            '',
            f"Upload: {max_upload / 1024 / 1024:.0f}MB, "
            f"Data: {max_data / 1024 / 1024:.0f}MB"
        ))

        return {'findings': findings}

    # ── Helpers ─────────────────────────────────────────────────────────

    def _check(self, name, passed, severity_if_fail, fail_message,
              recommendation='', current_value=''):
        """Create a check result entry."""
        if passed:
            return {
                'name': name,
                'status': 'pass',
                'message': f"{name}: ✅ OK",
                'current': current_value,
            }
        else:
            return {
                'name': name,
                'status': severity_if_fail,
                'message': f"{name}: ❌ {fail_message}",
                'recommendation': recommendation,
                'current': current_value,
            }

    def _format_text_output(self, results):
        """Format results as colored text."""
        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(f"  SECURITY AUDIT REPORT")
        lines.append(f"{'='*60}")
        lines.append(f"  Host:     {results['hostname']}")
        lines.append(f"  Django:   {'.'.join(map(str, results['django_version']))}")
        lines.append(f"  Python:   {results['python_version'].split()[0]}")
        lines.append(f"  Time:     {results['timestamp']}")
        lines.append(f"{'='*60}")

        for check_name, check_data in results['checks'].items():
            if not isinstance(check_data, dict) or 'findings' not in check_data:
                continue

            lines.append(f"\n  📋 {check_name.upper()} CHECKS")
            lines.append(f"  {'─'*56}")

            for finding in check_data['findings']:
                status = finding.get('status', 'info')
                color = self.SEVERITY_COLORS.get(status, '')
                reset = self.SEVERITY_COLORS['reset']
                icon = {'pass': '✅', 'warning': '⚠️', 'critical': '❌', 'info': 'ℹ️'}.get(status, '')

                lines.append(
                    f"    {color}{icon} {finding.get('message', '')}{reset}"
                )
                if finding.get('recommendation'):
                    lines.append(
                        f"       💡 {finding['recommendation']}"
                    )
                if finding.get('current'):
                    lines.append(
                        f"       Current: {finding['current']}"
                    )

        # Summary
        summary = results['summary']
        lines.append(f"\n{'='*60}")
        lines.append(f"  SUMMARY: {summary['total']} checks")
        lines.append(f"    ✅ {summary['passed']} passed")
        if summary['warnings']:
            lines.append(f"    ⚠️  {summary['warnings']} warnings")
        if summary['critical']:
            lines.append(f"    ❌ {summary['critical']} critical issues")
        lines.append(f"{'='*60}\n")

        return '\n'.join(lines)
