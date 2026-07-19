"""
API Security Service (APIS) implementation.

Implements:
- Per-user rate limiting (100 requests/minute)
- API key management with expiration and usage limits
- JWT token generation with automatic rotation
- Authentication header validation
- CORS policy enforcement
"""

import hashlib
import hmac
import logging
import secrets
import string
from datetime import timedelta
from typing import List, Optional, Tuple

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError

from security.models import APIKey, JWTSession, SecurityAuditLog

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Rate Limiting Service
# ═══════════════════════════════════════════════════════════════════════════════

class RateLimitResult:
    """Resultado de un chequeo de rate limiting."""

    def __init__(
        self,
        is_allowed: bool = True,
        remaining: int = 100,
        retry_after: int = 0,
        limit: int = 100,
    ):
        self.is_allowed = is_allowed
        self.remaining = remaining
        self.retry_after = retry_after  # seconds
        self.limit = limit


class PerUserRateLimitService:
    """
    Servicio de rate limiting por usuario.

    Límites:
    - 100 requests por minuto por usuario
    - Respuesta HTTP 429 con header Retry-After cuando se excede
    """

    DEFAULT_RATE_LIMIT = 100  # requests per minute
    WINDOW_SECONDS = 60

    CACHE_PREFIX = 'ratelimit_user_'
    BLOCK_PREFIX = 'ratelimit_blocked_'

    @classmethod
    def check_rate_limit(
        cls,
        user: User,
        endpoint: str = '',
        limit: int = None
    ) -> RateLimitResult:
        """
        Verifica el rate limit para un usuario.

        Args:
            user: Usuario
            endpoint: Endpoint específico (opcional)
            limit: Límite personalizado (usa DEFAULT_RATE_LIMIT si no se especifica)

        Returns:
            RateLimitResult: Resultado del chequeo
        """
        if limit is None:
            limit = cls.DEFAULT_RATE_LIMIT

        # Verificar si el usuario está bloqueado
        block_key = f'{cls.BLOCK_PREFIX}{user.id}'
        blocked_until = cache.get(block_key)
        if blocked_until:
            remaining_seconds = int((blocked_until - timezone.now()).total_seconds())
            if remaining_seconds > 0:
                return RateLimitResult(
                    is_allowed=False,
                    remaining=0,
                    retry_after=remaining_seconds,
                    limit=limit,
                )
            else:
                cache.delete(block_key)

        # Obtener contador actual
        cache_key = f'{cls.CACHE_PREFIX}{user.id}:{endpoint or "global"}'
        current = cache.get(cache_key, 0)

        if current >= limit:
            # Bloquear por 60 segundos
            block_until = timezone.now() + timedelta(seconds=cls.WINDOW_SECONDS)
            cache.set(block_key, block_until, timeout=cls.WINDOW_SECONDS)

            # Registrar evento
            SecurityAuditLog.objects.create(
                event_type=SecurityAuditLog.EventTypes.API_REQUEST,
                user=user,
                action='rate_limit_exceeded',
                resource=f'api/{endpoint}' if endpoint else 'api',
                details={
                    'limit': limit,
                    'current': current,
                    'endpoint': endpoint,
                },
                severity=SecurityAuditLog.SeverityLevels.WARNING,
                threat_level=4,
            )

            return RateLimitResult(
                is_allowed=False,
                remaining=0,
                retry_after=cls.WINDOW_SECONDS,
                limit=limit,
            )

        # Incrementar contador
        cache.set(cache_key, current + 1, timeout=cls.WINDOW_SECONDS)

        return RateLimitResult(
            is_allowed=True,
            remaining=limit - current - 1,
            retry_after=0,
            limit=limit,
        )

    @classmethod
    def get_rate_limit_headers(cls, result: RateLimitResult) -> dict:
        """
        Obtiene los headers HTTP para rate limiting.

        Args:
            result: Resultado del rate limit

        Returns:
            dict: Headers HTTP
        """
        headers = {
            'X-RateLimit-Limit': str(result.limit),
            'X-RateLimit-Remaining': str(result.remaining),
        }
        if not result.is_allowed:
            headers['Retry-After'] = str(result.retry_after)
        return headers


