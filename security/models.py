"""
Security Models for CFBC Django Project.

Implements all data models for:
- Authentication Service (AS): UserSecurityProfile
- Authorization Service (AZ): Role, ObjectPermission, RowLevelSecurityPolicy
- Data Protection Service (DS): EncryptedDataKey
- API Security Service (APIS): APIKey
- Security Testing Service (TS): SecurityReport
- Audit: SecurityAuditLog
"""

import uuid
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.conf import settings


# ═══════════════════════════════════════════════════════════════════════════════
# Modelo 1: UserSecurityProfile (Extensión del modelo User)
# ═══════════════════════════════════════════════════════════════════════════════

class UserSecurityProfile(models.Model):
    """Perfil de seguridad extendido para usuarios."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='security_profile'
    )

    # ── 2FA Configuration ──────────────────────────────────────────────────
    totp_secret = models.CharField(max_length=32, null=True, blank=True)
    backup_codes = models.JSONField(default=list)  # List of hashed backup codes
    two_factor_enabled = models.BooleanField(default=False)
    last_2fa_verification = models.DateTimeField(null=True, blank=True)

    # ── Session Management ─────────────────────────────────────────────────
    max_concurrent_sessions = models.IntegerField(default=3)
    session_timeout_minutes = models.IntegerField(default=15)
    invalidate_sessions_on_logout = models.BooleanField(default=True)

    # ── Account Lockout ────────────────────────────────────────────────────
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    last_failed_login = models.DateTimeField(null=True, blank=True)

    # ── Time-based Access ──────────────────────────────────────────────────
    allowed_access_hours = models.JSONField(default=dict)
    allowed_access_days = models.JSONField(default=list)

    # ── Password Preferences ───────────────────────────────────────────────
    require_password_change = models.BooleanField(default=False)
    password_changed_at = models.DateTimeField(auto_now_add=True)
    security_questions = models.JSONField(default=list)

    class Meta:
        verbose_name = 'Perfil de Seguridad'
        verbose_name_plural = 'Perfiles de Seguridad'

    def __str__(self):
        return f'Perfil de seguridad: {self.user.username}'

    @property
    def is_account_locked(self):
        """Verifica si la cuenta está bloqueada actualmente."""
        if self.account_locked_until and timezone.now() < self.account_locked_until:
            return True
        # Auto-unlock if lock period has expired
        if self.account_locked_until and timezone.now() >= self.account_locked_until:
            self.account_locked_until = None
            self.failed_login_attempts = 0
            self.save(update_fields=['account_locked_until', 'failed_login_attempts'])
        return False

    def record_failed_login(self):
        """Registra un intento de login fallido."""
        now = timezone.now()
        # Reset counter if 15 minutes have passed since last failed attempt
        if self.last_failed_login and (now - self.last_failed_login) > timedelta(minutes=15):
            self.failed_login_attempts = 0

        self.failed_login_attempts += 1
        self.last_failed_login = now

        # Lock account if exceeded max attempts
        if self.failed_login_attempts >= 5:
            self.account_locked_until = now + timedelta(minutes=30)

        self.save(update_fields=[
            'failed_login_attempts', 'last_failed_login', 'account_locked_until'
        ])

    def record_successful_login(self):
        """Resetea el contador de intentos fallidos tras un login exitoso."""
        self.failed_login_attempts = 0
        self.last_failed_login = None
        self.save(update_fields=['failed_login_attempts', 'last_failed_login'])


# ═══════════════════════════════════════════════════════════════════════════════
# Modelo 2: SecurityAuditLog
# ═══════════════════════════════════════════════════════════════════════════════

class SecurityAuditLog(models.Model):
    """Registro de auditoría de eventos de seguridad."""

    class EventTypes(models.TextChoices):
        AUTH = 'auth', 'Autenticación'
        AUTHORIZATION = 'authorization', 'Autorización'
        DATA_ACCESS = 'data_access', 'Acceso a Datos'
        FILE_OPERATION = 'file_operation', 'Operación de Archivos'
        API_REQUEST = 'api_request', 'Solicitud API'
        SECURITY_TEST = 'security_test', 'Prueba de Seguridad'
        CONFIGURATION = 'configuration', 'Configuración'

    class SeverityLevels(models.TextChoices):
        INFO = 'info', 'Información'
        WARNING = 'warning', 'Advertencia'
        ERROR = 'error', 'Error'
        CRITICAL = 'critical', 'Crítico'

    event_id = models.UUIDField(default=uuid.uuid4, unique=True)
    event_type = models.CharField(max_length=50, choices=EventTypes.choices)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    # Event Details
    action = models.CharField(max_length=200)
    resource = models.CharField(max_length=200, null=True, blank=True)
    resource_id = models.CharField(max_length=100, null=True, blank=True)
    details = models.JSONField(default=dict)

    # Security Context
    severity = models.CharField(
        max_length=20, choices=SeverityLevels.choices, default=SeverityLevels.INFO
    )
    success = models.BooleanField(default=True)
    threat_level = models.IntegerField(default=0)  # 0-10 scale

    # Response
    response_action = models.CharField(max_length=100, null=True, blank=True)
    response_details = models.TextField(null=True, blank=True)

    # Metadata
    session_id = models.CharField(max_length=100, null=True, blank=True)
    request_id = models.CharField(max_length=100, null=True, blank=True)
    retention_days = models.IntegerField(default=90)

    class Meta:
        verbose_name = 'Registro de Auditoría de Seguridad'
        verbose_name_plural = 'Registros de Auditoría de Seguridad'
        indexes = [
            models.Index(fields=['timestamp', 'event_type']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.get_event_type_display()} | {self.action} | {self.timestamp}'


# ═══════════════════════════════════════════════════════════════════════════════
# Modelo 3: RowLevelSecurityPolicy
# ═══════════════════════════════════════════════════════════════════════════════

class RowLevelSecurityPolicy(models.Model):
    """Políticas de seguridad a nivel de fila para PostgreSQL."""

    class PolicyTypes(models.TextChoices):
        SELECT = 'select', 'SELECT'
        INSERT = 'insert', 'INSERT'
        UPDATE = 'update', 'UPDATE'
        DELETE = 'delete', 'DELETE'
        ALL = 'all', 'ALL'

    table_name = models.CharField(max_length=100)
    policy_name = models.CharField(max_length=100)
    policy_type = models.CharField(max_length=20, choices=PolicyTypes.choices)

    # SQL expressions
    using_expression = models.TextField(help_text='SQL expression for USING clause')
    with_check_expression = models.TextField(
        null=True, blank=True, help_text='SQL expression for WITH CHECK clause'
    )

    # Roles
    roles = models.JSONField(default=list, help_text='List of roles this policy applies to')

    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='created_policies'
    )

    # Versioning
    version = models.IntegerField(default=1)
    previous_version = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        verbose_name = 'Política de Seguridad a Nivel de Fila'
        verbose_name_plural = 'Políticas de Seguridad a Nivel de Fila'
        unique_together = ['table_name', 'policy_name']
        indexes = [
            models.Index(fields=['table_name', 'is_active']),
        ]

    def __str__(self):
        return f'{self.policy_name} ON {self.table_name} ({self.get_policy_type_display()})'


# ═══════════════════════════════════════════════════════════════════════════════
# Modelo 4: EncryptedDataKey
# ═══════════════════════════════════════════════════════════════════════════════

class EncryptedDataKey(models.Model):
    """Claves de encriptación para diferentes tipos de datos."""

    class KeyTypes(models.TextChoices):
        PASSWORD = 'password', 'Contraseñas'
        TOKEN = 'token', 'Tokens'
        PII = 'pii', 'Información Personal'
        FINANCIAL = 'financial', 'Datos Financieros'
        HEALTH = 'health', 'Datos de Salud'
        DEFAULT = 'default', 'Por Defecto'

    class Algorithms(models.TextChoices):
        AES_GCM = 'AES-256-GCM', 'AES 256-bit GCM'
        CHACHA20 = 'ChaCha20-Poly1305', 'ChaCha20-Poly1305'

    key_id = models.UUIDField(default=uuid.uuid4, unique=True)
    key_type = models.CharField(max_length=20, choices=KeyTypes.choices)
    algorithm = models.CharField(
        max_length=20, choices=Algorithms.choices, default=Algorithms.AES_GCM
    )

    # Key Material (encrypted at rest with master key)
    encrypted_key = models.BinaryField()
    key_version = models.IntegerField(default=1)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    rotation_days = models.IntegerField(default=90)
    last_rotated = models.DateTimeField(auto_now_add=True)

    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)

    # Audit
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    audit_log = models.JSONField(default=list)

    class Meta:
        verbose_name = 'Clave de Encriptación'
        verbose_name_plural = 'Claves de Encriptación'
        indexes = [
            models.Index(fields=['key_type', 'is_active']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f'{self.get_key_type_display()} - {self.get_algorithm_display()} v{self.key_version}'

    def needs_rotation(self):
        """Verifica si la clave necesita rotación (cada 90 días)."""
        if not self.last_rotated:
            return True
        return (timezone.now() - self.last_rotated).days >= self.rotation_days


# ═══════════════════════════════════════════════════════════════════════════════
# Modelo 5: Role (RBAC)
# ═══════════════════════════════════════════════════════════════════════════════

class Role(models.Model):
    """Modelo para RBAC jerárquico."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default='')
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='children'
    )
    permissions = models.ManyToManyField(
        Permission, blank=True, related_name='security_roles'
    )
    scope = models.CharField(max_length=100, null=True, blank=True)
    is_system_role = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Rol de Seguridad'
        verbose_name_plural = 'Roles de Seguridad'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_inherited_permissions(self):
        """Obtiene todos los permisos incluyendo los heredados de padres."""
        permissions = set(self.permissions.all())
        if self.parent:
            permissions.update(self.parent.get_inherited_permissions())
        return permissions


