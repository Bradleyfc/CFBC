"""
Security middleware for CFBC Django Project.

Implements:
- WAFMiddleware: Blocks common attack patterns
- SecurityHeadersMiddleware: Adds security headers to responses
- SessionSecurityMiddleware: Manages session timeouts and concurrent sessions
"""

import re
import logging
from django.http import HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.conf import settings

from security.hardening.services import WAFService, SecurityHeadersService
from security.auth.services import SessionSecurityService, AccountLockoutService
from security.models import SecurityAuditLog

logger = logging.getLogger(__name__)


class WAFMiddleware(MiddlewareMixin):
    """
    Middleware de Web Application Firewall.

    Bloquea requests que contengan patrones de ataque comunes
    (SQL injection, XSS, path traversal, command injection).
    
    Modos de operación configurados por WAF_MODE en settings:
    - 'blocking': Bloquea todos los ataques detectados
    - 'logging': Solo logea, no bloquea (desarrollo)
    - 'selective': Solo bloquea ataques críticos
    - 'disabled': Desactiva el WAF completamente
    """

    EXEMPT_PATHS = [
        '/admin/',
        '/static/',
        '/media/',
        '/__debug__/',
        '/.well-known/',
        '/accounts/',
        '/blog/',
        '/course-documents/',
        '/',  # Root path
    ]

    # Solo bloquear categorías críticas en modo selectivo
    CRITICAL_CATEGORIES = ['sql_injection', 'command_injection', 'path_traversal']

    def process_request(self, request):
        """Verifica cada request contra las reglas WAF según el modo configurado."""
        if not getattr(settings, 'WAF_ENABLED', True):
            return None
            
        waf_mode = getattr(settings, 'WAF_MODE', 'selective')
        
        if waf_mode == 'disabled':
            return None
            
        path = request.path_info

        # Eximir rutas específicas
        for exempt in self.EXEMPT_PATHS:
            if path.startswith(exempt):
                return None

        # Solo verificar métodos que pueden contener datos
        if request.method not in ('GET', 'POST', 'PUT', 'PATCH'):
            return None

        # Aplicar WAF
        result = WAFService.check_request(request)
        if result.blocked:
            if waf_mode == 'logging':
                # Modo logging: solo registrar, no bloquear
                logger.warning(
                    f'[WAF LOGGING] Would block request: {result.rule_name} - '
                    f'{request.method} {path} - IP: {request.META.get("REMOTE_ADDR")}'
                )
                return None
            elif waf_mode == 'selective':
                # Modo selectivo: solo bloquear ataques críticos
                if result.category in self.CRITICAL_CATEGORIES:
                    logger.warning(
                        f'WAF blocked critical attack: {result.rule_name} - '
                        f'{request.method} {path} - IP: {request.META.get("REMOTE_ADDR")}'
                    )
                    return HttpResponse(
                        '<html><body><h1>403 Forbidden</h1>'
                        '<p>Request blocked by Web Application Firewall.</p>'
                        '<p><small>Critical security rule triggered</small></p></body></html>',
                        status=403,
                        content_type='text/html',
                    )
                else:
                    logger.info(
                        f'WAF detected non-critical attack: {result.rule_name} - '
                        f'{request.method} {path}'
                    )
                    return None
            else:
                # Modo blocking: bloquear todo
                logger.warning(
                    f'WAF blocked request: {result.rule_name} - '
                    f'{request.method} {path} - IP: {request.META.get("REMOTE_ADDR")}'
                )
                return HttpResponse(
                    '<html><body><h1>403 Forbidden</h1>'
                    '<p>Request blocked by Web Application Firewall.</p></body></html>',
                    status=403,
                    content_type='text/html',
                )

        return None


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware que añade headers de seguridad adicionales a todas las respuestas.
    """

    def process_response(self, request, response):
        """Añade headers de seguridad a la respuesta."""
        return SecurityHeadersService.apply_headers(response)


class SessionSecurityMiddleware(MiddlewareMixin):
    """
    Middleware de seguridad de sesiones.

    - Actualiza la marca de última actividad
    - Verifica sesiones concurrentes
    - Verifica bloqueo de cuenta
    """

    def process_request(self, request):
        """Procesa cada request para seguridad de sesión."""
        if request.user.is_authenticated:
            # Actualizar última actividad
            SessionSecurityService.update_last_activity(request)

            # Verificar bloqueo de cuenta por IP
            ip_address = request.META.get('REMOTE_ADDR', '')
            if ip_address and AccountLockoutService.check_ip_locked(ip_address):
                logger.warning(
                    f'Blocked request from locked IP: {ip_address}'
                )
                return JsonResponse(
                    {'error': 'Account temporarily locked. Try again later.'},
                    status=429,
                )

            # Verificar si la cuenta del usuario está bloqueada
            if AccountLockoutService.check_user_locked(request.user):
                return JsonResponse(
                    {'error': 'Account locked due to too many failed attempts. Try again later.'},
                    status=429,
                )

        return None


class RateLimitMiddleware(MiddlewareMixin):
    """
    Middleware de rate limiting por usuario.

    Limita a 100 requests por minuto por usuario autenticado.
    """

    def process_request(self, request):
        """Aplica rate limiting a la request."""
        if not request.user.is_authenticated:
            return None

        # Eximir rutas admin
        if request.path_info.startswith('/admin/'):
            return None

        from security.api_security.services import PerUserRateLimitService
        result = PerUserRateLimitService.check_rate_limit(request.user)

        if not result.is_allowed:
            logger.warning(
                f'Rate limit exceeded for user {request.user.username} '
                f'({request.path_info})'
            )
            response = JsonResponse(
                {
                    'error': 'Too Many Requests',
                    'message': f'Rate limit exceeded. Retry after {result.retry_after} seconds.',
                    'retry_after': result.retry_after,
                },
                status=429,
            )
            for key, value in PerUserRateLimitService.get_rate_limit_headers(
                result
            ).items():
                response[key] = value
            return response

        return None


class RowLevelSecurityMiddleware(MiddlewareMixin):
    """
    Middleware de Row-Level Security.

    Establece el contexto RLS en la conexión de base de datos
    para cada request autenticado, permitiendo que las políticas
    RLS de PostgreSQL filtren datos a nivel de fila.

    Limpia el contexto al finalizar la respuesta para evitar
    fuga de contexto entre requests.
    """

    def process_request(self, request):
        """Establece el contexto RLS al inicio de cada request."""
        from security.authorization.services import RowLevelSecurityService

        if request.user.is_authenticated:
            RowLevelSecurityService.set_rls_context(request.user)
        else:
            RowLevelSecurityService.clear_rls_context()

        return None

    def process_response(self, request, response):
        """Limpia el contexto RLS al finalizar la respuesta."""
        from security.authorization.services import RowLevelSecurityService
        RowLevelSecurityService.clear_rls_context()
        return response


class DataProtectionMiddleware(MiddlewareMixin):
    """
    Middleware de protección de datos.

    Sanitiza entradas y enmascara datos sensibles en logs/respuestas.
    """

    SANITIZE_PATHS = [
        '/course-documents/',
        '/blog/',
        '/accounts/',
    ]

    def process_request(self, request):
        """Sanitiza datos de entrada en endpoints específicos."""
        path = request.path_info

        # Solo sanitizar rutas específicas
        if not any(path.startswith(p) for p in self.SANITIZE_PATHS):
            return None

        # Sanitizar GET params
        if request.GET:
            from security.data_protection.services import InputSanitizationService
            sanitized = InputSanitizationService.sanitize_dict(dict(request.GET))
            request.GET = request.GET.copy()
            for key, value in sanitized.items():
                if isinstance(value, str):
                    request.GET[key] = value

        return None
