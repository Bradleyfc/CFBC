"""
Data Protection Service (DS) implementation.

Implements:
- AES-256-GCM encryption with separate keys per data type
- Input sanitization (SQL injection, XSS, command injection)
- File validation (magic numbers, signatures)
- Sensitive data masking in logs
- CORS restriction
- Data protection audit logging
"""

import base64
import hashlib
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from io import BytesIO

import magic
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.http import HttpRequest

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from security.models import EncryptedDataKey, SecurityAuditLog

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Encryption Service
# ═══════════════════════════════════════════════════════════════════════════════

class EncryptionService:
    """
    Servicio de encriptación AES-256-GCM con claves separadas por tipo de dato.
    """

    # Master key for encrypting data keys (derived from Django SECRET_KEY)
    _master_key = None

    @classmethod
    def _get_master_key(cls) -> bytes:
        """
        Obtiene o deriva la clave maestra del SECRET_KEY de Django.

        Returns:
            bytes: Clave maestra de 32 bytes
        """
        if cls._master_key is None:
            secret_key = settings.SECRET_KEY.encode()
            hkdf = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=None,
                info=b'cfbc-master-key',
            )
            cls._master_key = hkdf.derive(secret_key)
        return cls._master_key

    @classmethod
    def _get_or_create_data_key(cls, key_type: str) -> Tuple[EncryptedDataKey, bytes]:
        """
        Obtiene o crea una clave de datos para un tipo específico.

        Args:
            key_type: Tipo de dato ('password', 'token', 'pii', etc.)

        Returns:
            Tuple[EncryptedDataKey, bytes]: La clave del modelo y el material de clave
        """
        # Buscar clave activa del tipo solicitado
        data_key = EncryptedDataKey.objects.filter(
            key_type=key_type,
            is_active=True,
        ).order_by('-key_version').first()

        if data_key:
            # Descifrar el material de clave
            master_key = cls._get_master_key()
            aesgcm = AESGCM(master_key)
            nonce = data_key.encrypted_key[:12]
            ciphertext = data_key.encrypted_key[12:]
            key_material = aesgcm.decrypt(nonce, ciphertext, None)
            return data_key, key_material

        # Crear nueva clave
        return cls._rotate_key(key_type)

    @classmethod
    def _rotate_key(cls, key_type: str) -> Tuple[EncryptedDataKey, bytes]:
        """
        Rota la clave para un tipo de dato, creando una nueva.

        Args:
            key_type: Tipo de dato

        Returns:
            Tuple[EncryptedDataKey, bytes]: Nueva clave y material
        """
        # Generar nuevo material de clave
        key_material = AESGCM.generate_key(bit_length=256)

        # Encriptar con clave maestra
        master_key = cls._get_master_key()
        aesgcm = AESGCM(master_key)
        nonce = os.urandom(12)
        encrypted_key = nonce + aesgcm.encrypt(nonce, key_material, None)

        # Desactivar claves anteriores del mismo tipo
        EncryptedDataKey.objects.filter(
            key_type=key_type, is_active=True
        ).update(is_active=False)

        # Crear nueva entrada
        data_key = EncryptedDataKey.objects.create(
            key_type=key_type,
            key_version=(
                EncryptedDataKey.objects.filter(key_type=key_type).count() + 1
            ),
            encrypted_key=encrypted_key,
            rotation_days=90,
        )

        return data_key, key_material

    @classmethod
    def encrypt(cls, value: Any, key_type: str = 'default') -> str:
        """
        Encripta un valor usando AES-256-GCM.

        Args:
            value: Valor a encriptar
            key_type: Tipo de clave ('password', 'token', 'pii', etc.)

        Returns:
            str: Valor encriptado en formato base64
        """
        if value is None:
            return None

        # Convertir a bytes
        if isinstance(value, str):
            plaintext = value.encode('utf-8')
        elif isinstance(value, (dict, list)):
            plaintext = json.dumps(value, ensure_ascii=False).encode('utf-8')
        else:
            plaintext = str(value).encode('utf-8')

        data_key, key_material = cls._get_or_create_data_key(key_type)

        # Encriptar
        aesgcm = AESGCM(key_material)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        # Formato: key_id|nonce|ciphertext
        result = f"{data_key.key_id}|{base64.b64encode(nonce).decode()}|{base64.b64encode(ciphertext).decode()}"

        # Actualizar contador de uso
        data_key.usage_count += 1
        data_key.last_used = __import__('django').utils.timezone.now()
        data_key.save(update_fields=['usage_count', 'last_used'])

        # Registrar evento de encriptación
        SecurityAuditLog.objects.create(
            event_type=SecurityAuditLog.EventTypes.DATA_ACCESS,
            action='encrypt',
            resource=f'encrypted_data/{key_type}',
            details={'key_type': key_type},
            success=True,
        )

        return result

    @classmethod
    def decrypt(cls, encrypted_value: str, key_type: str = 'default') -> Any:
        """
        Descifra un valor previamente encriptado.

        Args:
            encrypted_value: Valor encriptado en formato key_id|nonce|ciphertext
            key_type: Tipo de clave

        Returns:
            Any: Valor descifrado
        """
        if encrypted_value is None:
            return None

        try:
            # Parsear formato: key_id|nonce|ciphertext
            parts = encrypted_value.split('|')
            if len(parts) != 3:
                logger.error(f'Invalid encrypted value format')
                return None

            key_id = parts[0]
            nonce = base64.b64decode(parts[1])
            ciphertext = base64.b64decode(parts[2])

            # Buscar la clave por key_id
            try:
                data_key = EncryptedDataKey.objects.get(key_id=key_id)
            except EncryptedDataKey.DoesNotExist:
                logger.error(f'Encryption key not found: {key_id}')
                return None

            # Descifrar el material de clave
            master_key = cls._get_master_key()
            aesgcm_master = AESGCM(master_key)
            key_material = aesgcm_master.decrypt(
                data_key.encrypted_key[:12],
                data_key.encrypted_key[12:],
                None
            )

            # Descifrar el valor
            aesgcm = AESGCM(key_material)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)

            # Intentar decodificar como JSON, si no, como string
            try:
                return json.loads(plaintext.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return plaintext.decode('utf-8')

        except Exception as e:
            logger.error(f'Decryption error: {str(e)}')
            return None


# ═══════════════════════════════════════════════════════════════════════════════
# Input Sanitization Service
# ═══════════════════════════════════════════════════════════════════════════════

class InputSanitizationService:
    """
    Servicio de sanitización de entrada contra inyecciones.
    """

    # Patrones de ataque comunes
    SQL_INJECTION_PATTERNS = [
        r"(\'|\"|;|--|/\*|\*/|@@|char|nchar|varchar|nvarchar)",
        r"\b(alter|begin|cast|create|cursor|declare|delete|drop|end|exec|execute|fetch|insert|kill|open|select|sys|sysobjects|syscolumns|table|update)\b",
        r"(\bunion\b.*\bselect\b|\bselect\b.*\bfrom\b|\binsert\b.*\binto\b)",
        r"(xp_cmdshell|sp_executesql|sp_prepare)",
    ]

    XSS_PATTERNS = [
        r'(<script[^>]*>|</script>|<iframe[^>]*>|</iframe>|<object[^>]*>|</object>|<embed[^>]*>|</embed>)',
        r'(javascript:|onload\s*=|onerror\s*=|onclick\s*=|onmouseover\s*=|onfocus\s*=)',
        r"(<[^>]*\s+on\w+\s*=|alert\(|confirm\(|prompt\()",
    ]

    COMMAND_INJECTION_PATTERNS = [
        r'(\||&|;|`|\$\(|\n|\r)',
        r'(&&|\|\||>|<|>>|<<)',
        r'\b(cmd|powershell|bash|sh|python|perl|ruby)\b.*[-/]',
    ]

    PATH_TRAVERSAL_PATTERNS = [
        r'(\.\./|\.\.\\|~/|//|\\\\)',
        r'(\.\.%2f|\.\.%5c|%2e%2e%2f)',
    ]

    SENSITIVE_DATA_PATTERNS = [
        # Passwords
        r'(?i)(password|passwd|pwd|secret)\s*[:=]\s*["\']?([^"\'&\s]+)',
        # Tokens
        r'(?i)(api[_-]?key|api[_-]?secret|access[_-]?token|auth[_-]?token|bearer)\s*[:=]\s*["\']?([^"\'&\s]+)',
        # PII - Email
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
        # PII - Phone
        r'\b(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
    ]

    MASK_PLACEHOLDER = '••••••••'

    @classmethod
    def sanitize_input(cls, value: str) -> str:
        """
        Sanitiza un string de entrada contra inyecciones.

        Args:
            value: Valor a sanitizar

        Returns:
            str: Valor sanitizado
        """
        if not isinstance(value, str):
            return value

        # Remover caracteres de control
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)

        # Sanitizar contra SQL injection
        for pattern in cls.SQL_INJECTION_PATTERNS:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)

        # Sanitizar contra XSS
        for pattern in cls.XSS_PATTERNS:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)

        # Sanitizar contra command injection
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            sanitized = re.sub(pattern, '', sanitized)

        # Sanitizar contra path traversal
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            sanitized = re.sub(pattern, '', sanitized)

        return sanitized

    @classmethod
    def sanitize_dict(cls, data: dict) -> dict:
        """
        Sanitiza recursivamente todos los valores string en un diccionario.

        Args:
            data: Diccionario a sanitizar

        Returns:
            dict: Diccionario sanitizado
        """
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = cls.sanitize_input(value)
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    cls.sanitize_input(item) if isinstance(item, str)
                    else item for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized

    @classmethod
    def contains_attack_pattern(cls, value: str) -> bool:
        """
        Verifica si un valor contiene patrones de ataque.

        Args:
            value: Valor a verificar

        Returns:
            bool: True si contiene patrones de ataque
        """
        if not isinstance(value, str):
            return False

        all_patterns = (
            cls.SQL_INJECTION_PATTERNS +
            cls.XSS_PATTERNS +
            cls.COMMAND_INJECTION_PATTERNS +
            cls.PATH_TRAVERSAL_PATTERNS
        )

        for pattern in all_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True

        return False