class UserRoleAssignment(models.Model):
    """Asignación de roles a usuarios."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='role_assignments'
    )
    role = models.ForeignKey(
        Role, on_delete=models.CASCADE, related_name='user_assignments'
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_roles'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Asignación de Rol'
        verbose_name_plural = 'Asignaciones de Roles'
        unique_together = ['user', 'role']
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f'{self.user.username} → {self.role.name}'


# ═══════════════════════════════════════════════════════════════════════════════
# Modelo 6: ObjectPermission
# ═══════════════════════════════════════════════════════════════════════════════

class ObjectPermission(models.Model):
    """Permisos a nivel de objeto usando django-guardian."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='object_permissions'
    )
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='granted_permissions'
    )

    class Meta:
        verbose_name = 'Permiso por Objeto'
        verbose_name_plural = 'Permisos por Objeto'
        unique_together = ['user', 'permission', 'content_type', 'object_id']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f'{self.user.username} → {self.permission.codename} on {self.content_type.model}#{self.object_id}'


class TimeBasedAccessPolicy(models.Model):
    """Políticas de acceso basadas en tiempo."""

    class Days(models.TextChoices):
        MONDAY = 'Monday', 'Lunes'
        TUESDAY = 'Tuesday', 'Martes'
        WEDNESDAY = 'Wednesday', 'Miércoles'
        THURSDAY = 'Thursday', 'Jueves'
        FRIDAY = 'Friday', 'Viernes'
        SATURDAY = 'Saturday', 'Sábado'
        SUNDAY = 'Sunday', 'Domingo'

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default='')
    start_hour = models.IntegerField(default=8, help_text='Hour (0-23)')
    end_hour = models.IntegerField(default=18, help_text='Hour (0-23)')
    allowed_days = models.JSONField(
        default=list, help_text='List of allowed days (Monday-Sunday)'
    )
    timezone = models.CharField(max_length=50, default='UTC', help_text='Timezone name')
    is_active = models.BooleanField(default=True)
    roles = models.ManyToManyField(Role, blank=True, related_name='time_policies')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Política de Acceso por Tiempo'
        verbose_name_plural = 'Políticas de Acceso por Tiempo'

    def __str__(self):
        return f'{self.name} ({self.start_hour}:00-{self.end_hour}:00)'


