"""
Advanced Security Features for CFBC Django Project.

This app implements the following security components:
- Authentication Service (AS): TOTP 2FA, session management, account lockout
- Authorization Service (AZ): RBAC, object-level permissions, time-based access
- Data Protection Service (DS): AES-256-GCM encryption, input sanitization, file validation
- API Security Service (APIS): Rate limiting, JWT management, API keys, OAuth2
- Application Hardening Service (HS): WAF rules, security.txt, SRI hashes
- Security Testing Service (TS): Automated security tests, compliance reports
"""

default_app_config = 'security.apps.SecurityConfig'