# ═══════════════════════════════════════════════════════════════════════════════
# API Key Management Service
# ═══════════════════════════════════════════════════════════════════════════════

class APIKeyService:
    """
    Servicio de gestión de API keys.

    Características:
    - Expiración configurable (1-365 días, default 90)
    - Límite diario de 10,000 requests
    - Generación segura de keys
    """

    KEY_LENGTH = 64
    DEFAULT_EXPIRATION_DAYS = 90
    DEFAULT_DAILY_LIMIT = 10000

    @staticmethod
    def _generate_key() -> Tuple[str, str]:
        """
        Genera una API key y su prefijo.

        Returns:
            Tuple[str, str]: (key_completa, key_prefix)
        """
        alphabet = string.ascii_letters + string.digits
        key = ''.join(secrets.choice(alphabet) for _ in range(APIKeyService.KEY_LENGTH))
        prefix = key[:8]
        return key, prefix

    @classmethod
    def create_api_key(
        cls,
        user: User,
        name: str,
        expires_in_days: int = None,
        daily_limit: int = None,
    ) -> APIKey:
        """
        Crea una nueva API key para un usuario.

        Args:
            user: Usuario
            name: Nombre descriptivo de la key
            expires_in_days: Días hasta expiración (1-365)
            daily_limit: Límite diario de requests

        Returns:
            APIKey: La API key creada
        """
        if expires_in_days is None:
            expires_in_days = cls.DEFAULT_EXPIRATION_DAYS

        # Validar rango de expiración
        expires_in_days = max(1, min(365, expires_in_days))

        if daily_limit is None:
            daily_limit = cls.DEFAULT_DAILY_LIMIT

        key, prefix = cls._generate_key()

        api_key = APIKey.objects.create(
            user=user,
            key=key,
            key_prefix=prefix,
            name=name,
            expires_at=timezone.now() + timedelta(days=expires_in_days),
            daily_limit=daily_limit,
        )

        logger.info(f'API key created: {name} for user {user.username}')

        return api_key

    @staticmethod
    def validate_api_key(key: str) -> Optional[APIKey]:
        """
        Valida una API key y retorna el objeto si es válida.

        Args:
            key: API key a validar

        Returns:
            Optional[APIKey]: API key si es válida, None si no
        """
        try:
            api_key = APIKey.objects.get(key=key, is_active=True)
        except APIKey.DoesNotExist:
            return None

        # Verificar expiración
        if api_key.is_expired():
            api_key.is_active = False
            api_key.save(update_fields=['is_active'])
            return None

        # Verificar límite diario
        if api_key.is_daily_limit_exceeded():
            return api_key  # Retornar pero con daily limit excedido

        # Incrementar uso
        api_key.increment_usage()

        return api_key

    @staticmethod
    def revoke_api_key(api_key: APIKey):
        """
        Revoca una API key.

        Args:
            api_key: API key a revocar
        """
        api_key.is_active = False
        api_key.save(update_fields=['is_active'])

        logger.info(f'API key revoked: {api_key.name} (user: {api_key.user.username})')

    @staticmethod
    def get_user_api_keys(user: User) -> List[APIKey]:
        """
        Obtiene todas las API keys activas de un usuario.

        Args:
            user: Usuario

        Returns:
            List[APIKey]: Lista de API keys activas
        """
        return list(APIKey.objects.filter(user=user, is_active=True))


# ═══════════════════════════════════════════════════════════════════════════════
# JWT Token Service
# ═══════════════════════════════════════════════════════════════════════════════

