"""
Comprehensive security app tests.

Tests models, signals, and basic functionality of all security modules.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import time

from security.models import (
    UserSecurityProfile, SecurityAuditLog, RowLevelSecurityPolicy,
    EncryptedDataKey, Role, UserRoleAssignment, ObjectPermission,
    TimeBasedAccessPolicy, AuthorizationAuditLog, APIKey,
    JWTSession, WAFRule, SecurityReport, ComplianceCheck,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Models Tests
# ═══════════════════════════════════════════════════════════════════════════════

class UserSecurityProfileModelTests(TestCase):
    """Tests for UserSecurityProfile model."""

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@test.com', 'password123')

    def test_profile_created_on_user_creation(self):
        """Profile should be auto-created via signal."""
        self.assertTrue(hasattr(self.user, 'security_profile'))
        self.assertIsNotNone(self.user.security_profile)

    def test_default_values(self):
        """Profile should have correct defaults."""
        profile = self.user.security_profile
        self.assertFalse(profile.two_factor_enabled)
        self.assertEqual(profile.max_concurrent_sessions, 3)
        self.assertEqual(profile.failed_login_attempts, 0)
        self.assertIsNone(profile.account_locked_until)

    def test_record_failed_login_locks_account(self):
        """5 failed attempts should lock account for 30 min."""
        profile = self.user.security_profile
        for i in range(5):
            profile.record_failed_login()
        self.assertTrue(profile.is_account_locked)
        self.assertIsNotNone(profile.account_locked_until)

    def test_record_successful_login_resets_counter(self):
        """Successful login should reset failed attempts."""
        profile = self.user.security_profile
        profile.record_failed_login()
        profile.record_failed_login()
        self.assertEqual(profile.failed_login_attempts, 2)
        profile.record_successful_login()
        self.assertEqual(profile.failed_login_attempts, 0)

    def test_account_auto_unlock_after_time(self):
        """Account should unlock automatically after lockout period."""
        profile = self.user.security_profile
        profile.account_locked_until = timezone.now() - timedelta(minutes=31)
        profile.save()
        self.assertFalse(profile.is_account_locked)

    def test_str_representation(self):
        """String representation should include username."""
        self.assertIn('testuser', str(self.user.security_profile))


class SecurityAuditLogModelTests(TestCase):
    """Tests for SecurityAuditLog model."""

    def setUp(self):
        self.user = User.objects.create_user('audituser', 'audit@test.com', 'password123')

    def test_create_audit_log(self):
        """Should create audit log with all fields."""
        log = SecurityAuditLog.objects.create(
            event_type=SecurityAuditLog.EventTypes.AUTH,
            user=self.user,
            action='login',
            resource='authentication',
            success=True,
        )
        self.assertEqual(log.event_type, 'auth')
        self.assertEqual(log.action, 'login')
        self.assertTrue(log.success)
        self.assertIsNotNone(log.event_id)
        self.assertIsNotNone(log.timestamp)

    def test_audit_log_default_severity(self):
        """Default severity should be INFO."""
        log = SecurityAuditLog.objects.create(
            event_type=SecurityAuditLog.EventTypes.AUTH,
            action='test',
        )
        self.assertEqual(log.severity, SecurityAuditLog.SeverityLevels.INFO)

    def test_audit_log_ordering(self):
        """Logs should be ordered by timestamp descending."""
        log1 = SecurityAuditLog.objects.create(
            event_type=SecurityAuditLog.EventTypes.AUTH, action='first'
        )
        log2 = SecurityAuditLog.objects.create(
            event_type=SecurityAuditLog.EventTypes.AUTH, action='second'
        )
        logs = SecurityAuditLog.objects.all()
        self.assertEqual(logs[0].action, 'second')
        self.assertEqual(logs[1].action, 'first')


class RoleModelTests(TestCase):
    """Tests for Role model."""

    def setUp(self):
        self.admin_role = Role.objects.create(name='admin', is_system_role=True)
        self.editor_role = Role.objects.create(
            name='editor', parent=self.admin_role, is_system_role=True
        )

    def test_role_hierarchy(self):
        """Roles should support parent-child hierarchy."""
        self.assertEqual(self.editor_role.parent, self.admin_role)
        self.assertIn(self.editor_role, self.admin_role.children.all())

    def test_inherited_permissions_empty(self):
        """Should return empty set when no permissions exist."""
        perms = self.editor_role.get_inherited_permissions()
        self.assertEqual(len(perms), 0)

    def test_str_representation(self):
        """String representation should be role name."""
        self.assertEqual(str(self.admin_role), 'admin')


class APIKeyModelTests(TestCase):
    """Tests for APIKey model."""

    def setUp(self):
        self.user = User.objects.create_user('apiuser', 'api@test.com', 'password123')

    def _create_api_key(self, key_str, prefix, name, **kwargs):
        """Helper to create API keys with proper length."""
        return APIKey.objects.create(
            user=self.user,
            key=key_str[:64].ljust(64, 'x'),
            key_prefix=prefix[:8].ljust(8, 'x'),
            name=name,
            expires_at=kwargs.pop('expires_at', timezone.now() + timedelta(days=90)),
            daily_limit=kwargs.pop('daily_limit', 10000),
            daily_used=kwargs.pop('daily_used', 0),
        )

    def test_create_api_key(self):
        """Should create API key with defaults."""
        key = self._create_api_key('testkey1', 'testkey1', 'Test Key')
        self.assertEqual(key.daily_limit, 10000)
        self.assertTrue(key.is_active)
        self.assertFalse(key.is_expired())

    def test_api_key_expiry(self):
        """Expired key should report as expired."""
        key = self._create_api_key(
            'expired', 'expired', 'Expired Key',
            expires_at=timezone.now() - timedelta(days=1),
        )
        self.assertTrue(key.is_expired())

    def test_daily_limit_exceeded(self):
        """Should detect when daily limit is exceeded."""
        key = self._create_api_key(
            'limited', 'limited', 'Limited Key',
            daily_limit=5, daily_used=5,
        )
        self.assertTrue(key.is_daily_limit_exceeded())

    def test_daily_limit_not_exceeded(self):
        """Should allow requests within daily limit."""
        key = self._create_api_key(
            'okaykey', 'okaykey', 'OK Key',
            daily_limit=100, daily_used=50,
        )
        self.assertFalse(key.is_daily_limit_exceeded())


class WAFRuleModelTests(TestCase):
    """Tests for WAFRule model."""

    def test_create_waf_rule(self):
        """Should create WAF rule with category and pattern."""
        rule = WAFRule.objects.create(
            name='Test SQL Injection',
            category=WAFRule.Categories.SQL_INJECTION,
            pattern=r"(\'|\"|;|--)",
            severity='critical',
        )
        self.assertTrue(rule.is_active)
        self.assertEqual(rule.hit_count, 0)
        self.assertIsNone(rule.last_hit)

    def test_str_representation(self):
        """String should include name and category."""
        rule = WAFRule.objects.create(
            name='Test XSS Rule',
            category=WAFRule.Categories.XSS,
            pattern=r'(<script|<iframe)',
        )
        self.assertIn('Test XSS Rule', str(rule))
        self.assertIn('XSS', str(rule))


# ═══════════════════════════════════════════════════════════════════════════════
# RLS Policy Tests
# ═══════════════════════════════════════════════════════════════════════════════

class RowLevelSecurityPolicyModelTests(TestCase):
    """Tests for RowLevelSecurityPolicy model."""

    def setUp(self):
        self.user = User.objects.create_user('rlstest', 'rls@test.com', 'password123')

    def test_create_rls_policy(self):
        """Should create RLS policy with SQL expressions."""
        policy = RowLevelSecurityPolicy.objects.create(
            table_name='accounts_registro',
            policy_name='user_own_data',
            policy_type=RowLevelSecurityPolicy.PolicyTypes.SELECT,
            using_expression='user_id = current_setting(''rls.user_id'')::int',
            roles=['authenticated'],
            created_by=self.user,
        )
        self.assertTrue(policy.is_active)
        self.assertEqual(policy.version, 1)
        self.assertIn('user_id', policy.using_expression)

    def test_str_representation(self):
        """String should include policy name and table."""
        policy = RowLevelSecurityPolicy.objects.create(
            table_name='blog_noticia',
            policy_name='blog_visibility',
            policy_type=RowLevelSecurityPolicy.PolicyTypes.SELECT,
            using_expression='estado = ''publicado''',
        )
        self.assertIn('blog_visibility', str(policy))
        self.assertIn('blog_noticia', str(policy))


class AuthorizationAuditLogModelTests(TestCase):
    """Tests for AuthorizationAuditLog model."""

    def setUp(self):
        self.user = User.objects.create_user('authzaudit', 'authz@test.com', 'password123')

    def test_log_granted_decision(self):
        """Should log granted authorization decisions."""
        log = AuthorizationAuditLog.objects.create(
            user=self.user,
            resource_type='blog.noticia',
            action='view',
            outcome='granted',
        )
        self.assertEqual(log.outcome, 'granted')
        self.assertIsNotNone(log.timestamp)

    def test_log_denied_decision(self):
        """Should log denied authorization decisions."""
        log = AuthorizationAuditLog.objects.create(
            user=self.user,
            resource_type='course_documents.coursedocument',
            action='delete',
            outcome='denied',
            reason='access_denied',
        )
        self.assertEqual(log.outcome, 'denied')
        self.assertEqual(log.reason, 'access_denied')


# ═══════════════════════════════════════════════════════════════════════════════
# Signal Tests
# ═══════════════════════════════════════════════════════════════════════════════

class SecuritySignalTests(TestCase):
    """Tests for security signals."""

    def test_profile_created_on_user_creation(self):
        """Signal should create UserSecurityProfile for new users."""
        user = User.objects.create_user('signaltest', 'signal@test.com', 'password123')
        self.assertTrue(
            UserSecurityProfile.objects.filter(user=user).exists()
        )
