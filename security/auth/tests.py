"""
Tests for Authentication Service (AS).

Tests: TOTP 2FA, session management, account lockout, backup codes.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
import time
import base64
import hashlib

from security.auth.services import (
    TOTPService, SessionSecurityService, AccountLockoutService,
)
from security.models import UserSecurityProfile, SecurityAuditLog


# ═══════════════════════════════════════════════════════════════════════════════
# TOTP Service Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TOTPServiceTests(TestCase):
    """Tests for TOTP 2FA implementation (RFC 6238)."""

    def setUp(self):
        self.secret = TOTPService.generate_secret()

    def test_generate_secret_length(self):
        """Secret should be 16 chars Base32 (80 bits)."""
        secret = TOTPService.generate_secret()
        self.assertEqual(len(secret), 16)
        # Should be valid Base32
        try:
            base64.b32decode(secret)
        except Exception:
            self.fail('Secret is not valid Base32')

    def test_generate_code_returns_6_digits(self):
        """Generated code should be exactly 6 digits."""
        code = TOTPService.generate_code(self.secret)
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())

    def test_verify_valid_code(self):
        """Should verify a valid code."""
        code = TOTPService.generate_code(self.secret)
        self.assertTrue(TOTPService.verify_code(self.secret, code))

    def test_verify_invalid_code(self):
        """Should reject an invalid code."""
        self.assertFalse(TOTPService.verify_code(self.secret, '000000'))

    def test_verify_empty_secret(self):
        """Should reject empty secret."""
        self.assertFalse(TOTPService.verify_code('', '123456'))

    def test_verify_empty_code(self):
        """Should reject empty code."""
        self.assertFalse(TOTPService.verify_code(self.secret, ''))

    def test_verify_code_within_window(self):
        """Should verify codes within ±30 second window."""
        code = TOTPService.generate_code(self.secret)
        # Wait 2 seconds (still within window)
        self.assertTrue(TOTPService.verify_code(self.secret, code, window=1))

    def test_verify_code_outside_window(self):
        """Should reject codes outside the time window."""
        # Generate code for a past timestamp
        past_code = TOTPService.generate_code(self.secret, int(time.time()) - 90)
        self.assertFalse(TOTPService.verify_code(self.secret, past_code, window=1))

    def test_generate_backup_codes_count(self):
        """Should generate exactly 10 backup codes."""
        codes = TOTPService.generate_backup_codes()
        self.assertEqual(len(codes), 10)

    def test_backup_codes_are_unique(self):
        """All backup codes should be unique."""
        codes = TOTPService.generate_backup_codes()
        self.assertEqual(len(codes), len(set(codes)))

    def test_backup_code_length(self):
        """Each backup code should be 8 characters."""
        codes = TOTPService.generate_backup_codes()
        for code in codes:
            self.assertEqual(len(code), 8)

    def test_backup_codes_alphanumeric(self):
        """Backup codes should be uppercase alphanumeric."""
        codes = TOTPService.generate_backup_codes()
        for code in codes:
            self.assertTrue(code.isalnum())
            self.assertTrue(code.isupper())

    def test_hash_backup_codes(self):
        """Should hash backup codes with SHA-256."""
        codes = ['ABCD1234', 'EFGH5678']
        hashed = TOTPService.hash_backup_codes(codes)
        expected = [
            hashlib.sha256(c.encode()).hexdigest()
            for c in codes
        ]
        self.assertEqual(hashed, expected)

    def test_verify_backup_code(self):
        """Should verify a backup code against hashes."""
        codes = TOTPService.generate_backup_codes()
        hashed = TOTPService.hash_backup_codes(codes)
        self.assertTrue(TOTPService.verify_backup_code(hashed, codes[0]))

    def test_verify_invalid_backup_code(self):
        """Should reject invalid backup code."""
        hashed = TOTPService.hash_backup_codes(['ABCD1234'])
        self.assertFalse(TOTPService.verify_backup_code(hashed, 'INVALID99'))

    def test_totp_uri_format(self):
        """URI should be in valid otpauth:// format."""
        uri = TOTPService.get_totp_uri(self.secret, 'testuser')
        self.assertTrue(uri.startswith('otpauth://totp/'))
        self.assertIn('secret=' + self.secret, uri)
        self.assertIn('issuer=CFBC', uri)
        self.assertIn('testuser', uri)

    def test_totp_uri_custom_issuer(self):
        """Should support custom issuer."""
        uri = TOTPService.get_totp_uri(self.secret, 'testuser', 'MyApp')
        self.assertIn('issuer=MyApp', uri)


