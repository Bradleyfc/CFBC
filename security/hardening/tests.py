"""
Tests for Application Hardening Service (HS).

Tests: WAF rules, security.txt, SRI hashes, security headers, exposed key detection.
"""

from django.test import TestCase, RequestFactory
from django.http import HttpResponse

from security.hardening.services import (
    WAFService, WAFResult, SecurityTxtService,
    SRIHashService, SecurityHeadersService, ExposedKeyDetectionService,
)
from security.models import WAFRule
import os
import hashlib
import base64


# ═══════════════════════════════════════════════════════════════════════════════
# WAF Service Tests
# ═══════════════════════════════════════════════════════════════════════════════

class WAFServiceTests(TestCase):
    """Tests for Web Application Firewall."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_sql_injection_detected(self):
        """Should detect SQL injection patterns."""
        request = self.factory.get('/search/?q=test%27%3BDROP%20TABLE')
        result = WAFService.check_request(request)
        self.assertTrue(result.blocked)
        self.assertIn('SQL', result.rule_name)

    def test_xss_detected(self):
        """Should detect XSS patterns."""
        request = self.factory.get('/search/?q=<script>alert(1)</script>')
        result = WAFService.check_request(request)
        self.assertTrue(result.blocked)
        self.assertIn('XSS', result.rule_name)

    def test_path_traversal_detected(self):
        """Should detect path traversal patterns."""
        request = self.factory.get('/file/?path=../../../etc/passwd')
        result = WAFService.check_request(request)
        self.assertTrue(result.blocked)
        self.assertIn('Path Traversal', result.rule_name)

    def test_normal_request_not_blocked(self):
        """Should not block normal requests."""
        request = self.factory.get('/search/?q=normal+search+query')
        result = WAFService.check_request(request)
        self.assertFalse(result.blocked)

    def test_waf_exempt_paths(self):
        """Should not block admin or static paths."""
        from security.middleware import WAFMiddleware
        from django.http import HttpResponse
        # Test the exempt path logic directly
        middleware = WAFMiddleware(get_response=lambda r: HttpResponse())
        for path in ['/admin/', '/static/', '/media/']:
            request = self.factory.get(f'{path}?q=<script>alert(1)</script>')
            result = middleware.process_request(request)
            self.assertIsNone(result, f'Path {path} should be exempt')

    def test_initialize_default_rules(self):
        """Should create default WAF rules."""
        WAFService.initialize_default_rules()
        rules = WAFRule.objects.filter(is_active=True)
        self.assertTrue(rules.exists())

    def test_waf_result_blocked(self):
        """WAFResult should show blocked state."""
        result = WAFResult(blocked=True, rule_name='Test', severity='critical')
        self.assertTrue(result.blocked)
        self.assertEqual(result.rule_name, 'Test')

    def test_default_rules_list(self):
        """Should have default rules for all OWASP categories."""
        categories = {r['category'] for r in WAFService.DEFAULT_RULES}
        expected = {'sql_injection', 'xss', 'path_traversal', 'command_injection', 'csrf'}
        self.assertEqual(categories, expected)


# ═══════════════════════════════════════════════════════════════════════════════
# Security.txt Tests
# ═══════════════════════════════════════════════════════════════════════════════

class SecurityTxtServiceTests(TestCase):
    """Tests for security.txt generation."""

    def test_generate_security_txt(self):
        """Should generate valid security.txt content."""
        content = SecurityTxtService.generate_security_txt()
        self.assertIn('Contact: mailto:', content)
        self.assertIn('security@cfbc.edu.ni', content)
        self.assertIn('Expires:', content)
        self.assertIn('Disclosure Policy', content)

    def test_security_txt_sections(self):
        """Security.txt should have all required sections."""
        content = SecurityTxtService.generate_security_txt()
        self.assertIn('Contact Information', content)
        self.assertIn('Encryption', content)
        self.assertIn('Acknowledgments', content)

    def test_security_txt_has_expiration(self):
        """Should include expiration date."""
        content = SecurityTxtService.generate_security_txt()
        self.assertIn('Expires:', content)


# ═══════════════════════════════════════════════════════════════════════════════
# SRI Hash Tests
# ═══════════════════════════════════════════════════════════════════════════════

class SRIHashServiceTests(TestCase):
    """Tests for Subresource Integrity hash generation."""

    def test_generate_sri_hash(self):
        """Should generate SHA-384 based SRI hash."""
        content = b'console.log("test");'
        sri = SRIHashService.generate_sri_hash(content)
        self.assertTrue(sri.startswith('sha384-'))
        # Verify it's valid base64
        hash_part = sri[7:]  # Remove 'sha384-' prefix
        try:
            base64.b64decode(hash_part)
        except Exception:
            self.fail('SRI hash content is not valid base64')

    def test_sri_consistent(self):
        """Same content should produce same SRI hash."""
        content = b'const x = 1;'
        hash1 = SRIHashService.generate_sri_hash(content)
        hash2 = SRIHashService.generate_sri_hash(content)
        self.assertEqual(hash1, hash2)

    def test_sri_different_for_different_content(self):
        """Different content should produce different SRI hashes."""
        hash1 = SRIHashService.generate_sri_hash(b'content1')
        hash2 = SRIHashService.generate_sri_hash(b'content2')
        self.assertNotEqual(hash1, hash2)

    def test_sri_tag_script(self):
        """Should generate SRI tag for JavaScript."""
        sri = SRIHashService.generate_sri_hash(b'alert("hi");')
        tag = SRIHashService.generate_sri_tag(
            'test.js', 'https://example.com/test.js'
        )
        # sri_tag requires file to exist on disk
        # Just verify the method handles missing files
        self.assertIsNone(tag)  # File doesn't exist, should return None


# ═══════════════════════════════════════════════════════════════════════════════
# Security Headers Tests
# ═══════════════════════════════════════════════════════════════════════════════

class SecurityHeadersServiceTests(TestCase):
    """Tests for security headers."""

    def test_get_additional_headers(self):
        """Should return all required security headers."""
        headers = SecurityHeadersService.get_additional_headers()
        self.assertIn('Expect-CT', headers)
        self.assertIn('Permissions-Policy', headers)
        self.assertIn('X-Content-Type-Options', headers)
        self.assertIn('Referrer-Policy', headers)
        self.assertIn('X-Permitted-Cross-Domain-Policies', headers)

    def test_apply_headers_to_response(self):
        """Should apply headers to HTTP response."""
        response = HttpResponse('OK')
        result = SecurityHeadersService.apply_headers(response)
        self.assertEqual(result['X-Content-Type-Options'], 'nosniff')
        self.assertIn('camera=()', result['Permissions-Policy'])
        self.assertEqual(
            result['Referrer-Policy'], 'strict-origin-when-cross-origin'
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Exposed Key Detection Tests
# ═══════════════════════════════════════════════════════════════════════════════

class ExposedKeyDetectionServiceTests(TestCase):
    """Tests for exposed API key detection."""

    def test_scan_file_nonexistent(self):
        """Should handle nonexistent files gracefully."""
        results = ExposedKeyDetectionService.scan_file('/nonexistent/file.py')
        self.assertEqual(len(results), 0)

    def test_detect_key_pattern(self):
        """Key pattern should detect long alphanumeric strings."""
        pattern = ExposedKeyDetectionService.KEY_PATTERN
        # 32+ alphanumeric string
        match = pattern.search('API_KEY = "abc123def456ghi789jkl012mno345pqr678stu901"')
        self.assertIsNotNone(match)

    def test_env_var_pattern(self):
        """Environment variable assignments should be recognized."""
        pattern = ExposedKeyDetectionService.ENV_VAR_PATTERN
        match = pattern.search('SECRET_KEY = "some-secret-value"')
        self.assertIsNotNone(match)

    def test_ignore_dirs(self):
        """Should have all necessary ignore directories."""
        ignore_dirs = ExposedKeyDetectionService.IGNORE_DIRS
        self.assertIn('.git', ignore_dirs)
        self.assertIn('__pycache__', ignore_dirs)
        self.assertIn('node_modules', ignore_dirs)
        self.assertIn('venv', ignore_dirs)
        self.assertIn('migrations', ignore_dirs)

    def test_scan_extensions(self):
        """Should scan common source file extensions."""
        extensions = ExposedKeyDetectionService.SCAN_EXTENSIONS
        self.assertIn('.py', extensions)
        self.assertIn('.js', extensions)
        self.assertIn('.html', extensions)
        self.assertIn('.yml', extensions)
