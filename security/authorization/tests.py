"""
Tests for Authorization Service (AZ).

Tests: RBAC, object permissions, time-based access, RLS integration.
"""

from django.test import TestCase
from django.contrib.auth.models import User, Permission, Group
from django.utils import timezone
from datetime import timedelta

from security.authorization.services import (
    RBACService, TimeBasedAccessService, ObjectPermissionService,
    AuthorizationAuditService, RowLevelSecurityService,
)
from security.models import (
    Role, UserRoleAssignment, ObjectPermission,
    TimeBasedAccessPolicy, AuthorizationAuditLog, RowLevelSecurityPolicy,
)


# ═══════════════════════════════════════════════════════════════════════════════
# RBAC Service Tests
# ═══════════════════════════════════════════════════════════════════════════════

class RBACServiceTests(TestCase):
    """Tests for hierarchical Role-Based Access Control."""

    def setUp(self):
        self.user = User.objects.create_user('rbacuser', 'rbac@test.com', 'password123')
        self.admin_user = User.objects.create_user('adminuser', 'admin@test.com', 'password123')
        self.admin_user.is_superuser = True
        self.admin_user.save()

        # Create role hierarchy
        self.admin_role = RBACService.create_role(
            'admin', description='Admin role', is_system_role=True
        )
        self.editor_role = RBACService.create_role(
            'editor', parent=self.admin_role, description='Editor role', is_system_role=True
        )
        self.viewer_role = RBACService.create_role(
            'viewer', parent=self.editor_role, description='Viewer role', is_system_role=True
        )

    def test_create_role_with_permissions(self):
        """Should create role and assign permissions."""
        perm = Permission.objects.first()
        role = RBACService.create_role(
            'custom_role',
            permissions=[perm.codename],
        )
        self.assertEqual(role.name, 'custom_role')
        self.assertIn(perm, role.permissions.all())

    def test_role_hierarchy_three_levels(self):
        """Should support 3-level hierarchy: admin > editor > viewer."""
        self.assertIsNone(self.admin_role.parent)
        self.assertEqual(self.editor_role.parent, self.admin_role)
        self.assertEqual(self.viewer_role.parent, self.editor_role)

    def test_assign_role_to_user(self):
        """Should assign role to user."""
        RBACService.assign_role(self.user, self.editor_role)
        assignments = UserRoleAssignment.objects.filter(
            user=self.user, role=self.editor_role, is_active=True
        )
        self.assertTrue(assignments.exists())

    def test_get_user_roles(self):
        """Should return all active roles for user."""
        RBACService.assign_role(self.user, self.editor_role)
        roles = RBACService.get_user_roles(self.user)
        self.assertIn(self.editor_role, roles)

    def test_remove_role_from_user(self):
        """Should deactivate role assignment."""
        RBACService.assign_role(self.user, self.editor_role)
        RBACService.remove_role(self.user, self.editor_role)
        roles = RBACService.get_user_roles(self.user)
        self.assertNotIn(self.editor_role, roles)

    def test_superuser_has_all_permissions(self):
        """Superuser should have all permissions."""
        self.assertTrue(
            RBACService.check_permission(self.admin_user, 'any_permission')
        )

    def test_check_permission_unassigned_user(self):
        """Regular user should not have unassigned permission."""
        self.assertFalse(
            RBACService.check_permission(self.user, 'add_noticia')
        )

    def test_get_user_permissions_basic(self):
        """Should return permissions for user (may have Django defaults)."""
        perms = RBACService.get_user_permissions(self.user)
        # User might have some default Django permissions, just verify it's a set
        self.assertIsInstance(perms, set)

    def test_assign_role_with_expiry(self):
        """Should support role assignment with expiration."""
        expires = timezone.now() + timedelta(days=30)
        RBACService.assign_role(
            self.user, self.editor_role, expires_at=expires
        )
        assignment = UserRoleAssignment.objects.get(
            user=self.user, role=self.editor_role
        )
        self.assertIsNotNone(assignment.expires_at)


# ═══════════════════════════════════════════════════════════════════════════════
# Object Permission Tests
# ═══════════════════════════════════════════════════════════════════════════════

class ObjectPermissionServiceTests(TestCase):
    """Tests for object-level permissions."""

    def setUp(self):
        self.user = User.objects.create_user('objuser', 'obj@test.com', 'password123')
        # Create a simple model instance for testing object permissions
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.auth.models import Permission

    def test_assign_and_check_object_permission(self):
        """Should assign object-level permission."""
        # We can test with the User model as the object
        perm = Permission.objects.get(codename='change_user')
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(User)

        ObjectPermissionService.assign_object_permission(
            self.user, 'change_user', self.user
        )
        obj_perm = ObjectPermission.objects.filter(
            user=self.user,
            permission=perm,
            content_type=ct,
            object_id=self.user.pk,
        )
        self.assertTrue(obj_perm.exists())

    def test_remove_object_permission(self):
        """Should remove object-level permission."""
        ObjectPermissionService.assign_object_permission(
            self.user, 'change_user', self.user
        )
        ObjectPermissionService.remove_object_permission(
            self.user, 'change_user', self.user
        )
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(User)
        obj_perm = ObjectPermission.objects.filter(
            user=self.user,
            permission__codename='change_user',
            content_type=ct,
            object_id=self.user.pk,
        )
        self.assertFalse(obj_perm.exists())


