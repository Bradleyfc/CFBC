"""
Signals for security app.

Creates UserSecurityProfile automatically for new users.
Logs authentication events (login/logout).
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.conf import settings


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_security_profile(sender, instance, created, **kwargs):
    """Crea automáticamente un UserSecurityProfile para cada nuevo usuario."""
    if created:
        from .models import UserSecurityProfile
        UserSecurityProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_security_profile(sender, instance, **kwargs):
    """Guarda el UserSecurityProfile cuando se guarda el usuario."""
    try:
        if hasattr(instance, 'security_profile'):
            instance.security_profile.save()
    except Exception:
        pass


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Registra eventos de login exitoso en el log de auditoría."""
    from .models import SecurityAuditLog
    
    ip_address = request.META.get('REMOTE_ADDR', '')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    SecurityAuditLog.objects.create(
        event_type='login',
        action=f'Usuario {user.username} inició sesión',
        user=user,
        ip_address=ip_address,
        success=True,
        severity='info',
        details={
            'username': user.username,
            'ip_address': ip_address,
            'user_agent': user_agent[:200] if user_agent else '',
        }
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Registra eventos de logout en el log de auditoría."""
    from .models import SecurityAuditLog
    
    if user:
        ip_address = request.META.get('REMOTE_ADDR', '') if request else ''
        
        SecurityAuditLog.objects.create(
            event_type='logout',
            action=f'Usuario {user.username} cerró sesión',
            user=user,
            ip_address=ip_address,
            success=True,
            severity='info',
            details={
                'username': user.username,
                'ip_address': ip_address,
            }
        )


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """Registra intentos de login fallidos en el log de auditoría."""
    from .models import SecurityAuditLog
    
    ip_address = request.META.get('REMOTE_ADDR', '') if request else ''
    username = credentials.get('username', 'unknown')
    
    SecurityAuditLog.objects.create(
        event_type='login_failed',
        action=f'Intento de login fallido para usuario {username}',
        user=None,
        ip_address=ip_address,
        success=False,
        severity='warning',
        details={
            'username': username,
            'ip_address': ip_address,
        }
    )
