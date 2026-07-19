# Generated migration to create default WAF rules

from django.db import migrations
from django.contrib.auth import get_user_model


def create_default_waf_rules(apps, schema_editor):
    """
    Crea las reglas WAF por defecto si no existen.
    Esta función se ejecuta automáticamente al hacer migrate.
    """
    WAFRule = apps.get_model('security', 'WAFRule')
    User = get_user_model()
    
    # Get or create admin user for created_by field
    try:
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            # If no superuser exists, we'll set created_by to None
            admin_user = None
    except Exception:
        admin_user = None

    # Define default WAF rules
    default_rules = [
        {
            'name': 'SQL Injection - Basic',
            'category': 'sql_injection',
            'pattern': r'(?i)(union.*select|select.*from|insert.*into|update.*set|delete.*from|drop.*table|create.*table|alter.*table)',
            'description': 'Detects basic SQL injection patterns',
            'severity': 'critical',
            'is_active': True,
        },
        {
            'name': 'XSS - Script Tags',
            'category': 'xss',
            'pattern': r'(?i)(<script.*?>.*?</script>|<script[^>]*>|javascript:|onload=|onerror=|onclick=)',
            'description': 'Detects XSS via script tags and event handlers',
            'severity': 'high',
            'is_active': True,
        },
        {
            'name': 'Path Traversal - Basic',
            'category': 'path_traversal',
            'pattern': r'(\.\./|\.\.\\|/etc/passwd|/etc/shadow|C:\\Windows\\|\.\.%2f|\.\.%5c)',
            'description': 'Detects path traversal attempts',
            'severity': 'high',
            'is_active': True,
        },
        {
            'name': 'Command Injection - Basic',
            'category': 'command_injection',
            'pattern': r'(?i)(\|\||&&|;|`|\$\(|\$\{|\n|\r|cat.*etc.*passwd|ls.*-la|netstat.*-an|whoami|id|pwd)',
            'description': 'Detects command injection attempts',
            'severity': 'critical',
            'is_active': True,
        },
        {
            'name': 'Sensitive Data Exposure',
            'category': 'custom',
            'pattern': r'(?i)(password|secret|key|token|api[_-]?key|auth[_-]?token|jwt|bearer)\s*[:=]\s*[\w\.\-_]+',
            'description': 'Detects potential sensitive data in requests',
            'severity': 'high',
            'is_active': True,
        },
    ]

    # Create rules if they don't exist
    created_count = 0
    for rule_data in default_rules:
        # Check if rule already exists by name
        if not WAFRule.objects.filter(name=rule_data['name']).exists():
            WAFRule.objects.create(
                name=rule_data['name'],
                category=rule_data['category'],
                pattern=rule_data['pattern'],
                description=rule_data['description'],
                severity=rule_data['severity'],
                is_active=rule_data['is_active'],
                created_by=admin_user,
            )
            created_count += 1
    
    print(f'✅ Created {created_count} default WAF rules')


def reverse_func(apps, schema_editor):
    """
    Elimina las reglas WAF por defecto al revertir la migración.
    """
    WAFRule = apps.get_model('security', 'WAFRule')
    
    default_rule_names = [
        'SQL Injection - Basic',
        'XSS - Script Tags',
        'Path Traversal - Basic',
        'Command Injection - Basic',
        'Sensitive Data Exposure',
    ]
    
    deleted_count = WAFRule.objects.filter(name__in=default_rule_names).delete()[0]
    print(f'🗑️ Deleted {deleted_count} default WAF rules')


class Migration(migrations.Migration):

    dependencies = [
        ('security', '0002_enable_pgcrypto_rls'),
    ]

    operations = [
        migrations.RunPython(create_default_waf_rules, reverse_func),
    ]