class AuthorizationAuditLog(models.Model):
    """Registro de auditoría de decisiones de autorización."""

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=100, null=True, blank=True)
    action = models.CharField(max_length=50, help_text='e.g., view, create, edit, delete')
    outcome = models.CharField(
        max_length=10, choices=[('granted', 'Granted'), ('denied', 'Denied')]
    )
    reason = models.TextField(blank=True, default='')
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = 'Auditoría de Autorización'
        verbose_name_plural = 'Auditorías de Autorización'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['resource_type', 'action']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.user} → {self.action} {self.resource_type} ({self.outcome})'


# ═══════════════════════════════════════════════════════════════════════════════
# Modelo 7: APIKey
# ═══════════════════════════════════════════════════════════════════════════════

class APIKey(models.Model):
    """Gestión de API keys para desarrolladores."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='api_keys'
    )
    key = models.CharField(max_length=64, unique=True)
    key_prefix = models.CharField(max_length=8, help_text='First 8 chars for identification')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    daily_limit = models.PositiveIntegerField(default=10000)
    daily_used = models.PositiveIntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    last_reset_date = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['key']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f'{self.name} ({self.key_prefix}...) - {self.user.username}'

    def is_expired(self):
        """Verifica si la API key ha expirado."""
        return timezone.now() > self.expires_at

    def is_daily_limit_exceeded(self):
        """Verifica si se ha excedido el límite diario."""
        from datetime import date
        if self.last_reset_date != date.today():
            self.daily_used = 0
            self.last_reset_date = date.today()
            self.save(update_fields=['daily_used', 'last_reset_date'])
        return self.daily_used >= self.daily_limit

    def increment_usage(self):
        """Incrementa el contador de uso diario."""
        from datetime import date
        if self.last_reset_date != date.today():
            self.daily_used = 0
            self.last_reset_date = date.today()
        self.daily_used += 1
        self.last_used = timezone.now()
        self.save(update_fields=['daily_used', 'last_used', 'last_reset_date'])


class JWTSession(models.Model):
    """Seguimiento de sesiones JWT para rotación."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='jwt_sessions'
    )
    jti = models.CharField(max_length=255, unique=True, help_text='JWT ID')
    access_token_created = models.DateTimeField()
    access_token_expires = models.DateTimeField()
    refresh_token = models.TextField()
    refresh_token_created = models.DateTimeField()
    refresh_token_expires = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    rotated_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Sesión JWT'
        verbose_name_plural = 'Sesiones JWT'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['jti']),
        ]

    def __str__(self):
        return f'JWT Session {self.jti[:8]}... - {self.user.username}'

    def needs_refresh(self):
        """Verifica si el token necesita refresco (<15 min antes de expirar)."""
        remaining = self.access_token_expires - timezone.now()
        return timedelta(minutes=0) <= remaining <= timedelta(minutes=15)


