"""
Application Hardening Service (HS) implementation.

Implements:
- WAF (Web Application Firewall) rules
- security.txt generation
- SRI (Subresource Integrity) hashes
- Additional security headers
- Exposed API key detection
"""

import hashlib
import logging
import os
import re
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.template.loader import render_to_string

from security.models import WAFRule, SecurityAuditLog

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# WAF Service
# ═══════════════════════════════════════════════════════════════════════════════

class WAFResult:
    """Resultado de la evaluación WAF."""

    def __init__(
        self,
        blocked: bool = False,
        rule_name: str = '',
        category: str = '',
        severity: str = '',
        description: str = '',
    ):
        self.blocked = blocked
        self.rule_name = rule_name
        self.category = category
        self.severity = severity
        self.description = description


class WAFService:
    """
    Web Application Firewall Service.

    Bloquea patrones de ataque comunes del OWASP Top 10:
    - SQL Injection
    - Cross-Site Scripting (XSS)
    - Path Traversal
    - Command Injection
    - CSRF
    """

    # Reglas por defecto (OWASP Top 10) - Modificadas para ser menos agresivas
    DEFAULT_RULES = [
        {
            'name': 'SQL Injection - Dangerous Keywords',
            'category': 'sql_injection',
            'pattern': r'(--|/\*|\*/|@@|union.*select|union.*all.*select|select.*from.*information_schema|drop.*table|truncate.*table)',
            'severity': 'critical',
            'description': 'Dangerous SQL keywords detected',
        },
        {
            'name': 'SQL Injection - System Tables',
            'category': 'sql_injection',
            'pattern': r'(sysobjects|syscolumns|sysdatabases|sysusers|sysxlogins|master\.\.sysdatabases)',
            'severity': 'critical',
            'description': 'System table reference detected',
        },
        {
            'name': 'XSS - Script Tags',
            'category': 'xss',
            'pattern': r'(<script[^>]*>.*</script>|<iframe[^>]*>.*</iframe>|<object[^>]*>.*</object>)',
            'severity': 'high',
            'description': 'XSS via script/iframe/object tags detected',
        },
        {
            'name': 'XSS - Event Handlers with malicious content',
            'category': 'xss',
            'pattern': r'(javascript:.*\(|<.*on\w+\s*=.*>)',
            'severity': 'high',
            'description': 'XSS via event handler detected',
        },
        {
            'name': 'Path Traversal - Multiple levels',
            'category': 'path_traversal',
            'pattern': r'(\.\./\.\./|\.\.\\\.\.\\|\.\.%2f\.\.%2f|\.\.%5c\.\.%5c)',
            'severity': 'high',
            'description': 'Path traversal attack with multiple levels detected',
        },
        {
            'name': 'Command Injection - Dangerous patterns',
            'category': 'command_injection',
            'pattern': r'(\|\||&&|;.*rm.*-rf|;.*del.*/q|;.*format|;.*shutdown)',
            'severity': 'critical',
            'description': 'Command injection with dangerous patterns detected',
        },
        {
            'name': 'CSRF - Missing or Invalid Token',
            'category': 'csrf',
            'pattern': r'',
            'severity': 'high',
            'description': 'CSRF protection check (handled by Django middleware)',
        },
    ]

    # Parámetros a verificar - solo los más peligrosos
    CHECK_PARAMETERS = ['cmd', 'command', 'exec', 'sh', 'bash', 'powershell', 'wget', 'curl']

    @classmethod
    def initialize_default_rules(cls):
        """
        Inicializa las reglas WAF por defecto si no existen.
        """
        for rule_data in cls.DEFAULT_RULES:
            WAFRule.objects.get_or_create(
                name=rule_data['name'],
                defaults={
                    'category': rule_data['category'],
                    'pattern': rule_data['pattern'],
                    'severity': rule_data['severity'],
                    'description': rule_data['description'],
                }
            )

    @classmethod
    def check_request(cls, request: HttpRequest) -> WAFResult:
        """
        Verifica una request contra las reglas WAF.

        Args:
            request: HttpRequest

        Returns:
            WAFResult: Resultado de la verificación
        """
        # Whitelist localhost en modo desarrollo
        if settings.DEBUG and request.META.get('REMOTE_ADDR') in ('127.0.0.1', '::1'):
            return WAFResult(blocked=False)
        
        # Eximir métodos HEAD y OPTIONS
        if request.method in ('HEAD', 'OPTIONS'):
            return WAFResult(blocked=False)

        # Verificar solo parámetros realmente peligrosos
        for param_name, param_value in request.GET.items():
            if param_name.lower() in cls.CHECK_PARAMETERS:
                result = cls._check_value(param_value, param_name)
                if result.blocked:
                    cls._log_waf_hit(result, request)
                    return result

        # Verificar POST data solo en rutas específicas
        if request.path_info.startswith('/api/') or 'upload' in request.path_info:
            for param_name, param_value in request.POST.items():
                if isinstance(param_value, str):
                    result = cls._check_value(param_value, param_name)
                    if result.blocked:
                        cls._log_waf_hit(result, request)
                        return result

        # Solo verificar path si tiene patrones claramente maliciosos
        path = request.path_info
        if path and (len(path) > 100 or '/../' in path or '..\\' in path):
            result = cls._check_value(path, 'path')
            if result.blocked:
                cls._log_waf_hit(result, request)
                return result

        return WAFResult(blocked=False)

    @classmethod
    def _check_value(cls, value: str, param_name: str) -> WAFResult:
        """
        Verifica un valor contra todas las reglas activas.

        Args:
            value: Valor a verificar
            param_name: Nombre del parámetro

        Returns:
            WAFResult: Resultado de la verificación
        """
        if not value or not isinstance(value, str):
            return WAFResult(blocked=False)

        # Obtener reglas activas de la base de datos
        rules = WAFRule.objects.filter(is_active=True)

        # Si no hay reglas en DB, usar las por defecto
        if not rules.exists():
            for rule_data in cls.DEFAULT_RULES:
                if rule_data['pattern']:
                    match = re.search(
                        rule_data['pattern'], value, re.IGNORECASE
                    )
                    if match:
                        return WAFResult(
                            blocked=True,
                            rule_name=rule_data['name'],
                            category=rule_data['category'],
                            severity=rule_data['severity'],
                            description=rule_data['description'],
                        )
            return WAFResult(blocked=False)

        # Usar reglas de la base de datos
        for rule in rules:
            if rule.pattern:
                match = re.search(rule.pattern, value, re.IGNORECASE)
                if match:
                    return WAFResult(
                        blocked=True,
                        rule_name=rule.name,
                        category=rule.category,
                        severity=rule.severity,
                        description=rule.description,
                    )

        return WAFResult(blocked=False)

    @classmethod
    def _log_waf_hit(cls, result: WAFResult, request: HttpRequest):
        """
        Registra un bloqueo WAF.

        Args:
            result: Resultado WAF
            request: HttpRequest
        """
        # Actualizar contador de la regla
        try:
            rule = WAFRule.objects.get(name=result.rule_name)
            rule.hit_count += 1
            rule.last_hit = __import__('django').utils.timezone.now()
            rule.save(update_fields=['hit_count', 'last_hit'])
        except WAFRule.DoesNotExist:
            pass

        # Determinar si es navegación normal
        path = request.path_info
        NORMAL_PATHS = ['/', '/favicon.ico', '/static/', '/media/', '/admin/jsi18n/']
        is_normal_navigation = any(path.startswith(p) or path == p for p in NORMAL_PATHS)
        is_localhost = request.META.get('REMOTE_ADDR', '') in ('127.0.0.1', '::1')
        
        # Si es navegación normal desde localhost, NO registrar en audit log
        if is_localhost and is_normal_navigation:
            # Solo log a archivo, no a base de datos
            import logging
            logger = logging.getLogger(__name__)
            logger.info(
                f'WAF: Blocked normal navigation from localhost - '
                f'{result.rule_name} - {request.method} {path} - '
                f'IP: {request.META.get("REMOTE_ADDR", "")}'
            )
            return

        # Registrar en audit log solo si es amenaza real o test significativo
        SecurityAuditLog.objects.create(
            event_type=SecurityAuditLog.EventTypes.API_REQUEST,
            action='waf_blocked',
            resource=f'waf/{result.category}',
            details={
                'rule_name': result.rule_name,
                'category': result.category,
                'description': result.description,
                'path': path,
                'method': request.method,
                'ip_address': request.META.get('REMOTE_ADDR', ''),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
                'query_string': request.META.get('QUERY_STRING', ''),
            },
            severity=SecurityAuditLog.SeverityLevels.CRITICAL,
            threat_level=8 if not is_localhost else 3,  # Menor threat_level si es localhost
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Security.txt Service
# ═══════════════════════════════════════════════════════════════════════════════

class SecurityTxtService:
    """
    Servicio de generación de security.txt.

    RFC 9116 - A Method for Web Security Policies.
    """

    @staticmethod
    def generate_security_txt() -> str:
        """
        Genera el contenido del archivo security.txt.

        Returns:
            str: Contenido del security.txt
        """
        contact_email = getattr(
            settings, 'SECURITY_CONTACT_EMAIL', 'security@cfbc.edu.ni'
        )
        encryption_key = getattr(
            settings, 'SECURITY_ENCRYPTION_KEY', ''
        )

        lines = [
            '# Security Policy for CFBC',
            '# https://cfbc.edu.ni',
            '',
            '======= Contact Information =======',
            f'Contact: mailto:{contact_email}',
            '',
            '======= Encryption =======',
        ]

        if encryption_key:
            lines.append(f'Encryption: {encryption_key}')

        lines.extend([
            '',
            '======= Disclosure Policy =======',
            'Preferred-Languages: es, en',
            'Policy: https://cfbc.edu.ni/.well-known/security-policy',
            '',
            '======= Acknowledgments =======',
            'Hiring: https://cfbc.edu.ni/jobs',
            '',
            '======= Expiration =======',
            f'Expires: {( __import__("django").utils.timezone.now() + __import__("django").utils.timezone.timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S.000Z")}',
        ])

        return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# SRI Hash Service
# ═══════════════════════════════════════════════════════════════════════════════

class SRIHashService:
    """
    Servicio de generación de hashes SRI (Subresource Integrity).

    Usa SHA-384 como algoritmo por defecto.
    """

    @staticmethod
    def generate_sri_hash(file_content: bytes) -> str:
        """
        Genera un hash SRI usando SHA-384.

        Args:
            file_content: Contenido del archivo en bytes

        Returns:
            str: Hash SRI en formato base64 (sha384-...)
        """
        hash_obj = hashlib.sha384(file_content)
        base64_hash = hash_obj.digest()
        import base64
        return f'sha384-{base64.b64encode(base64_hash).decode()}'

    @staticmethod
    def generate_sri_for_file(file_path: str) -> Optional[str]:
        """
        Genera un hash SRI para un archivo en el sistema de archivos.

        Args:
            file_path: Ruta al archivo

        Returns:
            Optional[str]: Hash SRI o None si el archivo no existe
        """
        if not os.path.exists(file_path):
            logger.error(f'File not found for SRI hash: {file_path}')
            return None

        with open(file_path, 'rb') as f:
            content = f.read()

        return SRIHashService.generate_sri_hash(content)

    @staticmethod
    def generate_sri_tag(file_path: str, resource_url: str) -> Optional[str]:
        """
        Genera un tag HTML completo con SRI.

        Args:
            file_path: Ruta local al archivo
            resource_url: URL del recurso

        Returns:
            Optional[str]: Tag HTML con SRI o None
        """
        sri_hash = SRIHashService.generate_sri_for_file(file_path)
        if not sri_hash:
            return None

        if resource_url.endswith('.js'):
            return (
                f'<script src="{resource_url}" '
                f'integrity="{sri_hash}" '
                f'crossorigin="anonymous"></script>'
            )
        elif resource_url.endswith('.css'):
            return (
                f'<link rel="stylesheet" href="{resource_url}" '
                f'integrity="{sri_hash}" '
                f'crossorigin="anonymous" />'
            )

        return None


# ═══════════════════════════════════════════════════════════════════════════════
# Security Headers Service
# ═══════════════════════════════════════════════════════════════════════════════

class SecurityHeadersService:
    """
    Servicio de headers de seguridad adicionales.
    """

    @staticmethod
    def get_additional_headers() -> dict:
        """
        Obtiene headers de seguridad adicionales.

        Returns:
            dict: Headers de seguridad
        """
        return {
            'Expect-CT': 'max-age=86400, enforce',
            'Permissions-Policy': (
                'camera=(), microphone=(), geolocation=(), '
                'interest-cohort=()'
            ),
            'X-Content-Type-Options': 'nosniff',
            'X-Permitted-Cross-Domain-Policies': 'none',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
        }

    @staticmethod
    def apply_headers(response: HttpResponse) -> HttpResponse:
        """
        Aplica headers de seguridad a una respuesta.

        Args:
            response: HttpResponse

        Returns:
            HttpResponse: Response con headers de seguridad
        """
        for header, value in SecurityHeadersService.get_additional_headers().items():
            response[header] = value
        return response


# ═══════════════════════════════════════════════════════════════════════════════
# Exposed API Key Detection Service
# ═══════════════════════════════════════════════════════════════════════════════

class ExposedKeyResult:
    """Resultado de detección de keys expuestas."""

    def __init__(
        self,
        file_path: str = '',
        line_number: int = 0,
        match: str = '',
        context: str = '',
        risk_level: str = 'medium',
    ):
        self.file_path = file_path
        self.line_number = line_number
        self.match = match
        self.context = context
        self.risk_level = risk_level


class ExposedKeyDetectionService:
    """
    Servicio de detección de API keys expuestas en el código.

    Detecta patrones: [A-Za-z0-9]{32,}
    """

    # Patrón para detectar API keys
    KEY_PATTERN = re.compile(r'[A-Za-z0-9]{32,}')

    # Archivos a escanear
    SCAN_EXTENSIONS = {'.py', '.js', '.html', '.yml', '.yaml', '.json',
                       '.env.example', '.ini', '.cfg', '.conf'}

    # Directorios a ignorar
    IGNORE_DIRS = {
        '.git', '__pycache__', 'node_modules', 'venv', '.venv',
        'env', '.env', 'migrations', 'staticfiles', 'media',
    }

    # Variables de entorno válidas (no son keys expuestas)
    ENV_VAR_PATTERN = re.compile(
        r'(SECRET_KEY|API_KEY|API_SECRET|ACCESS_TOKEN|PASSWORD|'
        r'DB_PASSWORD|EMAIL_HOST_PASSWORD)\s*=\s*["\']?([^"\']+)["\']?'
    )

    @classmethod
    def scan_file(cls, file_path: str, base_path: str = '') -> List[ExposedKeyResult]:
        """
        Escanea un archivo en busca de API keys expuestas.

        Args:
            file_path: Ruta al archivo
            base_path: Ruta base del proyecto

        Returns:
            List[ExposedKeyResult]: Lista de keys encontradas
        """
        results = []
        try:
            with open(file_path, 'r', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    # Ignorar líneas de importación y comentarios
                    stripped = line.strip()
                    if stripped.startswith('#') or stripped.startswith('//'):
                        continue
                    if 'import ' in stripped or 'from ' in stripped:
                        continue

                    # Buscar patrones de key
                    matches = cls.KEY_PATTERN.findall(stripped)
                    for match in matches:
                        # Verificar que no sea una variable de entorno
                        if cls.ENV_VAR_PATTERN.search(stripped):
                            continue

                        # Verificar que esté en un contexto de asignación
                        if '=' in stripped or ':' in stripped:
                            rel_path = os.path.relpath(file_path, base_path) if base_path else file_path
                            results.append(ExposedKeyResult(
                                file_path=rel_path,
                                line_number=line_num,
                                match=match[:16] + '...',
                                context=stripped[:100],
                                risk_level='high' if len(match) >= 40 else 'medium',
                            ))

        except (IOError, OSError) as e:
            logger.error(f'Error scanning file {file_path}: {e}')

        return results

    @classmethod
    def scan_codebase(cls, base_path: str = None) -> List[ExposedKeyResult]:
        """
        Escanea toda la base de código en busca de keys expuestas.

        Args:
            base_path: Ruta base del proyecto

        Returns:
            List[ExposedKeyResult]: Lista de keys encontradas
        """
        if base_path is None:
            base_path = settings.BASE_DIR

        results = []
        for root, dirs, files in os.walk(base_path):
            # Ignorar directorios
            dirs[:] = [d for d in dirs if d not in cls.IGNORE_DIRS]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in cls.SCAN_EXTENSIONS:
                    file_path = os.path.join(root, file)
                    results.extend(cls.scan_file(file_path, base_path))

        return results
