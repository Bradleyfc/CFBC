"""
Authentication Service (AS) implementation.

Implements:
- TOTP 2FA (RFC 6238)
- Session management (concurrent sessions, inactivity timeout)
- Account lockout
- Backup codes generation
- Authentication event logging
"""

import base64
import hashlib
import hmac
import struct
import time
import secrets
import string
from datetime import timedelta
from typing import List, Optional, Tuple

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Count

from security.models import (
    UserSecurityProfile, SecurityAuditLog,
)


class TOTPService:
    """
    TOTP (Time-based One-Time Password) service según RFC 6238.

    Genera y verifica códigos TOTP de 6 dígitos con expiración de 30 segundos.
    """

    # Configuración por defecto
    CODE_LENGTH = 6
    TIME_STEP = 30  # seconds
    BACKUP_CODE_COUNT = 10
    BACKUP_CODE_LENGTH = 8

    @staticmethod
    def generate_secret() -> str:
        """
        Genera un secreto TOTP en formato Base32.

        Returns:
            str: Secreto codificado en Base32 (16 caracteres = 80 bits)
        """
        random_bytes = secrets.token_bytes(10)  # 80 bits
        return base64.b32encode(random_bytes).decode('utf-8')

    @staticmethod
    def _get_hotp(secret: bytes, counter: int, digits: int = 6) -> str:
        """
        Genera un código HOTP (RFC 4226) usando HMAC-SHA1.

        Args:
            secret: Secreto en bytes
            counter: Contador de eventos
            digits: Número de dígitos (por defecto 6)

        Returns:
            str: Código HOTP de 'digits' dígitos
        """
        counter_bytes = struct.pack('>Q', counter)
        hmac_hash = hmac.new(secret, counter_bytes, hashlib.sha1).digest()

        # Dynamic truncation (RFC 4226 Section 5.3)
        offset = hmac_hash[-1] & 0x0F
        truncated = struct.unpack('>I', hmac_hash[offset:offset + 4])[0] & 0x7FFFFFFF
        return str(truncated % (10 ** digits)).zfill(digits)

    @classmethod
    def generate_code(cls, secret: str, timestamp: Optional[int] = None) -> str:
        """
        Genera un código TOTP para el timestamp dado.

        Args:
            secret: Secreto en Base32
            timestamp: Timestamp Unix (opcional, usa time.time() por defecto)

        Returns:
            str: Código TOTP de 6 dígitos
        """
        if timestamp is None:
            timestamp = int(time.time())
        counter = timestamp // cls.TIME_STEP
        secret_bytes = base64.b32decode(secret)
        return cls._get_hotp(secret_bytes, counter)

    @classmethod
    def verify_code(cls, secret: str, code: str, window: int = 1) -> bool:
        """
        Verifica un código TOTP dentro de una ventana de tiempo.

        Args:
            secret: Secreto en Base32
            code: Código a verificar (6 dígitos)
            window: Ventana de tolerancia (por defecto 1 = ±30 segundos)

        Returns:
            bool: True si el código es válido
        """
        if not secret or not code:
            return False

        current_timestamp = int(time.time())

        # Verificar dentro de la ventana: [-window, +window] steps
        for i in range(-window, window + 1):
            expected = cls.generate_code(secret, current_timestamp + (i * cls.TIME_STEP))
            if hmac.compare_digest(expected, code):
                return True

        return False

    @classmethod
    def generate_backup_codes(cls) -> List[str]:
        """
        Genera códigos de respaldo para recuperación de 2FA.

        Returns:
            List[str]: Lista de 10 códigos alfanuméricos de 8 caracteres
        """
        codes = set()
        while len(codes) < cls.BACKUP_CODE_COUNT:
            code = ''.join(secrets.choice(
                string.ascii_uppercase + string.digits
            ) for _ in range(cls.BACKUP_CODE_LENGTH))
            codes.add(code)
        return list(codes)

    @classmethod
    def hash_backup_codes(cls, codes: List[str]) -> List[str]:
        """
        Hashea los códigos de respaldo usando SHA-256.

        Args:
            codes: Lista de códigos en texto plano

        Returns:
            List[str]: Lista de códigos hasheados
        """
        return [
            hashlib.sha256(code.encode()).hexdigest()
            for code in codes
        ]

    @classmethod
    def verify_backup_code(cls, hashed_codes: List[str], code: str) -> bool:
        """
        Verifica un código de respaldo contra los hashes almacenados.

        Args:
            hashed_codes: Lista de códigos hasheados
            code: Código a verificar

        Returns:
            bool: True si el código es válido
        """
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        return code_hash in hashed_codes

    @classmethod
    def get_totp_uri(cls, secret: str, username: str, issuer: str = 'CFBC') -> str:
        """
        Genera la URI para el QR code (otpauth://).

        Args:
            secret: Secreto en Base32
            username: Nombre de usuario
            issuer: Emisor (por defecto 'CFBC')

        Returns:
            str: URI compatible con Google Authenticator, Authy, etc.
        """
        return (
            f'otpauth://totp/{issuer}:{username}?secret={secret}'
            f'&issuer={issuer}&algorithm=SHA1&digits={cls.CODE_LENGTH}&period={cls.TIME_STEP}'
        )