# ═══════════════════════════════════════════════════════════════════════════════
# Modelo 8: WAF Rule
# ═══════════════════════════════════════════════════════════════════════════════

class WAFRule(models.Model):
    """Reglas WAF para bloquear patrones de ataque."""

    class Categories(models.TextChoices):
        SQL_INJECTION = 'sql_injection', 'SQL Injection'
        XSS = 'xss', 'Cross-Site Scripting'
        PATH_TRAVERSAL = 'path_traversal', 'Path Traversal'
        COMMAND_INJECTION = 'command_injection', 'Command Injection'
        CSRF = 'csrf', 'CSRF'
        CUSTOM = 'custom', 'Personalizada'

    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=30, choices=Categories.choices)
    pattern = models.TextField(help_text='Regex pattern to match')
    description = models.TextField(blank=True, default='')
    severity = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Baja'),
            ('medium', 'Media'),
            ('high', 'Alta'),
            ('critical', 'Crítica'),
        ],
        default='high'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    hit_count = models.PositiveIntegerField(default=0)
    last_hit = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Regla WAF'
        verbose_name_plural = 'Reglas WAF'
        indexes = [
            models.Index(fields=['category', 'is_active']),
        ]

    def __str__(self):
        return f'{self.name} ({self.get_category_display()})'


# ═══════════════════════════════════════════════════════════════════════════════
# Modelo 9: SecurityReport
# ═══════════════════════════════════════════════════════════════════════════════

class SecurityReport(models.Model):
    """Reportes de seguridad generados por el Security Testing Service."""

    class ScanTypes(models.TextChoices):
        STATIC = 'static', 'Análisis Estático'
        DEPENDENCY = 'dependency', 'Escaneo de Dependencias'
        OWASP = 'owasp', 'Cumplimiento OWASP'
        PENETRATION = 'pentest', 'Prueba de Penetración'
        COMPLIANCE = 'compliance', 'Cumplimiento Normativo'

    report_id = models.UUIDField(default=uuid.uuid4, unique=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    scan_type = models.CharField(max_length=20, choices=ScanTypes.choices)
    findings = models.JSONField(default=list)
    severity_counts = models.JSONField(default=dict)
    recommendations = models.TextField(blank=True, default='')
    false_positives = models.JSONField(default=list)
    resolved = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    notes = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Reporte de Seguridad'
        verbose_name_plural = 'Reportes de Seguridad'
        indexes = [
            models.Index(fields=['scan_type', 'generated_at']),
        ]
        ordering = ['-generated_at']

    def __str__(self):
        return f'{self.get_scan_type_display()} - {self.generated_at.strftime("%Y-%m-%d %H:%M")}'


class ComplianceCheck(models.Model):
    """Verificaciones de cumplimiento normativo."""

    class Regulations(models.TextChoices):
        GDPR = 'gdpr', 'GDPR'
        HIPAA = 'hipaa', 'HIPAA'
        OWASP = 'owasp', 'OWASP Top 10'
        CUSTOM = 'custom', 'Personalizado'

    regulation = models.CharField(max_length=20, choices=Regulations.choices)
    check_name = models.CharField(max_length=200)
    passed = models.BooleanField()
    details = models.JSONField(default=dict)
    checked_at = models.DateTimeField(auto_now_add=True)
    report = models.ForeignKey(
        SecurityReport, on_delete=models.CASCADE,
        related_name='compliance_checks', null=True, blank=True
    )
    remediation = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Verificación de Cumplimiento'
        verbose_name_plural = 'Verificaciones de Cumplimiento'
        indexes = [
            models.Index(fields=['regulation', 'passed']),
        ]
        ordering = ['-checked_at']

    def __str__(self):
        return f'{self.get_regulation_display()} - {self.check_name}: {"✓" if self.passed else "✗"}'