# ═══════════════════════════════════════════════════════════════════════════════
# File Validation Service
# ═══════════════════════════════════════════════════════════════════════════════

class FileValidationResult:
    """Resultado de la validación de archivos."""

    def __init__(
        self,
        is_valid: bool = True,
        mime_type: str = '',
        detected_extension: str = '',
        is_malicious: bool = False,
        error_message: str = '',
    ):
        self.is_valid = is_valid
        self.mime_type = mime_type
        self.detected_extension = detected_extension
        self.is_malicious = is_malicious
        self.error_message = error_message


class FileValidationService:
    """
    Servicio de validación de archivos usando magic numbers y firmas.
    """

    # Mapeo de tipos MIME a extensiones
    MAGIC_SIGNATURES = {
        b'\x25\x50\x44\x46': ('application/pdf', 'pdf'),
        b'\xD0\xCF\x11\xE0': ('application/msword', 'doc'),
        b'\x50\x4B\x03\x04': ('application/zip', 'zip'),  # Also docx, xlsx, pptx
        b'\x89\x50\x4E\x47': ('image/png', 'png'),
        b'\xFF\xD8\xFF': ('image/jpeg', 'jpg'),
        b'\x47\x49\x46\x38': ('image/gif', 'gif'),
        b'\x52\x61\x72\x21': ('application/x-rar-compressed', 'rar'),
        b'\x1F\x8B': ('application/gzip', 'gz'),
    }

    # Tipos MIME peligrosos
    DANGEROUS_MIME_TYPES = {
        'application/x-executable',
        'application/x-msdownload',
        'application/x-msdos-program',
        'application/x-dosexec',
        'application/x-sh',
        'application/x-csh',
        'application/x-shellscript',
        'text/x-shellscript',
        'text/x-php',
        'application/x-php',
        'text/x-python',
        'text/javascript',
        'application/javascript',
    }

    # Extensiones peligrosas
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.msi',
        '.scr', '.pif', '.vbs', '.vbe', '.js', '.jse',
        '.wsf', '.wsh', '.ps1', '.psm1', '.psd1',
        '.sh', '.bash', '.zsh', '.ksh',
        '.php', '.php3', '.php4', '.php5', '.phtml',
        '.py', '.pyc', '.pyo',
        '.rb', '.pl', '.pm', '.cgi',
    }

    @classmethod
    def validate_file(cls, uploaded_file: UploadedFile) -> FileValidationResult:
        """
        Valida un archivo subido usando magic numbers y análisis de contenido.

        Args:
            uploaded_file: Archivo subido

        Returns:
            FileValidationResult: Resultado de la validación
        """
        # Leer primeros bytes para magic number
        file_start = uploaded_file.read(4096)
        uploaded_file.seek(0)

        mime_type, detected_ext = cls._detect_by_magic(file_start)

        result = FileValidationResult(
            mime_type=mime_type,
            detected_extension=detected_ext,
        )

        # Verificar tipo MIME peligroso
        if mime_type in cls.DANGEROUS_MIME_TYPES:
            result.is_valid = False
            result.is_malicious = True
            result.error_message = f'Tipo MIME peligroso detectado: {mime_type}'
            return result

        # Verificar extensión peligrosa
        original_name = uploaded_file.name.lower()
        for dangerous_ext in cls.DANGEROUS_EXTENSIONS:
            if original_name.endswith(dangerous_ext):
                result.is_valid = False
                result.is_malicious = True
                result.error_message = f'Extensión peligrosa detectada: {dangerous_ext}'
                return result

        # Verificar inconsistencia entre extensión y contenido
        file_ext = f'.{original_name.split(".")[-1]}' if '.' in original_name else ''
        if detected_ext and file_ext and detected_ext != file_ext:
            # No bloquear, solo registrar
            logger.warning(
                f'File extension mismatch: declared={file_ext}, '
                f'detected={detected_ext}, file={uploaded_file.name}'
            )

        # Verificar tamaño máximo
        max_size = getattr(settings, 'COURSE_DOCUMENTS_MAX_FILE_SIZE', 50 * 1024 * 1024)
        if uploaded_file.size > max_size:
            result.is_valid = False
            result.error_message = (
                f'Archivo demasiado grande: {uploaded_file.size} bytes '
                f'(máximo {max_size} bytes)'
            )
            return result

        # Verificar contenido embebido (scripts ocultos)
        if cls._contains_embedded_scripts(file_start):
            result.is_valid = False
            result.is_malicious = True
            result.error_message = 'Script embebido detectado en el archivo'
            return result

        return result

    @classmethod
    def _detect_by_magic(cls, data: bytes) -> Tuple[str, str]:
        """
        Detecta tipo MIME usando magic numbers.

        Args:
            data: Primeros bytes del archivo

        Returns:
            Tuple[str, str]: (mime_type, extension)
        """
        # Intentar con python-magic
        try:
            mime = magic.from_buffer(data, mime=True)
            if mime:
                ext = magic.from_buffer(data).lower()
                return mime, ext
        except Exception:
            pass

        # Fallback: detectar por magic numbers hardcodeados
        for signature, (mime_type, ext) in cls.MAGIC_SIGNATURES.items():
            if data.startswith(signature):
                return mime_type, ext

        # Intentar por el módulo mimetypes
        import mimetypes
        mime_type, _ = mimetypes.guess_type('file.bin')
        return mime_type or 'application/octet-stream', ''

    @classmethod
    def _contains_embedded_scripts(cls, data: bytes) -> bool:
        """
        Verifica si el contenido contiene scripts embebidos.

        Args:
            data: Datos del archivo

        Returns:
            bool: True si contiene scripts embebidos
        """
        # Buscar patrones de scripts en texto plano
        try:
            text = data.decode('utf-8', errors='ignore').lower()
            script_patterns = [
                '<script', '<?php', '<%', 'eval(',
                'exec(', 'system(', 'passthru(',
                'base64_decode', 'shell_exec',
            ]
            for pattern in script_patterns:
                if pattern in text:
                    return True
        except Exception:
            pass

        return False