class SessionSecurityService:
    """
    Servicio de gestión de sesiones de seguridad.

    Controla sesiones concurrentes, timeouts por inactividad,
    e invalidación de sesiones.
    """

    @staticmethod
    def get_active_session_count(user: User) -> int:
        """
        Obtiene el número de sesiones activas para un usuario.

        Args:
            user: Usuario

        Returns:
            int: Número de sesiones activas
        """
        from django.contrib.sessions.models import Session
        sessions = Session.objects.filter(
            expire_date__gte=timezone.now()
        )
        count = 0
        for session in sessions:
            data = session.get_decoded()
            if str(user.id) == str(data.get('_auth_user_id')):
                count += 1
        return count

    @staticmethod
    def check_concurrent_sessions(user: User) -> bool:
        """
        Verifica si el usuario excede el límite de sesiones concurrentes.
        Si excede 3 sesiones, registra un evento de seguridad.

        Args:
            user: Usuario

        Returns:
            bool: True si excede el límite
        """
        profile, _ = UserSecurityProfile.objects.get_or_create(user=user)
        max_sessions = profile.max_concurrent_sessions
        active = SessionSecurityService.get_active_session_count(user)

        if active > max_sessions and active >= 3:
            SecurityAuditLog.objects.create(
                event_type=SecurityAuditLog.EventTypes.AUTH,
                user=user,
                action='concurrent_sessions_exceeded',
                resource='session',
                details={
                    'active_sessions': active,
                    'max_sessions': max_sessions,
                },
                severity=SecurityAuditLog.SeverityLevels.WARNING,
                threat_level=3,
            )
            return True
        return False

    @staticmethod
    def invalidate_all_sessions(user: User) -> int:
        """
        Invalida todas las sesiones de un usuario.

        Args:
            user: Usuario

        Returns:
            int: Número de sesiones invalidadas
        """
        from django.contrib.sessions.models import Session
        count = 0
        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        for session in sessions:
            data = session.get_decoded()
            if str(user.id) == str(data.get('_auth_user_id')):
                session.expire_date = timezone.now() - timedelta(seconds=1)
                session.save()
                count += 1

        # Registrar evento de seguridad
        if count > 0:
            SecurityAuditLog.objects.create(
                event_type=SecurityAuditLog.EventTypes.AUTH,
                user=user,
                action='sessions_invalidated',
                resource='session',
                details={'invalidated_count': count},
                success=True,
            )

        return count

    @staticmethod
    def invalidate_inactive_sessions() -> int:
        """
        Invalida todas las sesiones inactivas por más de 15 minutos.

        Returns:
            int: Número de sesiones invalidadas
        """
        from django.contrib.sessions.models import Session
        cutoff = timezone.now() - timedelta(minutes=15)
        count = 0

        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        for session in sessions:
            data = session.get_decoded()
            last_activity = data.get('last_activity')
            if last_activity:
                last_activity_dt = timezone.datetime.fromisoformat(last_activity)
                if last_activity_dt < cutoff:
                    session.expire_date = timezone.now()
                    session.save()
                    count += 1

        return count

    @staticmethod
    def update_last_activity(request):
        """
        Actualiza la marca de última actividad en la sesión.

        Args:
            request: HttpRequest
        """
        if request.user.is_authenticated:
            request.session['last_activity'] = timezone.now().isoformat()