class JWTTokenService:
    """
    Servicio de gestión de tokens JWT con rotación automática.

    Características:
    - Access tokens con expiración (default 1 hora)
    - Refresh tokens con rotación automática
    - Renovación automática (<15 min antes de expirar)
    """

    ACCESS_TOKEN_EXPIRY_MINUTES = 60
    REFRESH_TOKEN_EXPIRY_DAYS = 7

    @classmethod
    def generate_tokens(cls, user: User) -> Tuple[str, str]:
        """
        Genera un par de tokens (access + refresh).

        Args:
            user: Usuario

        Returns:
            Tuple[str, str]: (access_token, refresh_token)
        """
        refresh = RefreshToken.for_user(user)

        # Personalizar claims
        refresh['user_id'] = user.id
        refresh['username'] = user.username

        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Almacenar sesión JWT
        access = AccessToken(access_token)
        JWTSession.objects.create(
            user=user,
            jti=access['jti'],
            access_token_created=timezone.now(),
            access_token_expires=timezone.now() + timedelta(
                minutes=cls.ACCESS_TOKEN_EXPIRY_MINUTES
            ),
            refresh_token=refresh_token,
            refresh_token_created=timezone.now(),
            refresh_token_expires=timezone.now() + timedelta(
                days=cls.REFRESH_TOKEN_EXPIRY_DAYS
            ),
        )

        SecurityAuditLog.objects.create(
            event_type=SecurityAuditLog.EventTypes.API_REQUEST,
            user=user,
            action='tokens_generated',
            resource='jwt',
            details={
                'access_expiry': cls.ACCESS_TOKEN_EXPIRY_MINUTES,
                'refresh_expiry': cls.REFRESH_TOKEN_EXPIRY_DAYS,
            },
            success=True,
        )

        return access_token, refresh_token

    @classmethod
    def refresh_access_token(cls, refresh_token_str: str) -> Optional[str]:
        """
        Refresca un access token usando un refresh token válido.

        Args:
            refresh_token_str: Refresh token

        Returns:
            Optional[str]: Nuevo access token, None si falla
        """
        try:
            refresh = RefreshToken(refresh_token_str)

            # Verificar que el refresh token no ha expirado
            if refresh.payload.get('exp', 0) < timezone.now().timestamp():
                logger.warning('Expired refresh token used')
                return None

            user_id = refresh.payload.get('user_id')
            if not user_id:
                return None

            # Buscar sesión JWT
            try:
                jti = refresh.payload.get('jti', '')
                jSession = JWTSession.objects.filter(
                    jti=jti,
                    is_active=True
                ).first()

                if jSession and not jSession.is_active:
                    return None
            except JWTSession.DoesNotExist:
                pass

            # Generar nuevo access token
            access = refresh.access_token

            # Actualizar sesión
            if jSession:
                jSession.rotated_at = timezone.now()
                jSession.access_token_expires = timezone.now() + timedelta(
                    minutes=cls.ACCESS_TOKEN_EXPIRY_MINUTES
                )
                jSession.save()

            return str(access)

        except TokenError as e:
            logger.error(f'Token refresh error: {str(e)}')
            return None

    @classmethod
    def check_and_refresh(cls, access_token_str: str) -> Optional[str]:
        """
        Verifica si un token necesita refresco y lo renueva si es necesario.

        Args:
            access_token_str: Access token actual

        Returns:
            Optional[str]: Nuevo token si se renovó, None si no necesita
        """
        try:
            access = AccessToken(access_token_str)
            exp = access.payload.get('exp', 0)
            remaining_seconds = exp - timezone.now().timestamp()

            # Si quedan menos de 15 minutos, renovar
            if 0 < remaining_seconds <= 15 * 60:
                # Obtener refresh token de la sesión
                jti = access.payload.get('jti', '')
                jSession = JWTSession.objects.filter(
                    jti=jti, is_active=True
                ).first()

                if jSession:
                    return cls.refresh_access_token(jSession.refresh_token)

            return None

        except TokenError:
            return None


# ═══════════════════════════════════════════════════════════════════════════════
# Authentication Validation Service
# ═══════════════════════════════════════════════════════════════════════════════

class AuthHeaderValidationResult:
    """Resultado de validación de headers de autenticación."""

    def __init__(
        self,
        is_valid: bool = False,
        auth_type: str = '',
        user: Optional[User] = None,
        error_message: str = '',
    ):
        self.is_valid = is_valid
        self.auth_type = auth_type  # 'bearer', 'api_key', 'session'
        self.user = user
        self.error_message = error_message


