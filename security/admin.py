"""
Admin configuration for security app.
"""

from django.contrib import admin
from .models import (
    UserSecurityProfile, SecurityAuditLog, RowLevelSecurityPolicy,
    EncryptedDataKey, Role, UserRoleAssignment, ObjectPermission,
    TimeBasedAccessPolicy, AuthorizationAuditLog, APIKey,
    JWTSession, WAFRule, SecurityReport, ComplianceCheck,
)


@admin.register(UserSecurityProfile)
class UserSecurityProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'two_factor_enabled', 'failed_login_attempts',
                    'account_locked_until', 'max_concurrent_sessions']
    list_filter = ['two_factor_enabled']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['totp_secret', 'backup_codes']


@admin.register(SecurityAuditLog)
class SecurityAuditLogAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'action', 'user', 'severity',
                    'success', 'timestamp']
    list_filter = ['event_type', 'severity', 'success', 'timestamp']
    search_fields = ['action', 'user__username', 'ip_address']
    readonly_fields = ['event_id', 'timestamp']
    date_hierarchy = 'timestamp'


@admin.register(RowLevelSecurityPolicy)
class RowLevelSecurityPolicyAdmin(admin.ModelAdmin):
    list_display = ['policy_name', 'table_name', 'policy_type', 'is_active', 'version']
    list_filter = ['policy_type', 'is_active', 'table_name']
    search_fields = ['policy_name', 'table_name']


@admin.register(EncryptedDataKey)
class EncryptedDataKeyAdmin(admin.ModelAdmin):
    list_display = ['key_type', 'algorithm', 'key_version', 'is_active',
                    'last_rotated', 'usage_count']
    list_filter = ['key_type', 'algorithm', 'is_active']
    readonly_fields = ['key_id', 'encrypted_key', 'usage_count', 'last_used']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_system_role', 'scope']
    list_filter = ['is_system_role']
    search_fields = ['name', 'description']
    filter_horizontal = ['permissions']


@admin.register(UserRoleAssignment)
class UserRoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'assigned_at', 'expires_at', 'is_active']
    list_filter = ['is_active', 'role']
    search_fields = ['user__username', 'role__name']


@admin.register(ObjectPermission)
class ObjectPermissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'permission', 'content_type', 'object_id',
                    'granted_at', 'expires_at']
    list_filter = ['content_type']
    search_fields = ['user__username', 'permission__codename']


@admin.register(TimeBasedAccessPolicy)
class TimeBasedAccessPolicyAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_hour', 'end_hour', 'is_active', 'timezone']
    list_filter = ['is_active', 'allowed_days']
    search_fields = ['name', 'description']
    filter_horizontal = ['roles']


@admin.register(AuthorizationAuditLog)
class AuthorizationAuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'resource_type', 'action', 'outcome', 'timestamp']
    list_filter = ['outcome', 'resource_type', 'timestamp']
    search_fields = ['user__username', 'resource_type', 'action']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'key_prefix', 'is_active',
                    'expires_at', 'daily_used', 'daily_limit']
    list_filter = ['is_active']
    search_fields = ['name', 'user__username', 'key']


@admin.register(JWTSession)
class JWTSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'jti', 'is_active', 'access_token_created',
                    'access_token_expires', 'rotated_at']
    list_filter = ['is_active']
    search_fields = ['user__username', 'jti']


@admin.register(WAFRule)
class WAFRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'severity', 'is_active',
                    'hit_count', 'last_hit']
    list_filter = ['category', 'severity', 'is_active']
    search_fields = ['name', 'description', 'pattern']
    readonly_fields = ['hit_count', 'last_hit']


@admin.register(SecurityReport)
class SecurityReportAdmin(admin.ModelAdmin):
    list_display = ['report_id', 'scan_type', 'generated_at', 'resolved']
    list_filter = ['scan_type', 'resolved', 'generated_at']
    readonly_fields = ['report_id', 'generated_at', 'findings']
    date_hierarchy = 'generated_at'


@admin.register(ComplianceCheck)
class ComplianceCheckAdmin(admin.ModelAdmin):
    list_display = ['regulation', 'check_name', 'passed', 'checked_at']
    list_filter = ['regulation', 'passed']
    search_fields = ['check_name']