class AccountLockoutService:
    """
    Servicio de bloqueo de cuentas.

    Implementa:
    - Máximo 5 intentos fallidos en 15 minutos por IP
    - Bloqueo automático por 30 minutos
    - Desbloqueo automático después de 30 minutos
    """

    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30
    ATTEMPT_WINDOW_MINUTES = 15
    IP_LOCKOUT_PREFIX = 'ip_lockout_'
    IP_ATTEMPT_PREFIX = 'ip_attempt_'

    @classmethod
    def record_failed_attempt(cls, user: User, ip_address: str = None):
        """
        Registra un intento fallido de inicio de sesión.

        Args:
            user: Usuario (opcional, puede ser None)
            ip_address: Dirección IP del intento
        """
        # Registrar en perfil de usuario
        if user:
            profile, _ = UserSecurityProfile.objects.get_or_create(user=user)
            profile.record_failed_login()

        # Tracking por IP usando cache
        if ip_address:
            ip_key = f'{cls.IP_ATTEMPT_PREFIX}{ip_address}'
            attempts = cache.get(ip_key, 0)
            attempts += 1
            cache.set(ip_key, attempts, timeout=cls.ATTEMPT_WINDOW_MINUTES * 60)

            if attempts >= cls.MAX_FAILED_ATTEMPTS:
                lock_key = f'{cls.IP_LOCKOUT_PREFIX}{ip_address}'
                cache.set(
                    lock_key, True,
                    timeout=cls.LOCKOUT_DURATION_MINUTES * 60
                )
                SecurityAuditLog.objects.create(
                    event_type=SecurityAuditLog.EventTypes.AUTH,
                    user=user,
                    action='ip_locked',
                    resource='authentication',
                    details={
                        'ip_address': ip_address,
                        'failed_attempts': attempts,
                        'lockout_duration': cls.LOCKOUT_DURATION_MINUTES,
                    },
                    severity=SecurityAuditLog.SeverityLevels.WARNING,
                    threat_level=5,
                )

        # Revisar si se necesita bloquear cuenta
        if user:
            profile, _ = UserSecurityProfile.objects.get_or_create(user=user)
            if profile.failed_login_attempts >= cls.MAX_FAILED_ATTEMPTS:
                SecurityAuditLog.objects.create(
                    event_type=SecurityAuditLog.EventTypes.AUTH,
                    user=user,
                    action='account_locked',
                    resource='authentication',
                    details={
                        'failed_attempts': profile.failed_login_attempts,
                        'lockout_duration': cls.LOCKOUT_DURATION_MINUTES,
                    },
                    severity=SecurityAuditLog.SeverityLevels.WARNING,
                    threat_level=5,
                )

    @classmethod
    def check_ip_locked(cls, ip_address: str) -> bool:
        """
        Verifica si una IP está bloqueada.

        Args:
            ip_address: Dirección IP

        Returns:
            bool: True si la IP está bloqueada
        """
        lock_key = f'{cls.IP_LOCKOUT_PREFIX}{ip_address}'
        return bool(cache.get(lock_key))

    @classmethod
    def check_user_locked(cls, user: User) -> bool:
        """
        Verifica si un usuario está bloqueado.

        Args:
            user: Usuario

        Returns:
            bool: True si el usuario está bloqueado
        """
        profile, _ = UserSecurityProfile.objects.get_or_create(user=user)
        return profile.is_account_locked

    @classmethod
    def record_successful_login(cls, user: User, ip_address: str = None):
        """
        Registra un inicio de sesión exitoso y resetea contadores.

        Args:
            user: Usuario
            ip_address: Dirección IP
        """
        # Resetear perfil de usuario
        profile, _ = UserSecurityProfile.objects.get_or_create(user=user)
        profile.record_successful_login()

        # Limpiar cache de IP
        if ip_address:
            ip_key = f'{cls.IP_ATTEMPT_PREFIX}{ip_address}'
            cache.delete(ip_key)
            lock_key = f'{cls.IP_LOCKOUT_PREFIX}{ip_address}'
            cache.delete(lock_key)

        SecurityAuditLog.objects.create(
            event_type=SecurityAuditLog.EventTypes.AUTH,
            user=user,
            action='login_success',
            resource='authentication',
            details={'ip_address': ip_address} if ip_address else {},
            success=True,
        )

    @classmethod
    def log_auth_event(
        cls, user: User, event_type: str, success: bool,
        metadata: dict = None
    ):
        """
        Registra un evento de autenticación para auditoría.

        Args:
            user: Usuario
            event_type: Tipo de evento
            success: Si fue exitoso
            metadata: Metadatos adicionales
        """
        SecurityAuditLog.objects.create(
            event_type=SecurityAuditLog.EventTypes.AUTH,
            user=user,
            action=event_type,
            resource='authentication',
            details=metadata or {},
            success=success,
            severity=(
                SecurityAuditLog.SeverityLevels.INFO if success
                else SecurityAuditLog.SeverityLevels.WARNING
            ),
        )
