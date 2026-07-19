"""
Views for Application Hardening Service.
"""

from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required

from security.hardening.services import (
    SecurityTxtService, SecurityHeadersService,
)


@require_http_methods(['GET'])
def security_txt(request):
    """Sirve el archivo security.txt en /.well-known/security.txt"""
    content = SecurityTxtService.generate_security_txt()
    return HttpResponse(content, content_type='text/plain')


@require_http_methods(['GET'])
def security_policy(request):
    """Sirve la política de divulgación de seguridad."""
    content = [
        '# Security Disclosure Policy',
        '',
        'Thank you for helping keep CFBC secure.',
        '',
        '## Reporting a Vulnerability',
        '',
        'If you discover a security vulnerability, please:',
        '',
        '1. Do NOT disclose it publicly',
        '2. Send an email to security@cfbc.edu.ni',
        '3. Include a detailed description and steps to reproduce',
        '4. Include your contact information for follow-up',
        '',
        '## What to expect',
        '',
        '- Acknowledgment within 48 hours',
        '- Regular updates on the remediation progress',
        '- Credit in our security acknowledgments (if desired)',
    ]
    return HttpResponse('\n'.join(content), content_type='text/plain')


@staff_member_required
@require_http_methods(['GET'])
def check_headers(request):
    """Verifica los headers de seguridad configurados."""
    headers = SecurityHeadersService.get_additional_headers()

    # Verificar headers estándar de Django
    django_checks = {
        'SECURE_SSL_REDIRECT': False,
        'SESSION_COOKIE_SECURE': False,
        'CSRF_COOKIE_SECURE': False,
        'X_FRAME_OPTIONS': 'DENY',
        'SECURE_CONTENT_TYPE_NOSNIFF': True,
        'SECURE_BROWSER_XSS_FILTER': True,
    }

    from django.conf import settings
    for check, expected in django_checks.items():
        actual = getattr(settings, check, None)
        django_checks[check] = {
            'expected': expected,
            'actual': actual,
            'passed': actual == expected,
        }

    return JsonResponse({
        'additional_headers': headers,
        'django_security_settings': django_checks,
    })