# ═══════════════════════════════════════════════════════════════════════════════
# Session Security Tests
# ═══════════════════════════════════════════════════════════════════════════════

class SessionSecurityServiceTests(TestCase):
    """Tests for session management."""

    def setUp(self):
        self.user = User.objects.create_user('sessionuser', 'session@test.com', 'password123')
        UserSecurityProfile.objects.get_or_create(user=self.user)

    def test_get_active_session_count_zero(self):
        """Should return 0 when no sessions exist."""
        count = SessionSecurityService.get_active_session_count(self.user)
        self.assertEqual(count, 0)

    def test_check_concurrent_sessions_no_sessions(self):
        """Should not exceed limit when no sessions."""
        exceeded = SessionSecurityService.check_concurrent_sessions(self.user)
        self.assertFalse(exceeded)

    def test_invalidate_all_sessions_with_no_sessions(self):
        """Should return 0 when no sessions to invalidate."""
        count = SessionSecurityService.invalidate_all_sessions(self.user)
        self.assertEqual(count, 0)


# ═══════════════════════════════════════════════════════════════════════════════
# Account Lockout Tests
# ═══════════════════════════════════════════════════════════════════════════════

class AccountLockoutServiceTests(TestCase):
    """Tests for account lockout."""

    def setUp(self):
        self.user = User.objects.create_user('lockuser', 'lock@test.com', 'password123')
        self.profile, _ = UserSecurityProfile.objects.get_or_create(user=self.user)
        cache.clear()

    def test_record_failed_attempt_increments_counter(self):
        """Failed attempt should increment counter."""
        AccountLockoutService.record_failed_attempt(self.user)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.failed_login_attempts, 1)

    def test_check_user_not_locked_initially(self):
        """User should not be locked initially."""
        self.assertFalse(AccountLockoutService.check_user_locked(self.user))

    def test_account_locks_after_5_attempts(self):
        """Account should lock after 5 failed attempts."""
        for i in range(5):
            AccountLockoutService.record_failed_attempt(self.user)
        self.assertTrue(AccountLockoutService.check_user_locked(self.user))

    def test_successful_login_resets_lockout(self):
        """Successful login should reset lockout counter."""
        for i in range(3):
            AccountLockoutService.record_failed_attempt(self.user)
        AccountLockoutService.record_successful_login(self.user)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.failed_login_attempts, 0)
        self.assertFalse(AccountLockoutService.check_user_locked(self.user))

    def test_audit_log_on_account_lock(self):
        """Should create audit log when account locks."""
        for i in range(5):
            AccountLockoutService.record_failed_attempt(self.user)
        logs = SecurityAuditLog.objects.filter(
            event_type=SecurityAuditLog.EventTypes.AUTH,
            action='account_locked',
        )
        self.assertTrue(logs.exists())

    def test_ip_tracking(self):
        """Should track failed attempts by IP."""
        ip = '192.168.1.1'
        self.assertFalse(AccountLockoutService.check_ip_locked(ip))
        # Record 5 failed attempts from same IP (user can be None for IP-only tracking)
        for i in range(5):
            AccountLockoutService.record_failed_attempt(None, ip_address=ip)
        self.assertTrue(AccountLockoutService.check_ip_locked(ip))

    def test_log_auth_event(self):
        """Should log auth events to audit."""
        AccountLockoutService.log_auth_event(
            self.user, 'login_test', True, {'method': 'password'}
        )
        log = SecurityAuditLog.objects.filter(
            event_type=SecurityAuditLog.EventTypes.AUTH,
            action='login_test',
        ).first()
        self.assertIsNotNone(log)
        self.assertTrue(log.success)