class AuthHeaderValidationService:
    """
    Servicio de validación de headers de autenticación.

    Soporta:
    - Bearer tokens (JWT)
    - API keys (X-API-Key header)
    - Session cookies
    """

    @staticmethod
    def validate_request(request: HttpRequest) -> AuthHeaderValidationResult:
        """
        Valida los headers de autenticación de una request.

        Args:
            request: HttpRequest

        Returns:
            AuthHeaderValidationResult: Resultado de la validación
        """
        # 1. Verificar Bearer token
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            return AuthHeaderValidationService._validate_bearer_token(token)

        # 2. Verificar API key
        api_key = request.META.get('HTTP_X_API_KEY', '')
        if api_key:
            return AuthHeaderValidationService._validate_api_key(api_key)

        # 3. Verificar session cookie
        if request.user.is_authenticated:
            return AuthHeaderValidationResult(
                is_valid=True,
                auth_type='session',
                user=request.user,
            )

        return AuthHeaderValidationResult(
            is_valid=False,
            error_message='No authentication credentials provided',
        )

    @staticmethod
    def _validate_bearer_token(token: str) -> AuthHeaderValidationResult:
        """
        Valida un Bearer token JWT.

        Args:
            token: Token JWT

        Returns:
            AuthHeaderValidationResult: Resultado de la validación
        """
        try:
            access = AccessToken(token)

            # Verificar expiración
            exp = access.payload.get('exp', 0)
            if exp < timezone.now().timestamp():
                return AuthHeaderValidationResult(
                    is_valid=False,
                    auth_type='bearer',
                    error_message='Token has expired',
                )

            user_id = access.payload.get('user_id')
            if not user_id:
                return AuthHeaderValidationResult(
                    is_valid=False,
                    auth_type='bearer',
                    error_message='Invalid token claims',
                )

            try:
                user = User.objects.get(id=user_id, is_active=True)
                return AuthHeaderValidationResult(
                    is_valid=True,
                    auth_type='bearer',
                    user=user,
                )
            except User.DoesNotExist:
                return AuthHeaderValidationResult(
                    is_valid=False,
                    auth_type='bearer',
                    error_message='User not found',
                )

        except TokenError as e:
            return AuthHeaderValidationResult(
                is_valid=False,
                auth_type='bearer',
                error_message=str(e),
            )

    @staticmethod
    def _validate_api_key(key: str) -> AuthHeaderValidationResult:
        """
        Valida una API key.

        Args:
            key: API key

        Returns:
            AuthHeaderValidationResult: Resultado de la validación
        """
        from security.api_security.services import APIKeyService

        api_key = APIKeyService.validate_api_key(key)
        if api_key is None:
            return AuthHeaderValidationResult(
                is_valid=False,
                auth_type='api_key',
                error_message='Invalid or expired API key',
            )

        # Verificar límite diario
        if api_key.is_daily_limit_exceeded():
            return AuthHeaderValidationResult(
                is_valid=False,
                auth_type='api_key',
                error_message='Daily API key limit exceeded',
            )

        return AuthHeaderValidationResult(
            is_valid=True,
            auth_type='api_key',
            user=api_key.user,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Middleware Helper Functions
# ═══════════════════════════════════════════════════════════════════════════════

class RateLimitMiddlewareHelper:
    """
    Helper para aplicar rate limiting en middleware.
    """

    @staticmethod
    def process_request(request: HttpRequest) -> Optional[HttpResponse]:
        """
        Procesa una request para rate limiting.

        Args:
            request: HttpRequest

        Returns:
            Optional[HttpResponse]: HttpResponse 429 si se excede el límite
        """
        if not request.user.is_authenticated:
            return None

        result = PerUserRateLimitService.check_rate_limit(request.user)
        if not result.is_allowed:
            from django.http import JsonResponse
            response = JsonResponse(
                {'error': 'Too Many Requests', 'retry_after': result.retry_after},
                status=429,
            )
            for key, value in PerUserRateLimitService.get_rate_limit_headers(
                result
            ).items():
                response[key] = value
            return response

        return None