# ═══════════════════════════════════════════════════════════════════════════════
# Sensitive Data Masking Service
# ═══════════════════════════════════════════════════════════════════════════════

class DataMaskingService:
    """
    Servicio de enmascaramiento de datos sensibles.
    """

    MASK_PLACEHOLDER = '••••••••'

    # Patrones de datos sensibles con grupos de captura
    SENSITIVE_PATTERNS = [
        # Passwords en texto
        (r'(?i)(password["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])', r'\g<1>' + MASK_PLACEHOLDER + r'\g<3>'),
        # Tokens
        (r'(?i)(token["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])', r'\g<1>' + MASK_PLACEHOLDER + r'\g<3>'),
        # API keys
        (r'(?i)(api[_-]?key["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])', r'\g<1>' + MASK_PLACEHOLDER + r'\g<3>'),
        # Secrets
        (r'(?i)(secret["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])', r'\g<1>' + MASK_PLACEHOLDER + r'\g<3>'),
        # Emails
        (r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', r'\1@***'),
        # Tarjetas de crédito (simples)
        (r'\b(\d{4}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?)\d{4}\b', r'\1' + '••••'),
        # Bearer tokens JWT
        (r'(Bearer\s+)[a-zA-Z0-9\-._~+/]+=*', r'\1' + MASK_PLACEHOLDER),
    ]

    @classmethod
    def mask_sensitive_data(cls, data: str) -> str:
        """
        Enmascara datos sensibles en un string.

        Args:
            data: String que puede contener datos sensibles

        Returns:
            str: String con datos sensibles enmascarados
        """
        if not isinstance(data, str):
            return str(data)

        masked = data
        for pattern, replacement in cls.SENSITIVE_PATTERNS:
            masked = re.sub(pattern, replacement, masked)

        return masked

    @classmethod
    def mask_log_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enmascara datos sensibles en un diccionario (para logging).

        Args:
            data: Diccionario con posibles datos sensibles

        Returns:
            Dict: Diccionario con datos sensibles enmascarados
        """
        SENSITIVE_KEYS = {
            'password', 'passwd', 'pwd', 'secret', 'token',
            'api_key', 'api_secret', 'access_token', 'refresh_token',
            'auth_token', 'authorization', 'credit_card', 'ssn',
            'email', 'phone', 'telephone', 'movil',
        }

        masked = {}
        for key, value in data.items():
            if key.lower() in SENSITIVE_KEYS and isinstance(value, str):
                if len(value) > 4:
                    masked[key] = value[:2] + cls.MASK_PLACEHOLDER + value[-2:]
                else:
                    masked[key] = cls.MASK_PLACEHOLDER
            elif isinstance(value, dict):
                masked[key] = cls.mask_log_data(value)
            elif isinstance(value, str):
                masked[key] = cls.mask_sensitive_data(value)
            else:
                masked[key] = value

        return masked


# ═══════════════════════════════════════════════════════════════════════════════
# CORS Security Service
# ═══════════════════════════════════════════════════════════════════════════════

class CORSSecurityService:
    """
    Servicio de seguridad CORS.

    Restringe orígenes a dominios confiables solamente.
    """

    @staticmethod
    def get_trusted_origins() -> List[str]:
        """
        Obtiene la lista de orígenes confiables.

        Returns:
            List[str]: Lista de orígenes permitidos
        """
        # Obtener del settings o usar valores por defecto
        origins = getattr(settings, 'CORS_TRUSTED_ORIGINS', [])
        if not origins:
            allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
            origins = [
                f'http://{host}' if not host.startswith('http') else host
                for host in allowed_hosts
                if host != 'testserver'
            ]
        return origins

    @staticmethod
    def is_origin_trusted(origin: str) -> bool:
        """
        Verifica si un origen es confiable.

        Args:
            origin: Origen a verificar

        Returns:
            bool: True si el origen está en la lista de confianza
        """
        if not origin:
            return False

        trusted = CORSSecurityService.get_trusted_origins()
        return origin in trusted


# ═══════════════════════════════════════════════════════════════════════════════
# Data Protection Audit Service
# ═══════════════════════════════════════════════════════════════════════════════

class DataProtectionAuditService:
    """
    Servicio de auditoría de protección de datos.
    """

    @staticmethod
    def log_operation(
        operation: str,
        data_type: str,
        success: bool = True,
        details: dict = None,
        user=None,
    ):
        """
        Registra una operación de protección de datos.

        Args:
            operation: Tipo de operación (encrypt, decrypt, sanitize, validate, mask)
            data_type: Tipo de dato
            success: Si fue exitosa
            details: Detalles adicionales
            user: Usuario que realizó la operación
        """
        SecurityAuditLog.objects.create(
            event_type=SecurityAuditLog.EventTypes.DATA_ACCESS,
            user=user,
            action=f'data_{operation}',
            resource=f'data_protection/{data_type}',
            details={
                'operation': operation,
                'data_type': data_type,
                **(details or {}),
            },
            success=success,
        )