# ═══════════════════════════════════════════════════════════════════════════════
# Time-Based Access Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TimeBasedAccessServiceTests(TestCase):
    """Tests for time-based access policies."""

    def setUp(self):
        self.user = User.objects.create_user('timeuser', 'time@test.com', 'password123')
        self.role = Role.objects.create(name='test_role')

    def test_create_time_policy(self):
        """Should create time-based access policy."""
        policy = TimeBasedAccessService.create_policy(
            name='Business Hours',
            start_hour=8,
            end_hour=18,
            allowed_days=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
            roles=[self.role],
        )
        self.assertEqual(policy.name, 'Business Hours')
        self.assertEqual(policy.start_hour, 8)
        self.assertEqual(policy.end_hour, 18)
        self.assertIn(self.role, policy.roles.all())

    def test_is_access_allowed_with_default_policy(self):
        """Default policy should allow access during business hours."""
        policy = TimeBasedAccessPolicy.objects.create(
            name='Always Open',
            start_hour=0,
            end_hour=24,
            allowed_days=['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                          'Friday', 'Saturday', 'Sunday'],
        )
        allowed = TimeBasedAccessService.is_access_allowed(self.user, policy)
        self.assertTrue(allowed)


# ═══════════════════════════════════════════════════════════════════════════════
# Authorization Audit Tests
# ═══════════════════════════════════════════════════════════════════════════════

class AuthorizationAuditServiceTests(TestCase):
    """Tests for authorization audit logging."""

    def setUp(self):
        self.user = User.objects.create_user('audituser', 'audit@test.com', 'password123')

    def test_log_granted_decision(self):
        """Should log granted authorization decisions."""
        AuthorizationAuditService.log_decision(
            self.user, 'blog.noticia', 'view', granted=True
        )
        log = AuthorizationAuditLog.objects.filter(
            user=self.user, resource_type='blog.noticia'
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.outcome, 'granted')

    def test_log_denied_decision(self):
        """Should log denied decisions and create SecurityAuditLog."""
        AuthorizationAuditService.log_decision(
            self.user, 'course_documents.coursedocument', 'delete',
            granted=False, reason='access_denied'
        )
        log = AuthorizationAuditLog.objects.filter(
            user=self.user, outcome='denied'
        ).first()
        self.assertIsNotNone(log)

    def test_log_denied_creates_security_audit(self):
        """Denied access should also create a SecurityAuditLog entry."""
        AuthorizationAuditService.log_decision(
            self.user, 'course_documents.coursedocument', 'delete',
            granted=False, reason='access_denied'
        )
        from security.models import SecurityAuditLog
        sec_log = SecurityAuditLog.objects.filter(
            event_type=SecurityAuditLog.EventTypes.AUTHORIZATION,
            action='access_denied_delete',
        ).first()
        self.assertIsNotNone(sec_log)
        self.assertFalse(sec_log.success)


# ═══════════════════════════════════════════════════════════════════════════════
# Row-Level Security Service Tests
# ═══════════════════════════════════════════════════════════════════════════════

class RowLevelSecurityServiceTests(TestCase):
    """Tests for RLS service integration."""

    def setUp(self):
        self.user = User.objects.create_user('rlsuser', 'rls@test.com', 'password123')
        self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'password123')

    def test_clear_rls_context(self):
        """Should clear RLS context without error."""
        try:
            RowLevelSecurityService.clear_rls_context()
        except Exception as e:
            self.fail(f'clear_rls_context raised {e}')

    def test_set_rls_context_authenticated(self):
        """Should set RLS context for authenticated user."""
        try:
            RowLevelSecurityService.set_rls_context(self.user)
        except Exception as e:
            self.fail(f'set_rls_context raised {e}')

    def test_set_rls_context_superuser(self):
        """Should set RLS context with superuser role."""
        try:
            RowLevelSecurityService.set_rls_context(self.admin)
        except Exception as e:
            self.fail(f'set_rls_context raised {e}')

    def test_set_rls_context_anonymous(self):
        """Should set RLS context for anonymous users."""
        try:
            RowLevelSecurityService.set_rls_context(None)
        except Exception as e:
            self.fail(f'set_rls_context raised {e}')

    def test_create_selective_policy(self):
        """Should create RLS policy record."""
        policy = RowLevelSecurityService.create_selective_permission_policy(
            table_name='test_table',
            policy_name='test_policy',
            using_expression='true',
            roles=['authenticated'],
        )
        self.assertEqual(policy.table_name, 'test_table')
        self.assertEqual(policy.policy_type, 'select')
