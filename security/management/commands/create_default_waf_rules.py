"""
Command to create default WAF rules.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from security.models import WAFRule


class Command(BaseCommand):
    help = 'Create default WAF rules for security system'

    def handle(self, *args, **options):
        # Get or create admin user for created_by field
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={'is_staff': True, 'is_superuser': True}
        )

        default_rules = [
            {
                'name': 'SQL Injection - Basic',
                'category': WAFRule.Categories.SQL_INJECTION,
                'pattern': r'(?i)(union.*select|select.*from|insert.*into|update.*set|delete.*from|drop.*table|create.*table|alter.*table)',
                'description': 'Detects basic SQL injection patterns',
                'severity': 'critical',
                'is_active': True,
            },
            {
                'name': 'XSS - Script Tags',
                'category': WAFRule.Categories.XSS,
                'pattern': r'(?i)(<script.*?>.*?</script>|<script[^>]*>|javascript:|onload=|onerror=|onclick=)',
                'description': 'Detects XSS via script tags and event handlers',
                'severity': 'high',
                'is_active': True,
            },
            {
                'name': 'Path Traversal - Basic',
                'category': WAFRule.Categories.PATH_TRAVERSAL,
                'pattern': r'(\.\./|\.\.\\|/etc/passwd|/etc/shadow|C:\\Windows\\|\.\.%2f|\.\.%5c)',
                'description': 'Detects path traversal attempts',
                'severity': 'high',
                'is_active': True,
            },
            {
                'name': 'Command Injection - Basic',
                'category': WAFRule.Categories.COMMAND_INJECTION,
                'pattern': r'(?i)(\|\||&&|;|`|\$\(|\$\{|\n|\r|cat.*etc.*passwd|ls.*-la|netstat.*-an|whoami|id|pwd)',
                'description': 'Detects command injection attempts',
                'severity': 'critical',
                'is_active': True,
            },
            {
                'name': 'CSRF Token Missing',
                'category': WAFRule.Categories.CSRF,
                'pattern': r'',
                'description': 'CSRF protection middleware - not a regex pattern',
                'severity': 'medium',
                'is_active': True,
            },
            {
                'name': 'Sensitive Data Exposure',
                'category': WAFRule.Categories.CUSTOM,
                'pattern': r'(?i)(password|secret|key|token|api[_-]?key|auth[_-]?token|jwt|bearer)\s*[:=]\s*[\w\.\-_]+',
                'description': 'Detects potential sensitive data in requests',
                'severity': 'high',
                'is_active': True,
            },
        ]

        created_count = 0
        updated_count = 0

        for rule_data in default_rules:
            # Skip if pattern is empty (like for CSRF which is handled by middleware)
            if rule_data['pattern'] == '':
                continue
                
            rule, created = WAFRule.objects.update_or_create(
                name=rule_data['name'],
                defaults={
                    'category': rule_data['category'],
                    'pattern': rule_data['pattern'],
                    'description': rule_data['description'],
                    'severity': rule_data['severity'],
                    'is_active': rule_data['is_active'],
                    'created_by': admin_user,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created rule: {rule.name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'Updated rule: {rule.name}'))

        self.stdout.write(self.style.SUCCESS(
            f'WAF rules created/updated: {created_count} created, {updated_count} updated'
        ))